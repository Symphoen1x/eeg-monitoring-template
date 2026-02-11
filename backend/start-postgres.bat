@echo off
echo Starting PostgreSQL Server...
echo.
echo Keep this window open while working on the project!
echo Press Ctrl+C to stop the server
echo.
cd "C:\Program Files\PostgreSQL\18\bin"
postgres.exe -D "C:\Program Files\PostgreSQL\18\data"
pause
