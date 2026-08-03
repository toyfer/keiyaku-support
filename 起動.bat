@echo off
chcp 932 >nul
cd /d "%~dp0"
if exist python\python.exe (
  python\python.exe run.py
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo Python が見つかりません。pip install 後に python run.py を実行するか、
    echo Embeddable Python を python\ に配置してください。
    pause
    exit /b 1
  )
  python run.py
)
if errorlevel 1 pause
