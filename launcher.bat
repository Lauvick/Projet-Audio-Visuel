@echo off
REM Script de lancement rapide pour le projet HERMANN
REM Réduction de Bruit IA

echo ===============================================
echo   PROJET HERMANN - REDUCTION DE BRUIT IA
echo ===============================================
echo.

:MENU
echo Choisissez une option:
echo.
echo [1] Installer les dependances
echo [2] Generer un fichier audio de test
echo [3] Lancer la reduction de bruit IA
echo [4] Executer le pipeline complet (test + denoise)
echo [5] Quitter
echo.
set /p choice="Votre choix (1-5): "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto GENERATE
if "%choice%"=="3" goto DENOISE
if "%choice%"=="4" goto FULL
if "%choice%"=="5" goto END
goto MENU

:INSTALL
echo.
echo Installation des dependances...
pip install -r requirements.txt
echo.
echo Installation terminee!
pause
goto MENU

:GENERATE
echo.
echo Generation du fichier audio de test...
python generate_test_audio.py
echo.
pause
goto MENU

:DENOISE
echo.
echo Lancement de la reduction de bruit IA...
python denoise_agent.py
echo.
pause
goto MENU

:FULL
echo.
echo === PIPELINE COMPLET ===
echo Etape 1: Generation du fichier test...
python generate_test_audio.py
echo.
echo Etape 2: Reduction de bruit IA...
python denoise_agent.py
echo.
echo === TERMINE ===
pause
goto MENU

:END
echo.
echo Merci d'avoir utilise le projet HERMANN!
echo.
exit
