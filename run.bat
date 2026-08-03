@echo off
cd /d "%~dp0"
if exist python\python.exe (
  python\python.exe run.py
) else (
  python run.py
)
pause
