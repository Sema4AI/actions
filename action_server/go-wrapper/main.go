package main

import (
	"archive/zip"
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"time"

	"github.com/gofrs/flock"
	"golang.org/x/mod/semver"

	_ "embed"
)

//go:embed assets/assets.zip
var ASSETS_ZIP []byte

//go:embed assets/version.txt
var ASSETS_VERSION []byte

//go:embed assets/app_hash
var ASSETS_APP_HASH []byte

// Constants
var debugGoWrapper = os.Getenv("SEMA4AI_GO_WRAPPER_DEBUG") == "1"

// read/write/execute for the owner, read/execute for the group and others
const DEFAULT_PERMISSIONS = 0755

type ColorType struct{}

func (ct *ColorType) Bold(str string) string {
	return fmt.Sprintf("\033[1m%s\033[0m", str)
}
func (ct *ColorType) Yellow(str string) string {
	return fmt.Sprintf("\033[33m%s\033[0m", str)
}
func (ct *ColorType) Green(str string) string {
	return fmt.Sprintf("\033[32m%s\033[0m", str)
}

func getLatestVersion(versionLatestUrl string) (string, error) {
	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "Getting latest version from %s\n", versionLatestUrl)
	}
	// Get the data from the URL
	versionResponse, err := http.Get(versionLatestUrl)
	if err != nil {
		return "", err
	}
	defer versionResponse.Body.Close()

	// Read the body content
	versionInBytes, err := io.ReadAll(versionResponse.Body)
	if err != nil {
		return "", err
	}
	// Convert the byte slice to string
	versionAsString := string(versionInBytes)
	return strings.TrimSpace(versionAsString), nil
}

func checkAvailableUpdate(version string, config RunConfig) {
	// Get the latest version
	latestVersion, err := getLatestVersion(config.VersionLatestURL)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Verifying latest version failed:%s\n", err)
		return
	}
	// Compare the given version with the latest one
	compareResult := semver.Compare(strings.TrimSpace("v"+version), strings.TrimSpace("v"+latestVersion))

	// If the current version is a previous version than the latest print the update suggestions
	if compareResult == -1 {
		colorT := &ColorType{}
		fmt.Fprintf(os.Stderr, "\n ⏫ A new version of %s is now available: %s → %s \n", config.ExecutableName, colorT.Yellow(version), colorT.Green(latestVersion))
		if runtime.GOOS == "darwin" && config.ShowBrewMessage != "" {
			fmt.Fprintf(os.Stderr, "    To update, download from: %s \n", colorT.Bold(config.DownloadLatestURL))
			fmt.Fprintf(os.Stderr, "    Or run: %s \n\n", colorT.Bold(config.ShowBrewMessage))
		} else {
			fmt.Fprintf(os.Stderr, "    To update, download from: %s \n\n", colorT.Bold(config.DownloadLatestURL))
		}
	}
}

func expandAssets(dest string) error {
	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "Expanding assets to: %s (pid: %d)\n", dest, os.Getpid())
	}

	// Create a reader for the zip content
	zipReader, err := zip.NewReader(bytes.NewReader(ASSETS_ZIP), int64(len(ASSETS_ZIP)))
	if err != nil {
		return err
	}

	// Extract each file from the zip
	for _, file := range zipReader.File {
		if strings.Contains(file.Name, "..") {
			// This is a security check to avoid directory traversal attacks (CodeQL: go/zipslip)
			panic(fmt.Sprintf("Error: found '..' in file name %s (in embedded zip assets)\n", file.Name))
		}
		destPath := filepath.Join(dest, file.Name)

		if file.FileInfo().IsDir() {
			err := os.MkdirAll(destPath, DEFAULT_PERMISSIONS)
			if err != nil {
				return err
			}
			continue
		}

		// Create destination directory if it doesn't exist
		err := os.MkdirAll(filepath.Dir(destPath), DEFAULT_PERMISSIONS)
		if err != nil {
			return err
		}

		// Open the file from the zip
		rc, err := file.Open()
		if err != nil {
			return err
		}

		// Create the destination file
		destFile, err := os.Create(destPath)
		if err != nil {
			rc.Close()
			return err
		}

		// Copy the contents
		_, err = io.Copy(destFile, rc)
		rc.Close()
		destFile.Close()
		if err != nil {
			return err
		}

		// Set the file permissions
		err = os.Chmod(destPath, DEFAULT_PERMISSIONS)
		if err != nil {
			return err
		}
	}

	return nil
}

func isDirEmpty(path string) bool {
	entries, err := os.ReadDir(path)
	if err != nil {
		return false
	}
	return len(entries) == 0
}

type ZipHashMatches int

const (
	NoHashFile ZipHashMatches = iota
	EmptyHashFile
	HashDoesNotMatch
	HashMatches
)

