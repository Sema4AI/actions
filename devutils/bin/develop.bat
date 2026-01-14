@echo off

pushd .
SET scriptPath=%~dp0
SET scriptPath=%scriptPath:~0,-1%
cd /D %scriptPath%

SET projectName=action-server
SET rccPath=%scriptPath%\rcc.exe
SET condaYaml=%scriptPath%\develop.yaml
SET activatePath=%scriptPath%\activate.bat

echo 
:: Get RCC binary using joshyorko/rcc GitHub releases
SET rccUrl=https://github.com/joshyorko/rcc/releases/download/v18.13.1/rcc-windows64.exe
IF NOT EXIST "%rccPath%" (
    curl -o %rccPath% %rccUrl% --fail || goto env_error
)

:: Create a new or replace an already existing virtual environment.
IF EXIST "%activatePath%" (
    echo Detected existing development environment.
    echo Do you want to create a clean environment? [Y/N]
    choice /C YN /N /M "Select [Y]es (clean environment) or [N]o (use existing):"
    IF ERRORLEVEL 2 GOTO env_setup
)

:env_new
echo Creating a clean environment...
echo command: %rccPath% ht vars %condaYaml% --space %projectName% --sema4ai > %activatePath%
%rccPath% ht vars %condaYaml% --space %projectName% --sema4ai > %activatePath%

:env_setup
:: Activate the virtual environment and install dependencies everytime.
echo calling: call %activatePath%
call %activatePath%

echo.
echo Developer env. ready!
goto end

:env_error
echo.
echo Development environment setup failed!
goto end

:end
SET rccPath=
SET condaYamlPath=
SET scriptPath=
SET projectName=
popd
pause
