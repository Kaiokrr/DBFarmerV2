@echo off
title DBFarmer v2 - Dragon Ball Legends
color 0D

:menu
cls
echo.
echo  ========================================
echo   DBFarmer v2 - Dragon Ball Legends
echo   Adapted for BlueStacks 5
echo  ========================================
echo.
echo  What do you want to do?
echo.
echo  [1] Install dependencies
echo  [2] Capture reference images
echo  [3] Launch the bot
echo  [4] Quit
echo.
set /p choice=" Choice (1-4): "

if "%choice%"=="1" (
    python install.py
    goto menu
)
if "%choice%"=="2" (
    python capture.py
    goto menu
)
if "%choice%"=="3" (
    python main.py
    pause
    goto menu
)
if "%choice%"=="4" exit

echo Invalid choice
timeout /t 2 >nul
goto menu
