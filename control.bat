@echo off
REM بوت مستقل - لوحة التحكم
REM Freelancer Bot - Control Panel

:menu
cls
echo.
echo ============================================
echo   بوت مستقل - لوحة التحكم
echo   Freelancer Bot - Control Panel
echo ============================================
echo.
echo 1. شغّل البوت
echo 2. اختبر البوت
echo 3. عرض الحالة
echo 4. إيقاف البوت
echo 5. الخروج
echo.
set /p choice="اختر (1-5): "

if "%choice%"=="1" goto start_bot
if "%choice%"=="2" goto test_bot
if "%choice%"=="3" goto status
if "%choice%"=="4" goto stop_bot
if "%choice%"=="5" goto exit
goto menu

:start_bot
cls
echo.
echo ⏳ جاري تشغيل البوت...
echo.
cd C:\xampp\htdocs\BotTelegram
python bot_working.py
goto menu

:test_bot
cls
echo.
echo 🧪 اختبار البوت...
echo.
cd C:\xampp\htdocs\BotTelegram
python test_connection.py
pause
goto menu

:status
cls
echo.
echo 📊 حالة البوت:
echo.
tasklist | findstr python
echo.
if %errorlevel% equ 0 (
    echo ✅ البوت يعمل!
) else (
    echo ❌ البوت لا يعمل
)
echo.
pause
goto menu

:stop_bot
cls
echo.
echo ⏹️ إيقاف البوت...
echo.
taskkill /F /IM python.exe
echo ✅ تم
echo.
pause
goto menu

:exit
cls
echo.
echo 👋 شكراً!
echo.

