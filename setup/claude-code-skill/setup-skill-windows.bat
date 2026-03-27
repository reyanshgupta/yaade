@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "SKILL_DIR=%USERPROFILE%\.claude\skills\yaade"

echo Setting up Yaade skill for Claude Code (Windows)
echo =================================================

:: Create skill directory
if not exist "%SKILL_DIR%" mkdir "%SKILL_DIR%"

:: Copy skill file
copy "%SCRIPT_DIR%SKILL.md" "%SKILL_DIR%\SKILL.md" >nul

echo Setup complete!
echo.
echo Skill installed to: %SKILL_DIR%
echo.
echo Usage:
echo   - Type /yaade to invoke the skill
echo   - Or say "remember this" / "what do you remember about"
echo.
echo Note: Make sure the Yaade MCP server is configured and running.
echo       Run: yaade serve
echo.
pause
