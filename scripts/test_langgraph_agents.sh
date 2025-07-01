#!/bin/bash
# LangGraph 에이전트 개별 테스트 스크립트

echo "=== LangGraph 에이전트 테스트 ==="
echo ""
echo "테스트할 에이전트를 선택하세요:"
echo "1. Planning Agent"
echo "2. Research Agent"  
echo "3. Report Writing Agent"
echo "4. 모든 에이전트 (LangGraph Studio)"
echo ""
read -p "선택 (1-4): " choice

# 환경 변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

case $choice in
    1)
        echo "\nPlanning Agent 테스트 시작..."
        cd agents
        langgraph dev --graph planning
        ;;
    2)
        echo "\nResearch Agent 테스트 시작..."
        echo "MCP 서버를 먼저 시작합니다..."
        python ../all-search-mcp/run_server.py --transport http &
        MCP_PID=$!
        sleep 3
        cd agents
        langgraph dev --graph research
        kill $MCP_PID 2>/dev/null
        ;;
    3)
        echo "\nReport Writing Agent 테스트 시작..."
        cd agents
        langgraph dev --graph report_writing
        ;;
    4)
        echo "\nLangGraph Studio 시작..."
        langgraph dev
        ;;
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac