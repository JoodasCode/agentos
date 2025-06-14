#!/bin/bash

# AgentOS Service Startup Script
# This script starts all services in the correct order for Trigger.dev v3

echo "🚀 Starting AgentOS Services"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}Port $1 is already in use${NC}"
        return 1
    else
        return 0
    fi
}

# Function to start a service in background
start_service() {
    local name=$1
    local command=$2
    local port=$3
    
    echo -e "${YELLOW}Starting $name...${NC}"
    
    if check_port $port; then
        eval "$command" &
        local pid=$!
        echo "$pid" > "/tmp/agentos_${name,,}_pid"
        echo -e "${GREEN}✅ $name started (PID: $pid, Port: $port)${NC}"
    else
        echo -e "${RED}❌ Cannot start $name - port $port is in use${NC}"
    fi
}

# Stop any existing services
echo "🧹 Cleaning up existing services..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "trigger.dev" 2>/dev/null || true
pkill -f "ts-node src/api.ts" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

sleep 2

echo ""
echo "🔧 Starting services..."

# 1. Start Trigger.dev API Bridge (Port 3001)
cd trigger-jobs
start_service "Trigger.dev API Bridge" "npm run api" 3001

# 2. Start Trigger.dev Dev Server (for task development)
start_service "Trigger.dev Dev Server" "npm run dev" 3000

# 3. Start FastAPI Backend (Port 8000)
cd ../backend
start_service "FastAPI Backend" "python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" 8000

# 4. Start Next.js Frontend (Port 3002, avoiding conflict with Trigger.dev)
cd ../frontend
start_service "Next.js Frontend" "npm run dev -- --port 3002" 3002

cd ..

echo ""
echo "🎉 All services started!"
echo "========================"
echo ""
echo "📋 Service URLs:"
echo "  • Frontend:           http://localhost:3002"
echo "  • Backend API:        http://localhost:8000"
echo "  • Backend Docs:       http://localhost:8000/docs"
echo "  • Trigger.dev Bridge: http://localhost:3001"
echo "  • Trigger.dev Dev:    http://localhost:3000"
echo ""
echo "🧪 Test Commands:"
echo "  • Test integrations:  python3 test_integrations.py"
echo "  • Test automation:    curl http://localhost:3001/health"
echo "  • Backend health:     curl http://localhost:8000/api/health/status"
echo ""
echo "🛑 To stop all services:"
echo "  ./stop_services.sh"
echo ""
echo "📝 Logs are available in the terminal tabs where each service is running." 