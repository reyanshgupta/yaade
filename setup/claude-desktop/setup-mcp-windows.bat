@echo off
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0..\.."
for %%i in ("%PROJECT_DIR%") do set "PROJECT_DIR=%%~fi"

echo Setting up Yaade for Claude Desktop (Windows)
echo ==============================================

set "USE_PIP_MODE=0"
where yaade >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('where yaade') do set "YAADE_PATH=%%i"
    echo !YAADE_PATH! | findstr /B /C:"!PROJECT_DIR!\.venv\" >nul
    if %errorlevel% neq 0 set "USE_PIP_MODE=1"
)
if "!USE_PIP_MODE!"=="0" (
    where uv >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: yaade not found in PATH and uv not installed.
        echo   - Install yaade globally: pip install yaade
        echo   - Or install uv and run this script from the yaade repo.
        pause
        exit /b 1
    )
    for /f "tokens=*" %%i in ('where uv') do set "UV_PATH=%%i"
    echo Using repo + uv (central directory: %PROJECT_DIR%)
) else (
    echo Using pip-installed yaade: !YAADE_PATH!
)

set "CLAUDE_CONFIG_DIR=%APPDATA%\Claude"
set "CLAUDE_CONFIG_FILE=%CLAUDE_CONFIG_DIR%\claude_desktop_config.json"

if not exist "%CLAUDE_CONFIG_DIR%" mkdir "%CLAUDE_CONFIG_DIR%"
if exist "%CLAUDE_CONFIG_FILE%" copy "%CLAUDE_CONFIG_FILE%" "%CLAUDE_CONFIG_FILE%.backup" >nul

echo Configuring MCP server...

if "!USE_PIP_MODE!"=="1" (
    python "%PROJECT_DIR%\setup\mcp_config.py" write claude-desktop "%CLAUDE_CONFIG_FILE%" 1 "!YAADE_PATH!"
) else (
    python "%PROJECT_DIR%\setup\mcp_config.py" write claude-desktop "%CLAUDE_CONFIG_FILE%" 0 "!UV_PATH!" "!PROJECT_DIR!"
)

echo.
echo Setup complete!
echo.
echo Configuration details:
if "!USE_PIP_MODE!"=="1" (
    echo    Mode: pip-installed yaade
    echo    Yaade path: !YAADE_PATH!
) else (
    echo    Mode: run from repo (uv^)
    echo    Project root: %PROJECT_DIR%
)
echo    Config file: %CLAUDE_CONFIG_FILE%
echo.
echo Restart Claude Desktop for changes to take effect.
echo.
pause
