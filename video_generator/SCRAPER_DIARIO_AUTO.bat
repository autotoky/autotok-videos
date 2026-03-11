@echo off
:: AutoTok Stats Scraper — Ejecucion automatica (sin pause, para Task Scheduler)
:: Logs en scraper_log.txt
:: Si se llama con /apagar, apaga el PC al terminar

:: Rutas absolutas para que funcione desde Task Scheduler
set BASEDIR=C:\Users\gasco\Documents\PROYECTOS_WEB\autotok-videos\video_generator
set LOGFILE=%BASEDIR%\scraper_log.txt
set PYTHON=python

cd /d "%BASEDIR%"

echo [%date% %time%] Scraper iniciado >> "%LOGFILE%"
"%PYTHON%" "%BASEDIR%\stats_scraper.py" >> "%LOGFILE%" 2>&1
echo [%date% %time%] Scraper completado (exit code: %ERRORLEVEL%) >> "%LOGFILE%"
echo. >> "%LOGFILE%"

:: Apagar PC si se paso el parametro /apagar
if "%~1"=="/apagar" (
    echo [%date% %time%] Apagando PC en 60 segundos... >> "%LOGFILE%"
    shutdown /s /t 60 /c "AutoTok Scraper completado — apagando PC"
)
