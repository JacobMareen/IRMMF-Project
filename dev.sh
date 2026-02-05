#!/bin/bash

# IRMMF Development Startup Script
# Usage: ./dev.sh

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   🚀 IRMMF Development Environment      ${NC}"
echo -e "${BLUE}=========================================${NC}"

# 1. Cleanup old processes
echo -e "\n${BLUE}[1/3] Cleaning up ports 8000 and 5173...${NC}"
PID_BACKEND=$(lsof -ti:8000)
if [ ! -z "$PID_BACKEND" ]; then
    echo "   Killing old Backend (PID $PID_BACKEND)..."
    kill -9 $PID_BACKEND
fi

PID_FRONTEND=$(lsof -ti:5173)
if [ ! -z "$PID_FRONTEND" ]; then
    echo "   Killing old Frontend (PID $PID_FRONTEND)..."
    kill -9 $PID_FRONTEND
fi

# 2. Start Backend
echo -e "\n${BLUE}[2/3] Starting Backend (Uvicorn)...${NC}"
source .venv/bin/activate
# Run in background, log to backend.log
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "   ${GREEN}✅ Backend started (PID $BACKEND_PID)${NC}"

# 3. Start Frontend
echo -e "\n${BLUE}[3/3] Starting Frontend (Vite)...${NC}"
cd frontend
# Run in background, log to frontend.log
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo -e "   ${GREEN}✅ Frontend started (PID $FRONTEND_PID)${NC}"

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}   🎉 ENVIRONMENT IS READY!              ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "   🌍 UI:  http://localhost:5173"
echo -e "   🔌 API: http://localhost:8000"
echo -e "   📄 Logs are being written to backend.log and frontend.log"
echo -e "\n   👉 Press ${RED}Ctrl+C${NC} to stop everything."

# Trap SIGINT (Ctrl+C) to kill children
cleanup() {
    echo -e "\n\n${RED}🛑 Stopping services...${NC}"
    kill $BACKEND_PID
    kill $FRONTEND_PID
    echo "   ✅ Cleanup complete. Bye!"
    exit
}
trap cleanup SIGINT

# Keep script running to maintain the trap
wait
