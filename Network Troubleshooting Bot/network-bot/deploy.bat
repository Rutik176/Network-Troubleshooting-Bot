@echo off
REM Network Troubleshooting Bot - Windows Deployment Script

echo 🚀 Starting Network Troubleshooting Bot Deployment
echo =================================================

REM Check for Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

REM Check for Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    echo Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose found

REM Create necessary directories
echo 📁 Creating directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "config" mkdir config

REM Copy sample configuration if it doesn't exist
if not exist "config\config.yaml" (
    echo 📝 Creating sample configuration...
    if exist "config\config.sample.yaml" (
        copy "config\config.sample.yaml" "config\config.yaml"
    )
)

REM Build and start services
echo 🏗️ Building and starting services...
docker-compose up -d --build

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 15 /nobreak >nul

REM Check service health
echo 🔍 Checking service health...
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️ API Server might still be starting...
) else (
    echo ✅ API Server is running at http://localhost:8000
)

curl -f http://localhost:8501 >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Dashboard might still be starting...
) else (
    echo ✅ Dashboard is running at http://localhost:8501
)

echo.
echo 🎉 Deployment complete!
echo =================================
echo 📊 Dashboard: http://localhost:8501
echo 🔗 API Docs: http://localhost:8000/docs
echo ❤️ Health Check: http://localhost:8000/health
echo.
echo 📋 Useful commands:
echo   docker-compose logs -f                 # View logs
echo   docker-compose down                   # Stop services
echo   docker-compose restart               # Restart services
echo   docker-compose ps                    # Check status
echo.
echo Press any key to open the dashboard...
pause >nul
start http://localhost:8501