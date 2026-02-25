@echo off
title DBFarmer v2 - Dragon Ball Legends
color 0D
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
    pause
    goto :eof
)
if "%choice%"=="2" (
    python capture.py
    pause
    goto :eof
)
if "%choice%"=="3" (
    python main.py
    pause
    goto :eof
)
if "%choice%"=="4" exit

echo Invalid choice
pause
