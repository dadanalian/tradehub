@echo off
title TradeHub - Foreign Trade Platform
echo.
echo ============================================
echo   ?? TradeHub ??????
echo ============================================
echo.
echo   Starting server...
echo   Open http://127.0.0.1:5000 in your browser
echo.
echo ============================================
echo.
cd /d D:\tradehub
python -c "from app import app; app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)"
pause