func zipHashMatches(zipHash, targetDirectory string) ZipHashMatches {
	currentZipHash, err := os.ReadFile(filepath.Join(targetDirectory, "app_hash"))
	if err != nil {
		return NoHashFile
	}
	if len(currentZipHash) == 0 {
		return EmptyHashFile
	}
	matches := zipHash == strings.TrimSpace(string(currentZipHash))
	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "App hash matches: %t\n", matches)
	}
	if matches {
		return HashMatches
	}
	return HashDoesNotMatch
}

const LOCK_TIMEOUT = 120 * time.Second

func obtainLock(lockFile string) (*flock.Flock, error) {
	fileLock := flock.New(lockFile)

	ctx, cancel := context.WithTimeout(context.Background(), LOCK_TIMEOUT)
	defer cancel()

	locked, err := fileLock.TryLockContext(ctx, 250*time.Millisecond) // try to lock every 1/4 second
	if err != nil {
		// unable to lock the cache, something is wrong, refuse to use it.
		return nil, fmt.Errorf("unable to read lock file %s: %v", lockFile, err)
	}

	if locked {
		if debugGoWrapper {
			fmt.Fprintf(os.Stderr, "> Locked the file %s (pid: %d)\n", fileLock.Path(), os.Getpid())
		}
	}

	return fileLock, nil
}

func makeAssetExpansion(targetDirectory string, zipHash string) error {
	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "Requesting assets expansion to: %s\n", targetDirectory)
	}

	// Create parent directory if it doesn't exist
	err := os.MkdirAll(targetDirectory, DEFAULT_PERMISSIONS)
	if err != nil {
		return fmt.Errorf("Error creating parent directory: %s\n", err)
	}

	lockFile := filepath.Join(targetDirectory, "extract.lock")
	fileLock, err := obtainLock(lockFile)
	if err != nil {
		return fmt.Errorf("Error obtaining lock: %s\n", err)
	}

	locked := fileLock.Locked()
	defer unlock(fileLock)

	hashMatches := zipHashMatches(zipHash, targetDirectory)
	if hashMatches == HashMatches {
		if debugGoWrapper {
			fmt.Fprintf(os.Stderr, "Zip hash matches, skipping asset expansion (pid: %d)\n", os.Getpid())
		}
		return nil // Someone wrote it while we were waiting for the lock (ok whether locked or not)
	}

	if !locked {
		fmt.Fprintf(os.Stderr, "> Unable to lock the file %s to extract assets in %s seconds (pid: %d). EXITING NOW.\n", fileLock.Path(), LOCK_TIMEOUT, os.Getpid())
		os.Exit(1)
	}

	// We don't want to override in all cases: we just want to override if
	// the version is a local version (or if the app_hash was not found or is empty, which means that the assets weren't fully expanded the last time).
	if hashMatches == HashDoesNotMatch {
		version := strings.TrimSpace(string(ASSETS_VERSION))
		// Check with regexp for the \b (word boundary) for local
		localRegex := regexp.MustCompile(`\blocal\b`)
		if localRegex.MatchString(version) {
			if debugGoWrapper {
				fmt.Fprintf(os.Stderr, "Version is a local version, overriding existing assets (pid: %d)\n", os.Getpid())
			}
		} else {
			// Notify that the version is not a local version, so we don't override the assets.
			// Still, go on to do the launch with the existing assets.
			fmt.Fprintf(os.Stderr, `
The app_hash in "%s" does not match the app_hash of this executable and the version 
does not include "local" in the version (%s). Assets will not be overridden.
Please remove the contents to force an update. Proceeding with the launch with existing assets.`,
				version,
				targetDirectory)
			return nil
		}
	}

	// Extract assets to the target path
	err = expandAssets(targetDirectory)
	if err != nil {
		return fmt.Errorf("Error extracting the zip file with the assets: %s\n", err)
	}

	// To finalize, write the zip hash to the target directory
	err = os.WriteFile(filepath.Join(targetDirectory, "app_hash"), []byte(zipHash), 0644)
	if err != nil {
		return fmt.Errorf("Error writing app_hash: %s\n", err)
	}

	return nil
}

func unlock(fileLock *flock.Flock) {
	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "> Unlocking the file %s (pid: %d)\n", fileLock.Path(), os.Getpid())
	}
	if err := fileLock.Unlock(); err != nil {
		fmt.Fprintf(os.Stderr, "Error unlocking the file %s: %s (pid: %d)\n", fileLock.Path(), err, os.Getpid())
	}
}

// RunConfig holds configuration for extracting and running the executable
type RunConfig struct {
	ExecutableName    string
	DownloadLatestURL string
	VersionLatestURL  string
	DoUpdateCheck     bool
	ShowBrewMessage   string
}

