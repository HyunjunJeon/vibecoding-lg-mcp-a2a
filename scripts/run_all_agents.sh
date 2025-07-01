#!/bin/bash
# 모든 에이전트 실행 스크립트

echo "=== TTimes Guide Coding - 전체 시스템 시작 ==="

# 환경 변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 포트 설정
export MCP_SERVER_PORT=8090
export PLANNING_AGENT_PORT=8003
export RESEARCH_AGENT_PORT=8001
export REPORT_WRITING_AGENT_PORT=8004
export UNIFIED_AGENT_PORT=8000

# 프로세스 종료 함수
cleanup() {
    echo "\n=== 시스템 종료 중... ==="
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# 시그널 핸들러 등록
trap cleanup SIGINT SIGTERM

# 1. LangConnect 시작 (Docker Compose)
echo "\n1. LangConnect 시작..."
cd langconnect
docker compose up -d
cd ..
sleep 5

# 2. FastMCP 2.x HTTP 서버 시작  
echo "\n2. FastMCP HTTP 서버 시작 (포트 $MCP_SERVER_PORT)..."
uv run python all-search-mcp/run_server.py --port $MCP_SERVER_PORT &
sleep 3

# 3. A2A 서버들 시작
echo "\n3. Planning Agent A2A 서버 시작 (포트 $PLANNING_AGENT_PORT)..."
python agents/a2a_servers/planning_a2a_server.py &
sleep 2

echo "\n4. Research Agent A2A 서버 시작 (포트 $RESEARCH_AGENT_PORT)..."
python agents/a2a_servers/research_a2a_server.py &
sleep 2

echo "\n5. Report Writing Agent A2A 서버 시작 (포트 $REPORT_WRITING_AGENT_PORT)..."
python agents/a2a_servers/report_writing_a2a_server.py &
sleep 2

# 4. UnifiedResearch Agent API 서버 시작
echo "\n6. UnifiedResearch Agent API 서버 시작 (포트 $UNIFIED_AGENT_PORT)..."
cd a2a_client
uvicorn unified_research_agent.api_server:app --host 0.0.0.0 --port $UNIFIED_AGENT_PORT --reload &
cd ..

# 5. Google ADK Web UI 시작
echo "\n7. Google ADK Web UI 시작 (포트 8500)..."
cd a2a_client
adk web . --port 8500 &
cd ..

echo "\n=== 모든 서비스가 시작되었습니다 ==="
echo ""
echo "접속 URL:"
echo "- Google ADK Web UI: http://localhost:8500"
echo "- UnifiedResearch Agent API: http://localhost:$UNIFIED_AGENT_PORT/docs"
echo "- Planning Agent: http://localhost:$PLANNING_AGENT_PORT"
echo "- Research Agent: http://localhost:$RESEARCH_AGENT_PORT"
echo "- Report Writing Agent: http://localhost:$REPORT_WRITING_AGENT_PORT"
echo "- FastMCP HTTP Server: http://localhost:$MCP_SERVER_PORT"
echo "- LangConnect: http://localhost:8080"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."

# 백그라운드 프로세스 대기
wait