@echo off
chcp 65001 >nul
echo Installing Git hooks...
echo.

REM Save current directory
set ORIGINAL_DIR=%CD%

REM Get project root (where .git directory is)
for /f "delims=" %%i in ('git rev-parse --show-toplevel 2^>nul') do set PROJECT_ROOT=%%i

if "%PROJECT_ROOT%"=="" (
    echo ERROR: Not a git repository
    echo Please run this script from within a git repository
    exit /b 1
)

REM Convert Unix path to Windows path (Git Bash returns Unix-style paths)
set PROJECT_ROOT=%PROJECT_ROOT:/=\%

echo Project root: %PROJECT_ROOT%
echo.

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Check if .git-hooks/pre-commit exists
if not exist ".git-hooks\pre-commit" (
    echo ERROR: Hook template not found: .git-hooks\pre-commit
    echo Please ensure the project structure is correct
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)

REM Backup existing hook
if exist ".git\hooks\pre-commit" (
    echo Backing up existing hook...
    copy ".git\hooks\pre-commit" ".git\hooks\pre-commit.backup" >nul
)

REM Copy hook file
echo Installing pre-commit hook...
copy ".git-hooks\pre-commit" ".git\hooks\pre-commit" >nul

if errorlevel 1 (
    echo ERROR: Failed to install hook
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)

echo.
echo SUCCESS: Git hook installed
echo.
echo What it does:
echo   - Blocks AI agents from committing to main branch
echo   - Warns humans when committing to main branch
echo.
echo Test the hook:
echo   1. Switch to main: git checkout main
echo   2. Set env var: set AGENT_TASK=true
echo   3. Try commit: git commit -m "test"
echo   4. Should be rejected
echo.

REM Return to original directory
cd /d "%ORIGINAL_DIR%"

pause