func forceTouchWhen(path string, when time.Time) {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		err = os.WriteFile(path, []byte{}, 0o644)
		if err != nil {
			fmt.Fprintf(os.Stderr, "(ignored) Error creating file to touch %s: %s\n", path, err)
		}
	}
	err := os.Chtimes(path, when, when)
	if err != nil {
		fmt.Fprintf(os.Stderr, "(ignored) Error touching file %s: %s\n", path, err)
	}
}

func extractAndRun(config RunConfig) {
	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "Debug mode enabled (SEMA4AI_GO_WRAPPER_DEBUG=1)\n")
	}

	var targetDirectory string
	var executablePath string

	// Get the app hash for the zip file
	zipHash := strings.TrimSpace(string(ASSETS_APP_HASH))

	// Get the version
	version := strings.TrimSpace(string(ASSETS_VERSION))

	if config.DoUpdateCheck {
		// Check if there is an update available, but only do it if there is
		// no `SEMA4AI_OPTIMIZE_FOR_CONTAINER` environment variable set to 1.
		if os.Getenv("SEMA4AI_OPTIMIZE_FOR_CONTAINER") != "1" && os.Getenv("SEMA4AI_SKIP_UPDATE_CHECK") != "1" {
			checkAvailableUpdate(version, config)
		}
	}

	// Determine the appropriate path based on the operating system
	switch runtime.GOOS {
	case "windows":
		appDataDir := os.Getenv("LOCALAPPDATA")
		if appDataDir == "" {
			fmt.Fprintf(os.Stderr, "Error getting local app data directory (LOCALAPPDATA environment variable is not set)\n")
			os.Exit(1)
		}
		targetDirectory = fmt.Sprintf("%s\\sema4ai\\bin\\%s\\internal\\%s", appDataDir, config.ExecutableName, version)
		executablePath = filepath.Join(targetDirectory, fmt.Sprintf("%s.exe", config.ExecutableName))
	case "linux", "darwin":
		homeDir, err := os.UserHomeDir()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error getting user home directory: %s\n", err)
			os.Exit(1)
		}
		targetDirectory = fmt.Sprintf("%s/.sema4ai/bin/%s/internal/%s", homeDir, config.ExecutableName, version)
		executablePath = filepath.Join(targetDirectory, config.ExecutableName)
	default:
		fmt.Fprintf(os.Stderr, "Unsupported operating system\n")
		os.Exit(1)
	}

	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "targetDirectory: %s\n", targetDirectory)
		fmt.Fprintf(os.Stderr, "executablePath: %s\n", executablePath)
	}

	// If the folder doesn't exist already, we create it and copy all files
	_, err := os.Stat(targetDirectory)
	if os.IsNotExist(err) || isDirEmpty(targetDirectory) || zipHashMatches(zipHash, targetDirectory) != HashMatches {
		err = makeAssetExpansion(targetDirectory, zipHash)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error expanding assets to %s.\n%s", targetDirectory, err)
			os.Exit(1)
		}
	} else {
		if debugGoWrapper {
			fmt.Fprintf(os.Stderr, "Skipping asset expansion (path already exists: %s)\n", targetDirectory)
		}
	}

	touchFile := filepath.Join(targetDirectory, "lastLaunchTouch")
	forceTouchWhen(touchFile, time.Now())

	cmd := exec.Command(executablePath, os.Args[1:]...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	err = cmd.Run()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error executing %s: %s\n", config.ExecutableName, err)
		os.Exit(1)
	}
}

func main() {
	const ACTION_SERVER_LATEST_BASE_URL = "https://cdn.sema4.ai/action-server/releases/latest/"
	const VERSION_LATEST_URL = ACTION_SERVER_LATEST_BASE_URL + "version.txt"

	var osPathInUrl, actionExe string
	switch runtime.GOOS {
	case "windows":
		osPathInUrl = "windows64"
		actionExe = "action-server.exe"
	case "linux":
		osPathInUrl = "linux64"
		actionExe = "action-server"
	case "darwin":
		actionExe = "action-server"
		switch runtime.GOARCH {
		case "arm64":
			osPathInUrl = "macos-arm64"
		case "amd64":
			osPathInUrl = "macos64"
		default:
			fmt.Printf("Unknown architecture: %s\n", runtime.GOARCH)
		}
	default:
		fmt.Fprintf(os.Stderr, "Unsupported operating system\n")
		os.Exit(1)
	}
	downloadLatestUrl, _ := url.JoinPath(ACTION_SERVER_LATEST_BASE_URL, osPathInUrl, actionExe)

	// Create the configuration struct instead of passing multiple parameters
	config := RunConfig{
		ExecutableName:    "action-server",
		DownloadLatestURL: downloadLatestUrl,
		VersionLatestURL:  VERSION_LATEST_URL,
		DoUpdateCheck:     true,
		ShowBrewMessage:   "brew update && brew install sema4ai/tools/action-server",
	}

	extractAndRun(config)
}
