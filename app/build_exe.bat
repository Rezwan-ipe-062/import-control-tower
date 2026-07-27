@echo off
REM Build Import Control Tower executable with PyInstaller
REM Requires: pip install pyinstaller

echo Building Import Control Tower executable...

pyinstaller --onefile --windowed --name "ImportControlTower" ^
    --add-data "config;config" ^
    --add-data "reference;reference" ^
    --hidden-import "pandas" ^
    --hidden-import "openpyxl" ^
    --hidden-import "plotly" ^
    --hidden-import "streamlit" ^
    app.py

echo.
echo Build complete. Executable is in dist/ImportControlTower.exe
pause
