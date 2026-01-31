@echo off
setlocal enabledelayedexpansion

echo Setting up Claude Desktop MCP configuration for Yaade (Windows)...

:: Get the current project directory
set "PROJECT_DIR=%~dp0..\.."
for %%i in ("%PROJECT_DIR%") do set "PROJECT_DIR=%%~fi"

:: Find uv.exe in PATH
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: uv not found in PATH. Please install uv first.
    echo You can install it from: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

:: Get full path to uv
for /f "tokens=*" %%i in ('where uv') do set "UV_PATH=%%i"

:: Claude Desktop config directory
set "CLAUDE_CONFIG_DIR=%APPDATA%\Claude"
set "CLAUDE_CONFIG_FILE=%CLAUDE_CONFIG_DIR%\claude_desktop_config.json"

:: Create Claude config directory if it doesn't exist
if not exist "%CLAUDE_CONFIG_DIR%" (
    mkdir "%CLAUDE_CONFIG_DIR%"
    echo Created Claude config directory: %CLAUDE_CONFIG_DIR%
)

:: Check if config file exists
if exist "%CLAUDE_CONFIG_FILE%" (
    echo Backing up existing config to claude_desktop_config.json.backup
    copy "%CLAUDE_CONFIG_FILE%" "%CLAUDE_CONFIG_FILE%.backup" >nul
)

:: Create or update the configuration
echo Creating Claude Desktop MCP configuration...

:: Escape backslashes for JSON
set "UV_PATH_ESCAPED=%UV_PATH:\=\\%"
set "PROJECT_DIR_ESCAPED=%PROJECT_DIR:\=\\%"

(
echo {
echo   "mcpServers": {
echo     "yaade": {
echo       "command": "!UV_PATH_ESCAPED!",
echo       "args": ["run", "--directory", "!PROJECT_DIR_ESCAPED!", "yaade", "serve"],
echo       "env": {
echo         "YAADE_LOG_LEVEL": "INFO"
echo       }
echo     }
echo   }
echo }
) > "%CLAUDE_CONFIG_FILE%"

echo.
echo Claude Desktop MCP configuration has been set up successfully!
echo.
echo Configuration details:
echo - Project directory: %PROJECT_DIR%
echo - UV path: %UV_PATH%
echo - Config file: %CLAUDE_CONFIG_FILE%
echo.
echo Please restart Claude Desktop for the changes to take effect.
echo.
pause
