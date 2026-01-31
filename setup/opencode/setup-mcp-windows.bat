@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\..\"
set "CONFIG_DIR=%USERPROFILE%\.config\opencode"
set "CONFIG_FILE=%CONFIG_DIR%\opencode.json"

echo Setting up Yaade for OpenCode (Windows)
echo ========================================

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo UV is not installed. Please install UV first:
    echo    https://docs.astral.sh/uv/getting-started/installation/
    echo    Or use: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    exit /b 1
)

echo UV found

cd /d "%PROJECT_ROOT%"

echo Installing dependencies...
uv sync

echo Creating OpenCode config directory...
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

echo Configuring MCP server...

REM Get the absolute path without trailing slash
for %%i in ("%PROJECT_ROOT%.") do set "PROJECT_ROOT_ABS=%%~fi"

if exist "%CONFIG_FILE%" (
    echo Existing config found, updating...
    copy "%CONFIG_FILE%" "%CONFIG_FILE%.backup" >nul

    python -c "import json; f=open(r'%CONFIG_FILE%', 'r'); config=json.load(f); f.close(); config.setdefault('mcp', {}); config['mcp']['yaade']={'type': 'local', 'command': ['uv', '--project', r'%PROJECT_ROOT_ABS%', 'run', 'yaade', 'serve'], 'environment': {}, 'enabled': True}; f=open(r'%CONFIG_FILE%', 'w'); json.dump(config, f, indent=2); f.close(); print('Updated config')"
) else (
    echo Creating new config file...
    (
    echo {
    echo   "$schema": "https://opencode.ai/config.json",
    echo   "mcp": {
    echo     "yaade": {
    echo       "type": "local",
    echo       "command": ["uv", "--project", "%PROJECT_ROOT_ABS:\=/%", "run", "yaade", "serve"^],
    echo       "environment": {},
    echo       "enabled": true
    echo     }
    echo   }
    echo }
    ) > "%CONFIG_FILE%"
)

echo Setup complete!
echo.
echo Configuration details:
echo    Config file: %CONFIG_FILE%
echo    Project root: %PROJECT_ROOT_ABS%
echo.
echo To use Yaade:
echo    1. Restart OpenCode if it's running
echo    2. The MCP server will be available as 'yaade'
echo    3. Use tools like add_memory, search_memories, etc.
echo.
echo To test the server manually:
echo    cd "%PROJECT_ROOT_ABS%" ^&^& uv run yaade serve

pause
