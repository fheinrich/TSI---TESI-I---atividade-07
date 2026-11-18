@echo off
rem Executor: processa todos os audios da pasta coloque_audio_aqui
rem Saidas em "Transcricoes (saidas)". Passe --falar para gerar audio tambem.
cd /d "%~dp0"
call venv\Scripts\activate.bat
python main.py audio %*
echo.
pause
