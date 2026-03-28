@echo off
echo ============================================================
echo  AI Fashion Assistant - Dev Server Startup
echo ============================================================

echo.
echo [1/4] Starting Docker containers (PostgreSQL + Redis)...
docker compose up postgres redis -d
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker failed to start. Make sure Docker Desktop is running.
    echo Open Docker Desktop from Start Menu, wait for it to fully load, then re-run this script.
    pause
    exit /b 1
)

echo.
echo [2/4] Waiting 5s for PostgreSQL to be ready...
timeout /t 5 /nobreak >nul

echo.
echo [3/4] Running Alembic migrations...
C:\venv\Scripts\alembic upgrade head
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Alembic migration failed. Check your DATABASE_URL in .env
    pause
    exit /b 1
)

echo.
echo [4/4] Starting FastAPI server...
echo  API docs: http://localhost:8000/docs
echo  Health:   http://localhost:8000/health
echo.
C:\venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
