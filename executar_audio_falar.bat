@echo off
rem Executor: processa os audios de coloque_audio_aqui e TAMBEM gera o resumo em audio (.mp3)
rem Saidas em "Transcricoes (saidas)". Requer internet (gTTS).
cd /d "%~dp0"
call venv\Scripts\activate.bat
python main.py audio --falar %*
echo.
pause
