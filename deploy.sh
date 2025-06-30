#!/bin/bash

# BarSan Backend Deployment Script
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
DOMAIN="myhostserver.sytes.net"

echo "🚀 Deploying BarSan Backend to $ENVIRONMENT environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p uploads logs ssl nginx/conf.d

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Copying from .env.production..."
    cp .env.production .env
    print_warning "Please update the .env file with your actual values before continuing."
    read -p "Press Enter to continue after updating .env file..."
fi

# Pull latest images
print_status "Pulling latest Docker images..."
docker-compose pull

# Build the application
print_status "Building the application..."
docker-compose build --no-cache

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down

# Start the services
print_status "Starting services..."
docker-compose up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U barsan_user -d barsan_db > /dev/null 2>&1; then
    print_status "✅ PostgreSQL is healthy"
else
    print_error "❌ PostgreSQL is not healthy"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_status "✅ Redis is healthy"
else
    print_error "❌ Redis is not healthy"
fi

# Check Backend
if curl -f http://localhost:3001/health > /dev/null 2>&1; then
    print_status "✅ Backend is healthy"
else
    print_error "❌ Backend is not healthy"
fi

# Run database migrations
print_status "Running database migrations..."
docker-compose exec backend bun run db:generate
docker-compose exec backend bun run db:push

# Seed database (only if needed)
read -p "Do you want to seed the database? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Seeding database..."
    docker-compose exec backend bun run db:seed
fi

# Show running services
print_status "Deployment completed! Services status:"
docker-compose ps

print_status "🎉 BarSan Backend is now running!"
echo ""
echo "📋 Service URLs:"
echo "   🌐 API: https://$DOMAIN:3001"
echo "   📚 API Docs: https://$DOMAIN:3001/swagger"
echo "   🗄️ PgAdmin: https://pgadmin.$DOMAIN (if enabled)"
echo "   ❤️ Health Check: https://$DOMAIN:3001/health"
echo ""
echo "📊 Admin Accounts:"
echo "   👤 Username: superadmin"
echo "   🔑 Password: BarSan2024Admin!"
echo ""
echo "🔧 Useful Commands:"
echo "   📋 View logs: docker-compose logs -f"
echo "   🔄 Restart: docker-compose restart"
echo "   🛑 Stop: docker-compose down"
echo "   🧹 Cleanup: docker-compose down -v"
