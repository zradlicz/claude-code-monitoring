#!/bin/bash
set -e

echo "========================================="
echo "Claude Code Monitoring Setup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}Docker and Docker Compose are installed.${NC}"
echo ""

# Create data directory if it doesn't exist
mkdir -p data

# Build and start services
echo "Building and starting services..."
docker-compose up -d --build

echo ""
echo -e "${GREEN}Services started successfully!${NC}"
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Service Status:"
docker-compose ps

echo ""
echo "========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================="
echo ""
echo "Access the services:"
echo "  - Grafana Dashboard: http://localhost:3000"
echo "    (Default credentials: admin/admin)"
echo ""
echo "  - SQLite Bridge Stats: http://localhost:5000/stats"
echo ""
echo "  - OpenTelemetry Collector: grpc://localhost:4317"
echo ""
echo "To configure Claude Code to send telemetry:"
echo "  1. Set up your environment variables (see configure-claude.sh)"
echo "  2. Run Claude Code normally"
echo "  3. Open Grafana to view metrics and prompts"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
