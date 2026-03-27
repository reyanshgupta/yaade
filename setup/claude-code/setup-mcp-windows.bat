@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\..\"
set "CONFIG_FILE=%USERPROFILE%\.claude.json"

echo Setting up Yaade for Claude Code (Windows)
echo ===========================================

set "USE_PIP_MODE=0"
where yaade >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('where yaade') do set "YAADE_PATH=%%i"
    for %%i in ("%PROJECT_ROOT%.") do set "PROJECT_ROOT_ABS=%%~fi"
    echo !YAADE_PATH! | findstr /B /C:"!PROJECT_ROOT_ABS!\.venv\" >nul
    if %errorlevel% neq 0 set "USE_PIP_MODE=1"
)
if "!USE_PIP_MODE!"=="0" (
    where uv >nul 2>nul
    if %errorlevel% neq 0 (
        echo Error: yaade not found in PATH and uv not installed.
        echo   - Install yaade globally: pip install yaade
        echo   - Or install uv and run this script from the yaade repo.
        exit /b 1
    )
    for /f "tokens=*" %%i in ('where uv') do set "UV_PATH=%%i"
    cd /d "%PROJECT_ROOT%"
    echo Installing dependencies...
    uv sync
    for %%i in ("%PROJECT_ROOT%.") do set "PROJECT_ROOT_ABS=%%~fi"
) else (
    echo Using pip-installed yaade: !YAADE_PATH!
    for %%i in ("%PROJECT_ROOT%.") do set "PROJECT_ROOT_ABS=%%~fi"
)

if exist "%CONFIG_FILE%" copy "%CONFIG_FILE%" "%CONFIG_FILE%.backup" >nul

echo Configuring MCP server...

if "!USE_PIP_MODE!"=="1" (
    python "%PROJECT_ROOT_ABS%\setup\mcp_config.py" write claude-code "%CONFIG_FILE%" 1 "!YAADE_PATH!"
) else (
    python "%PROJECT_ROOT_ABS%\setup\mcp_config.py" write claude-code "%CONFIG_FILE%" 0 "!UV_PATH!" "!PROJECT_ROOT_ABS!"
)

echo Setup complete!
echo.
echo Configuration details:
echo    Config file: %CONFIG_FILE%
if "!USE_PIP_MODE!"=="1" (
    echo    Mode: pip-installed yaade
    echo    Yaade path: !YAADE_PATH!
    echo.
    echo To test: yaade serve
) else (
    echo    Mode: run from repo (uv^)
    echo    Project root: %PROJECT_ROOT_ABS%
    echo.
    echo To test: cd "%PROJECT_ROOT_ABS%" ^&^& uv run yaade serve
)
echo.
echo Restart Claude Code to use Yaade.
echo.
pause
