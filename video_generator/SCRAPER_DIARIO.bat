@echo off
echo ============================================
echo   AutoTok Stats Scraper — Ejecucion manual
echo   %date% %time%
echo ============================================

set BASEDIR=C:\Users\gasco\Documents\PROYECTOS_WEB\autotok-videos\video_generator
set PYTHON=python

cd /d "%BASEDIR%"

echo Usando Python: %PYTHON%
echo.

"%PYTHON%" "%BASEDIR%\stats_scraper.py"

echo.
echo ============================================
echo   Scraper completado
echo ============================================
echo.
pause
