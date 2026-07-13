@echo off
REM Lanza Trading FCP con el Python del entorno virtual (.venv), sin PyCharm.
REM Asi los botones heredan el .venv (con pandas, ib_insync, etc.) via sys.executable.
cd /d "C:\Users\favio\Desktop\TRADING"
start "" ".venv\Scripts\pythonw.exe" "Trading_FCP.py"
