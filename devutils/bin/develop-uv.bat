@echo off
REM UV-based Development Environment Setup
REM Just checks for uv, then runs uv sync in action_server

pushd .
SET scriptPath=%~dp0
SET scriptPath=%scriptPath:~0,-1%
SET actionServerPath=%scriptPath%\..\..\action_server

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

:: Run uv sync in action_server directory
echo Running uv sync in action_server...
cd /D "%actionServerPath%"
uv sync

echo.
echo Developer env. ready!
echo.
echo Usage:
echo   cd action_server
echo   uv run list          - List available commands
echo   uv run lint          - Run linting
echo   uv run test          - Run tests
echo.

goto end

:env_error
echo.
echo Development environment setup failed!
goto end

:end
SET scriptPath=
SET actionServerPath=
popd
pause
