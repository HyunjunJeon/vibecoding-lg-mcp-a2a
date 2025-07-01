#!/bin/bash
# Docker Compose로 전체 시스템 실행 스크립트

echo "=== TTimes Guide Coding Docker 실행 ==="
echo ""

# 스크립트 디렉토리에서 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 환경 변수 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사합니다..."
    cp .env.example .env
    echo "✅ .env 파일이 생성되었습니다. API 키를 설정해주세요."
    echo ""
fi

# 실행 옵션 선택
echo "실행 모드를 선택하세요:"
echo "1. 전체 시스템 시작 (build + up)"
echo "2. 백그라운드로 시작 (build + up -d)"
echo "3. 로그 확인 (logs -f)"
echo "4. 시스템 중지 (down)"
echo "5. 시스템 완전 삭제 (down -v)"
echo "6. 개별 서비스 재시작"
echo "7. 헬스체크 상태 확인"
echo ""
read -p "선택 (1-7): " choice

case $choice in
    1)
        echo "\n전체 시스템을 빌드하고 시작합니다..."
        docker compose build
        docker compose up
        ;;
    2)
        echo "\n전체 시스템을 백그라운드로 시작합니다..."
        docker compose build
        docker compose up -d
        echo "\n시스템이 시작되었습니다."
        echo ""
        echo "접속 URL:"
        echo "- UnifiedResearch Agent API: http://localhost:8000"
        echo "- Planning Agent: http://localhost:8003"
        echo "- Research Agent: http://localhost:8001"
        echo "- Report Writing Agent: http://localhost:8004"
        echo "- MCP Server: http://localhost:8090"
        echo "- LangConnect: http://localhost:8080"
        echo ""
        echo "로그 확인: docker compose logs -f [service_name]"
        ;;
    3)
        echo "\n서비스 이름 (전체는 Enter):"
        echo "가능한 서비스: postgres, redis, langconnect, mcp-server,"
        echo "              planning-agent, research-agent, report-writing-agent,"
        echo "              unified-research-agent"
        read -p "> " service
        
        if [ -z "$service" ]; then
            docker compose logs -f
        else
            docker compose logs -f $service
        fi
        ;;
    4)
        echo "\n시스템을 중지합니다..."
        docker compose down
        ;;
    5)
        echo "\n⚠️  경고: 모든 데이터가 삭제됩니다!"
        read -p "정말로 삭제하시겠습니까? (y/N): " confirm
        if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
            docker compose down -v
            echo "시스템과 데이터가 완전히 삭제되었습니다."
        else
            echo "취소되었습니다."
        fi
        ;;
    6)
        echo "\n재시작할 서비스를 선택하세요:"
        echo "1. postgres"
        echo "2. redis"
        echo "3. langconnect"
        echo "4. mcp-server"
        echo "5. planning-agent"
        echo "6. research-agent"
        echo "7. report-writing-agent"
        echo "8. unified-research-agent"
        read -p "> " service_num
        
        case $service_num in
            1) service="postgres" ;;
            2) service="redis" ;;
            3) service="langconnect" ;;
            4) service="mcp-server" ;;
            5) service="planning-agent" ;;
            6) service="research-agent" ;;
            7) service="report-writing-agent" ;;
            8) service="unified-research-agent" ;;
            *) echo "잘못된 선택"; exit 1 ;;
        esac
        
        echo "\n$service 서비스를 재시작합니다..."
        docker compose restart $service
        ;;
    7)
        echo "\n=== 헬스체크 상태 확인 ==="
        echo ""
        
        # 각 서비스의 헬스 상태 확인
        services=("postgres" "redis" "langconnect" "mcp-server" "planning-agent" "research-agent" "report-writing-agent" "unified-research-agent")
        
        for service in "${services[@]}"; do
            status=$(docker compose ps $service --format json 2>/dev/null | jq -r '.[0].State' 2>/dev/null)
            health=$(docker compose ps $service --format json 2>/dev/null | jq -r '.[0].Health' 2>/dev/null)
            
            if [ -z "$status" ]; then
                echo "❌ $service: 실행되지 않음"
            elif [ "$health" == "healthy" ]; then
                echo "✅ $service: 정상 (healthy)"
            elif [ "$health" == "unhealthy" ]; then
                echo "❌ $service: 비정상 (unhealthy)"
            elif [ "$status" == "running" ]; then
                echo "⚠️  $service: 실행 중 (헬스체크 없음)"
            else
                echo "❓ $service: $status"
            fi
        done
        ;;
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac