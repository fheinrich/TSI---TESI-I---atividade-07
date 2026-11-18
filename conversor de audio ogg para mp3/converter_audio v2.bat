@echo off
rem Converte todos os .ogg e .m4a da pasta coloque_audio_aqui para .mp3
cd /d "%~dp0coloque_audio_aqui"
for %%f in (*.ogg *.m4a) do (
    echo Convertendo %%f ...
    ffmpeg -y -loglevel error -i "%%f" "%%~nf.mp3"
)
echo Conversao concluida.
pause
