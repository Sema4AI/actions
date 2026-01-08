@echo off
REM UV-based Development Environment Setup
REM Syncs all workspace packages for development

pushd .
SET scriptPath=%~dp0
SET scriptPath=%scriptPath:~0,-1%
SET repoRoot=%scriptPath%\..\..

echo.
echo === UV-based Development Environment Setup ===
echo.

:: Check if uv is installed
where uv >nul 2>nul
IF ERRORLEVEL 1 (
    echo Error: uv not found.
    echo Please install uv v0.9.18 or later: https://github.com/astral-sh/uv
    goto env_error
)

echo uv version:
uv --version
echo.

:: Run uv sync --all-packages from repo root to install all workspace packages
echo Running uv sync --all-packages (installs all workspace packages)...
cd /D "%repoRoot%"
uv sync --all-packages

echo.
echo Developer env. ready!
echo.
echo Usage:
echo   cd action_server
echo   uv run list          - List available commands
echo   uv run lint          - Run linting
echo   uv run test          - Run tests
echo   uv run build-exe     - Build executable
echo.
echo Workspace packages installed:
echo   - sema4ai-action-server
echo   - sema4ai-actions
echo   - sema4ai-build-common
echo   - sema4ai-common
echo   - sema4ai-devutils
echo   - sema4ai-mcp
echo   - sema4ai-http-helper
echo.

goto end

:env_error
echo.
echo Development environment setup failed!
goto end

:end
SET scriptPath=
SET repoRoot=
popd
pause
