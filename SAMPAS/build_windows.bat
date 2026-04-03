@echo off
REM ============================================================
REM  SAMPAS  Windows 빌드 스크립트
REM  실행 전: pip install pyinstaller 완료 필요
REM ============================================================

echo.
echo  ====================================
echo   SAMPAS Build Script
echo  ====================================
echo.

REM 1. 의존성 설치
echo [1/3] Installing dependencies...
pip install pyinstaller numpy
if errorlevel 1 (
    echo ERROR: pip install failed
    pause & exit /b 1
)

REM 2. PyInstaller로 .exe 생성
echo.
echo [2/3] Building EXE with PyInstaller...
pyinstaller --clean SAMPAS.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause & exit /b 1
)

REM 3. Inno Setup 인스톨러 생성 (Inno Setup이 설치된 경우)
echo.
echo [3/3] Creating installer with Inno Setup...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
    %ISCC% SAMPAS_installer.iss
    echo Installer created in installer_output\
) else (
    echo [SKIP] Inno Setup not found. EXE is at dist\SAMPAS\SAMPAS.exe
)

echo.
echo  Build complete!
echo  ====================================
pause
