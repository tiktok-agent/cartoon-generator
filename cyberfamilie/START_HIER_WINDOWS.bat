@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Cyberfamilie - gratis filmstudio ===
echo Installeer eerst Python 3.10+ en FFmpeg (ffmpeg en ffprobe op PATH).
echo.
python -m pip install -r requirements.txt
if errorlevel 1 (echo Installatie mislukt.&pause&exit /b 1)
python pipeline.py prepare
python pipeline.py status
:menu
echo.
echo 1 = Probeer gratis Wan, Hunyuan en LTX (internet nodig)
echo 2 = Controleer welke scenes klaar zijn
echo 3 = Monteer echte video-clips tot MP4
 echo 4 = Stop
echo Voeg andere gratis video's toe via: python pipeline.py import --shot shot_01 --file jouwclip.mp4
set /p choice=Keuze: 
if "%choice%"=="1" python pipeline.py render --provider auto
if "%choice%"=="2" python pipeline.py status
if "%choice%"=="3" python pipeline.py assemble
if "%choice%"=="4" exit /b 0
goto menu