# Scripts 디렉토리 가이드

이 디렉토리는 TTimes Guide Coding 프로젝트의 실행 및 테스트 스크립트를 포함합니다.

## 🚀 실행 스크립트

### 1. `dev_langgraph.sh`

LangGraph 개발 환경을 시작합니다.

```bash
./scripts/dev_langgraph.sh
```

- LangGraph Studio 실행 (http://localhost:8123)
- 선택적으로 LangConnect와 MCP 서버 시작
- 개별 에이전트 테스트 및 디버깅 가능

### 2. `run_google_adk.sh`

Google ADK 기반 UnifiedResearch Agent를 실행합니다.

```bash
./scripts/run_google_adk.sh
```

실행 모드:
1. **CLI 모드**: 대화형 인터페이스
2. **Web UI 모드**: ADK Web Interface
3. **API 서버 모드**: REST API (http://localhost:8000)

### 3. `start_a2a_servers.sh`

모든 A2A 서버를 시작합니다.

```bash
./scripts/start_a2a_servers.sh
```

시작되는 서버:
- Planning Agent (포트 8003)
- Research Agent (포트 8001)
- Report Writing Agent (포트 8004)
- MCP Server (포트 8090)

### 4. `run_all_agents.sh`

전체 시스템을 시작합니다 (LangConnect 포함).

```bash
./scripts/run_all_agents.sh
```

### 5. `quick_test.sh`

빠른 테스트를 위한 스크립트입니다.

```bash
./scripts/quick_test.sh
```

테스트 옵션:
1. MCP 서버 테스트
2. LangGraph 에이전트 단일 테스트
3. A2A 서버 헬스체크
4. 전체 시스템 API 테스트

### 6. `docker_run.sh` 🐳

Docker Compose로 전체 시스템을 관리합니다.

```bash
./scripts/docker_run.sh
```

실행 옵션:
1. **전체 시스템 시작**: 모든 서비스 빌드 및 실행
2. **백그라운드 실행**: 데몬 모드로 실행
3. **로그 확인**: 실시간 로그 모니터링
4. **시스템 중지**: 모든 컨테이너 중지
5. **완전 삭제**: 컨테이너 및 볼륨 삭제
6. **개별 서비스 재시작**: 특정 서비스만 재시작
7. **헬스체크 상태**: 모든 서비스 상태 확인

## 📝 개발 워크플로우

### LangGraph 에이전트 개발

1. `./scripts/dev_langgraph.sh` 실행
2. LangGraph Studio에서 에이전트 테스트
3. 필요시 코드 수정 후 재시작

### A2A 통합 테스트

1. `./scripts/start_a2a_servers.sh`로 A2A 서버 시작
2. 다른 터미널에서 `./scripts/run_google_adk.sh` 실행
3. CLI 또는 Web UI로 테스트

### 전체 시스템 테스트

1. `./scripts/run_all_agents.sh`로 전체 시스템 시작
2. `./scripts/quick_test.sh`로 빠른 테스트 수행

### Docker 환경 실행 🐳

1. `./scripts/docker_run.sh` 실행
2. 옵션 2 선택 (백그라운드 실행)
3. 모든 서비스가 healthy 상태가 될 때까지 대기
4. API 테스트: `curl http://localhost:8000/health`

## 🛠️ 기타 스크립트

### `dev_run_langgraph_platform.sh`

LangGraph Platform 개발 서버를 실행합니다.

### `test_langgraph_agents.sh`

개별 LangGraph 에이전트를 테스트합니다.

## 📌 참고사항

- 모든 스크립트는 프로젝트 루트에서 실행해야 합니다
- `.env` 파일에 필요한 환경 변수가 설정되어 있어야 합니다
- Docker가 실행 중이어야 합니다 (LangConnect용)
- Python 3.13+ 및 uv가 설치되어 있어야 합니다