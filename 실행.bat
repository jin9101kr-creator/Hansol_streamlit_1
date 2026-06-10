@echo off
chcp 65001 > nul
echo 주식 대시보드를 시작합니다...
start "" "C:\Users\admin\AppData\Local\Programs\Python\Python313\python.exe" -m streamlit run "%~dp0korean_stock_dashboard.py"
timeout /t 3 /nobreak > nul
start "" "http://localhost:8501"
