@echo off
rem Executor de imagens: descreve todas as imagens da pasta coloque_imagem_aqui
rem Saidas em "Transcricoes (saidas)". Passe --falar para gerar audio tambem.
cd /d "%~dp0"
call venv\Scripts\activate.bat
python main.py imagem %*
echo.
pause
