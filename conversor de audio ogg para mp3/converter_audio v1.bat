@echo off
cd /d "%~dp0"
if not exist "meu_audio.ogg" (
    echo Arquivo meu_audio.ogg nao encontrado nesta pasta.
    pause
    exit /b 1
)
ffmpeg -y -i "meu_audio.ogg" "meu_audio.mp3"
if errorlevel 1 (
    echo Erro na conversao. Verifique se o ffmpeg esta instalado.
) else (
    echo Conversao concluida: meu_audio.mp3
)
pause
