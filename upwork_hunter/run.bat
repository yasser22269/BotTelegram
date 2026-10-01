@echo off
cd /d "%~dp0"
chcp 65001 >nul
:loop
python bot.py
echo Bot stopped, restarting in 10s...
timeout /t 10 >nul
goto loop
