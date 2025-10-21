@echo off
REM Activate virtual environment
call ".venv\Scripts\activate.bat"

REM Run app in a separate process so this CMD can close
start "" python app.py

REM Exit immediately
exit
