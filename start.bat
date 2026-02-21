@echo off
title DBFarmer v2 - Dragon Ball Legends
color 0D
echo.
echo  ========================================
echo   DBFarmer v2 - Dragon Ball Legends
echo   Adapte pour BlueStacks 5
echo  ========================================
echo.
echo  Que veux-tu faire ?
echo.
echo  [1] Installer les dependances
echo  [2] Capturer les images de reference
echo  [3] Lancer le bot
echo  [4] Quitter
echo.
set /p choice=" Choix (1-4): "

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

echo Choix invalide
pause
