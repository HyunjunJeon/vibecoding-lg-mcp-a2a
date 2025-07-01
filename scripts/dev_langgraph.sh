#!/bin/bash
# LangGraph 개발 환경 실행 스크립트

echo "=== LangGraph 개발 환경 시작 ==="
echo ""

# 환경 변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# LangConnect 실행 여부 확인
echo "LangConnect(벡터 DB)를 시작하시겠습니까? (y/n)"
read -p "> " start_langconnect

if [[ "$start_langconnect" == "y" || "$start_langconnect" == "Y" ]]; then
    echo "\nLangConnect 시작 중..."
    cd langconnect
    make up
    cd ..
    echo "LangConnect가 시작되었습니다. (http://localhost:8080)"
    sleep 5
fi

# MCP 서버 실행 여부 확인
echo "\nMCP 서버를 시작하시겠습니까? (Research Agent 테스트에 필요) (y/n)"
read -p "> " start_mcp

if [[ "$start_mcp" == "y" || "$start_mcp" == "Y" ]]; then
    echo "\nMCP 서버 시작 중..."
    python all-search-mcp/run_server.py --transport http --port 8090 &
    MCP_PID=$!
    echo "MCP 서버가 시작되었습니다. (http://localhost:8090/mcp)"
    sleep 3
fi

# LangGraph Studio 시작
echo "\nLangGraph Studio를 시작합니다..."
echo "사용 가능한 그래프:"
echo "- planning: 계획 수립 에이전트"
echo "- research: 자료조사 에이전트"
echo "- report_writing: 보고서 작성 에이전트"
echo ""

uv run langgraph dev

# 정리 작업
if [[ ! -z "$MCP_PID" ]]; then
    echo "\nMCP 서버 종료 중..."
    kill $MCP_PID 2>/dev/null
fi

echo "\nLangGraph 개발 환경이 종료되었습니다."