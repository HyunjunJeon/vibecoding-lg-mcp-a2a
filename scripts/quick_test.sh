#!/bin/bash
# 빠른 테스트를 위한 스크립트

echo "=== TTimes Guide Coding 빠른 테스트 ==="
echo ""

# 환경 변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 테스트 모드 선택
echo "테스트할 항목을 선택하세요:"
echo "1. MCP 서버 테스트"
echo "2. LangGraph 에이전트 단일 테스트"
echo "3. A2A 서버 헬스체크"
echo "4. 전체 시스템 테스트 (API 호출)"
echo ""
read -p "선택 (1-4): " test_mode

case $test_mode in
    1)
        echo "\n=== MCP 서버 테스트 ==="
        # MCP 서버 시작
        python all-search-mcp/run_server.py --transport http --port 8090 &
        MCP_PID=$!
        sleep 3
        
        # 테스트
        echo "\n웹 검색 테스트:"
        curl -X POST http://localhost:8090/mcp/rpc \
          -H "Content-Type: application/json" \
          -d '{"jsonrpc":"2.0","method":"search_web","params":{"query":"LangGraph"},"id":1}'
        
        echo "\n\n상태 확인:"
        curl http://localhost:8090/health
        
        # 정리
        kill $MCP_PID 2>/dev/null
        ;;
        
    2)
        echo "\n=== LangGraph 에이전트 테스트 ==="
        echo "테스트할 에이전트:"
        echo "1. Planning Agent"
        echo "2. Research Agent"
        echo "3. Report Writing Agent"
        read -p "선택: " agent
        
        case $agent in
            1) graph="planning" ;;
            2) graph="research" ;;
            3) graph="report_writing" ;;
            *) echo "잘못된 선택"; exit 1 ;;
        esac
        
        langgraph test --graph $graph
        ;;
        
    3)
        echo "\n=== A2A 서버 헬스체크 ==="
        ports=(8003 8001 8004)
        names=("Planning" "Research" "Report Writing")
        
        for i in ${!ports[@]}; do
            echo "\n${names[$i]} Agent (포트 ${ports[$i]}):"
            curl -s http://localhost:${ports[$i]}/health | jq '.' 2>/dev/null || echo "서버가 실행되지 않음"
        done
        ;;
        
    4)
        echo "\n=== 전체 시스템 테스트 ==="
        echo "테스트 주제를 입력하세요:"
        read -p "> " topic
        
        echo "\n연구 요청 전송 중..."
        curl -X POST http://localhost:8000/research \
          -H "Content-Type: application/json" \
          -d "{\"topic\": \"$topic\", \"depth\": \"basic\"}" \
          | jq '.'
        ;;
        
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac

echo "\n테스트 완료!"