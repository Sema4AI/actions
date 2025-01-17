package main

import (
	"archive/zip"
	"bytes"
	"embed"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"

	"golang.org/x/mod/semver"
)

//go:embed all:assets/*
var content embed.FS

// Constants
const ACTION_SERVER_LATEST_BASE_URL = "https://cdn.sema4.ai/action-server/releases/latest/"
const VERSION_LATEST_URL = ACTION_SERVER_LATEST_BASE_URL + "version.txt"

var debugGoWrapper = os.Getenv("SEMA4AI_ACTION_SERVER_GO_WRAPPER_DEBUG") == "1"

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

func getLatestVersion() (string, error) {
	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "Getting latest version from %s\n", VERSION_LATEST_URL)
	}
	// Get the data from the URL
	versionResponse, err := http.Get(VERSION_LATEST_URL)
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

func checkAvailableUpdate(version string) {
	// Get the latest version
	latestVersion, err := getLatestVersion()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Verifying latest version failed:%s\n", err)
		return
	}
	// Compare the given version with the latest one
	compareResult := semver.Compare(strings.TrimSpace("v"+version), strings.TrimSpace("v"+latestVersion))

	// If the current version is a previous version than the latest print the update suggestions
	if compareResult == -1 {
		// Construct the needed URL path to get to the downloadable object
		var actionOS, actionExe string
		switch runtime.GOOS {
		case "windows":
			actionOS = "windows64"
			actionExe = "action-server.exe"
		case "linux":
			actionOS = "linux64"
			actionExe = "action-server"
		case "darwin":
			actionExe = "action-server"
			switch runtime.GOARCH {
			case "arm64":
				actionOS = "macos-arm64"
			case "amd64":
				actionOS = "macos64"
			default:
				fmt.Printf("Unknown architecture: %s\n", runtime.GOARCH)
			}
		default:
			fmt.Fprintf(os.Stderr, "Unsupported operating system\n")
			os.Exit(1)
		}
		colorT := &ColorType{}
		urlPath, _ := url.JoinPath(ACTION_SERVER_LATEST_BASE_URL, actionOS, actionExe)
		fmt.Fprintf(os.Stderr, "\n ⏫ A new version of action-server is now available: %s → %s \n", colorT.Yellow(version), colorT.Green(latestVersion))
		if runtime.GOOS == "darwin" {
			fmt.Fprintf(os.Stderr, "    To update, download from: %s \n", colorT.Bold(urlPath))
			fmt.Fprintf(os.Stderr, "    Or run: %s \n\n", colorT.Bold("brew update && brew install sema4ai/tools/action-server"))
		} else {
			fmt.Fprintf(os.Stderr, "    To update, download from: %s \n\n", colorT.Bold(urlPath))
		}
	}
}

func expandAssets(src, dest string) error {
	// Read the zip file from the embedded filesystem
	zipPath := fmt.Sprintf("%s/assets.zip", src)
	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "Expanding assets from %s to %s\n", zipPath, dest)
	}
	zipContent, err := content.ReadFile(zipPath)
	if err != nil {
		return err
	}

	// Create a reader for the zip content
	zipReader, err := zip.NewReader(bytes.NewReader(zipContent), int64(len(zipContent)))
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
			err := os.MkdirAll(destPath, 0755)
			if err != nil {
				return err
			}
			continue
		}

		// Create destination directory if it doesn't exist
		err := os.MkdirAll(filepath.Dir(destPath), 0755)
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
		err = os.Chmod(destPath, 0755)
		if err != nil {
			return err
		}
	}

	return nil
}

func main() {
	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "Debug mode enabled (SEMA4AI_ACTION_SERVER_GO_WRAPPER_DEBUG=1)\n")
	}

	var actionServerPath string
	var executablePath string

	// Read the version
	versionData, err := content.ReadFile("assets/version.txt")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading version.txt: %s\n", err)
		os.Exit(1)
	}
	version := strings.TrimSpace(string(versionData))

	// Check if there is an update available, but only do it if there is
	// no `SEMA4AI_OPTIMIZE_FOR_CONTAINER` environment variable set to 1.
	if os.Getenv("SEMA4AI_OPTIMIZE_FOR_CONTAINER") != "1" && os.Getenv("SEMA4AI_SKIP_UPDATE_CHECK") != "1" {
		checkAvailableUpdate(version)
	}

	// Determine the appropriate path based on the operating system
	switch runtime.GOOS {
	case "windows":
		appDataDir := os.Getenv("LOCALAPPDATA")
		actionServerPath = fmt.Sprintf("%s\\sema4ai\\action-server\\%s", appDataDir, version)
		executablePath = filepath.Join(actionServerPath, "action-server.exe")
	case "linux", "darwin":
		homeDir, err := os.UserHomeDir()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error getting user home directory: %s\n", err)
			os.Exit(1)
		}
		actionServerPath = fmt.Sprintf("%s/.sema4ai/action-server/%s", homeDir, version)
		executablePath = filepath.Join(actionServerPath, "action-server")
	default:
		fmt.Fprintf(os.Stderr, "Unsupported operating system\n")
		os.Exit(1)
	}

	if debugGoWrapper {
		fmt.Fprintf(os.Stderr, "actionServerPath: %s\n", actionServerPath)
		fmt.Fprintf(os.Stderr, "executablePath: %s\n", executablePath)
	}

	// If the folder doesn't exist already, we create it and copy all files
	_, err = os.Stat(actionServerPath)
	if os.IsNotExist(err) {
		err = os.MkdirAll(actionServerPath, 0755)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error creating directory: %s\n", err)
			os.Exit(1)
		}

		err = expandAssets("assets", actionServerPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error extracting the zip file with the assets: %s\n", err)
			os.Exit(1)
		}
	} else {
		if debugGoWrapper {
			fmt.Fprintf(os.Stderr, "Skipping asset expansion (actionServerPath already exists: %s)\n", actionServerPath)
		}
	}

	cmd := exec.Command(executablePath, os.Args[1:]...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	err = cmd.Run()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error executing action-server: %s\n", err)
		os.Exit(1)
	}
}
