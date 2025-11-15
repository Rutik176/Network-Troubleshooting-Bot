#!/bin/bash
# Network Troubleshooting Bot - Deployment Script

echo "🚀 Starting Network Troubleshooting Bot Deployment"
echo "================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Docker
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check for Docker Compose
if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs config

# Copy sample configuration if it doesn't exist
if [ ! -f "config/config.yaml" ]; then
    echo "📝 Creating sample configuration..."
    cp config/config.sample.yaml config/config.yaml 2>/dev/null || echo "Note: No sample config found"
fi

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ API Server is running at http://localhost:8000"
else
    echo "⚠️ API Server might still be starting..."
fi

if curl -f http://localhost:8501 >/dev/null 2>&1; then
    echo "✅ Dashboard is running at http://localhost:8501"
else
    echo "⚠️ Dashboard might still be starting..."
fi

echo ""
echo "🎉 Deployment complete!"
echo "================================="
echo "📊 Dashboard: http://localhost:8501"
echo "🔗 API Docs: http://localhost:8000/docs"
echo "❤️ Health Check: http://localhost:8000/health"
echo ""
echo "📋 Useful commands:"
echo "  docker-compose logs -f                 # View logs"
echo "  docker-compose down                   # Stop services" 
echo "  docker-compose restart               # Restart services"
echo "  docker-compose ps                    # Check status"