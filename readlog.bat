@echo off
set "LOGFILE=../sublimeapistudy_log.txt"
if not exist "%LOGFILE%" (
    echo Log file not found: %LOGFILE%
    pause
    exit /b
)
powershell -Command "Get-Content -Path '%LOGFILE%' -Tail 10 -Wait"