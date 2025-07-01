#!/bin/bash
# Google ADK 실행 스크립트

echo "=== Google ADK UnifiedResearch Agent 실행 ==="
echo ""

# 환경 변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Google API Key 확인
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "경고: GOOGLE_API_KEY가 설정되지 않았습니다."
    echo ".env 파일에 GOOGLE_API_KEY를 설정해주세요."
    echo ""
fi

# 실행 모드 선택
echo "실행 모드를 선택하세요:"
echo "1. CLI 모드 (대화형 인터페이스)"
echo "2. Web UI 모드 (ADK Web Interface)"
echo "3. API 서버 모드 (REST API)"
echo ""
read -p "선택 (1-3): " mode

case $mode in
    1)
        echo "\nCLI 모드로 시작합니다..."
        echo "종료하려면 'quit' 또는 'q'를 입력하세요."
        echo ""
        cd a2a_client
        python unified_research_agent.py
        ;;
    2)
        echo "\nADK Web UI를 시작합니다..."
        echo "브라우저가 자동으로 열립니다."
        echo ""
        # ADK Web UI 실행
        adk web a2a_client/
        ;;
    3)
        echo "\nAPI 서버 모드로 시작합니다..."
        echo "API 엔드포인트: http://localhost:8000"
        echo ""
        cd a2a_client
        uvicorn unified_research_agent:app --host 0.0.0.0 --port 8000 --reload
        ;;
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac