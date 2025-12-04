@echo off
title Frère Théodore - Générateur de Shorts
echo.
echo ========================================
echo   🎬 Frère Théodore - Générateur de Shorts
echo ========================================
echo.
echo Démarrage de l'application...
echo.

cd /d "%~dp0"
.\.conda\python.exe ai_agent\app_gui.py

if errorlevel 1 (
    echo.
    echo ❌ Une erreur s'est produite.
    echo Appuyez sur une touche pour fermer...
    pause > nul
)
