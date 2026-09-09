@echo off
cd /d "%~dp0"
py src\main.py
if errorlevel 1 pause
