# T-Times Guide Coding A2A Implementation Guide

## 목차

1. [개요](#개요)
2. [아키텍처](#아키텍처)
3. [현재 구현 상태](#현재-구현-상태)
4. [API 엔드포인트](#api-엔드포인트)
5. [메시지 형식](#메시지-형식)
6. [에이전트 구현 가이드](#에이전트-구현-가이드)
7. [클라이언트 구현 가이드](#클라이언트-구현-가이드)
8. [테스트 가이드](#테스트-가이드)
9. [개선 사항](#개선-사항)

## 개요

이 프로젝트는 A2A(Agent-to-Agent) 프로토콜을 사용하여 다중 에이전트 시스템을 구현합니다. 세 가지 주요 에이전트가 협력하여 연구 작업을 수행합니다:

- **Planning Agent**: 사용자 요청을 분석하고 실행 계획 수립
- **Research Agent**: 웹 검색과 벡터 DB 검색을 통한 정보 수집
- **Report Writing Agent**: 수집된 정보를 바탕으로 전문적인 보고서 작성

### 프로토콜 버전

- A2A SDK: v0.2.9+
- JSON-RPC: 2.0
- 통신 방식: HTTP POST, Server-Sent Events (SSE)

## 아키텍처

### 시스템 구성도

```
┌─────────────────┐
│   Client/User   │
└────────┬────────┘
         │
         v
┌─────────────────────────┐
│  Simple Orchestrator    │  (FastAPI)
│  - A2A 클라이언트       │
│  - 에이전트 조정        │
└────────┬────────────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    │         │         │          │
    v         v         v          v
┌─────────┐ ┌─────────┐ ┌──────────────┐
│Planning │ │Research │ │Report Writing│
│ Agent   │ │ Agent   │ │   Agent      │
│(Port:   │ │(Port:   │ │(Port: 8004)  │
│ 8003)   │ │ 8001)   │ └──────────────┘
└─────────┘ └─────────┘
```

### 통신 흐름

1. **클라이언트 → Orchestrator**: REST API 요청
2. **Orchestrator → Agents**: A2A JSON-RPC 요청
3. **Agents → Orchestrator**: A2A JSON-RPC 응답
4. **Orchestrator → 클라이언트**: 통합된 결과 반환

## 현재 구현 상태

### 구현된 기능

#### 1. Simple Orchestrator (`a2a_client/simple_orchestrator.py`)

- ✅ A2A 프로토콜을 사용한 에이전트 호출
- ✅ 3단계 연구 프로세스 조정
- ✅ JSON-RPC 2.0 메시지 형식
- ✅ 비동기 처리 (aiohttp)
- ✅ 에러 처리 및 타임아웃 관리

#### 2. Planning Agent (`agents/a2a_servers/planning_a2a_server_v3.py`)

- ✅ Currency Agent 패턴 구현
- ✅ LangGraph 통합
- ✅ 스트리밍 응답 지원
- ✅ Task 상태 관리
- ⚠️ `final` 플래그 누락

#### 3. Research Agent (`agents/a2a_servers/research_a2a_server.py`)

- ✅ 웹 검색 및 벡터 DB 검색 통합
- ✅ 스트리밍 및 비스트리밍 모드 지원
- ✅ MCP 클라이언트 통합 (선택적)
- ✅ 상세한 진행 상황 업데이트

#### 4. Report Writing Agent (`agents/a2a_servers/report_writing_a2a_server.py`)

- ✅ 전문적인 보고서 생성
- ✅ 다양한 출력 형식 지원
- ✅ 컨텍스트 기반 작성

### 미구현/개선 필요 기능

1. **인증 및 보안**
   - ❌ Bearer 토큰 인증
   - ❌ API 키 관리
   - ❌ HTTPS 지원

2. **고급 기능**
   - ❌ Push Notifications (웹훅)
   - ❌ 파일 업로드/다운로드
   - ❌ 멀티모달 지원 (이미지, 오디오)

3. **프로토콜 준수**
   - ⚠️ 일관되지 않은 AgentExecutor 구현
   - ⚠️ 불완전한 Task 상태 전이
   - ⚠️ A2A 특정 에러 코드 미사용

## API 엔드포인트

### Orchestrator 엔드포인트

#### POST /research

연구 작업 수행

**요청:**
```json
{
  "topic": "LangGraph 멀티 에이전트 시스템",
  "depth": "comprehensive",
  "output_format": "markdown"
}
```

**응답:**
```json
{
  "topic": "LangGraph 멀티 에이전트 시스템",
  "stages": {
    "planning": {...},
    "research": {...},
    "report": {...}
  },
  "final_report": {...},
  "timestamp": "2024-01-01T00:00:00"
}
```

#### GET /agents/status

모든 에이전트 상태 확인

### A2A Agent 엔드포인트

모든 에이전트는 표준 A2A 엔드포인트를 제공:

- `POST /` - JSON-RPC 요청 처리
- `GET /` - Agent Card 반환
- `GET /health` - 헬스체크

## 메시지 형식

### A2A JSON-RPC 요청

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "unique-message-id",
      "role": "user",
      "parts": [
        {
          "text": "요청 내용"
        },
        {
          "data": {
            "context": "추가 컨텍스트"
          }
        }
      ]
    }
  }
}
```

### A2A JSON-RPC 응답

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "task": {
      "id": "task-id",
      "contextId": "context-id",
      "status": {
        "state": "completed"
      }
    },
    "message": {
      "role": "agent",
      "parts": [
        {
          "text": "응답 텍스트"
        },
        {
          "data": {
            "results": [...]
          }
        }
      ]
    }
  }
}
```

## 에이전트 구현 가이드

### 1. 기본 구조

```python
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

class MyAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        # 에이전트 로직 구현
        pass
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        # 취소 로직 구현
        pass
```

### 2. Agent Card 정의

```python
agent_card = AgentCard(
    name='My Agent',
    description='에이전트 설명',
    url='http://localhost:8000/',
    version='1.0.0',
    capabilities=AgentCapabilities(
        streaming=True,
        pushNotifications=False
    ),
    skills=[
        AgentSkill(
            id='skill_id',
            name='스킬 이름',
            description='스킬 설명',
            tags=['tag1', 'tag2'],
            examples=['예제 1', '예제 2']
        )
    ]
)
```

### 3. LangGraph 통합

```python
from langgraph.graph import StateGraph, END

class MyAgent:
    def __init__(self, model, checkpointer):
        self.model = model
        self.checkpointer = checkpointer
    
    def build_graph(self):
        workflow = StateGraph(MyState)
        # 그래프 구성
        return workflow.compile(checkpointer=self.checkpointer)
```

## 클라이언트 구현 가이드

### 1. 단순 호출

```python
import aiohttp
import json

async def call_agent(agent_url, message):
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"text": message}]
            }
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(agent_url, json=payload) as resp:
            return await resp.json()
```

### 2. 스트리밍 처리

```python
async def stream_agent(agent_url, message):
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/stream",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"text": message}]
            }
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(agent_url, json=payload) as resp:
            async for line in resp.content:
                if line.startswith(b'data: '):
                    data = json.loads(line[6:])
                    yield data
```

## 테스트 가이드

### 1. 개별 에이전트 테스트

```bash
# 에이전트 서버 시작
python agents/a2a_servers/planning_a2a_server_v3.py

# 테스트 실행
python test_a2a_simple.py
```

### 2. 통합 테스트

```bash
# 모든 에이전트 시작 (Docker Compose 사용)
docker-compose up

# Orchestrator를 통한 테스트
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI trends", "depth": "comprehensive"}'
```

### 3. 성능 테스트

```python
import asyncio
import time

async def performance_test():
    start = time.time()
    tasks = []
    
    for i in range(10):
        task = call_agent(agent_url, f"Test query {i}")
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    print(f"Completed {len(results)} requests in {elapsed:.2f}s")
    print(f"Average: {elapsed/len(results):.2f}s per request")
```

## 개선 사항

### 1. 즉시 적용 가능한 개선

#### 1.1 스트림 종료 표시 추가

```python
# planning_a2a_server_v3.py 수정
yield {
    'is_task_complete': True,
    'require_user_input': False,
    'content': final_state.get("execution_plan", "계획 수립이 완료되었습니다."),
    'data': result,
    'final': True  # 추가
}
```

#### 1.2 Task 상태 전이 개선

```python
# 초기화 시
await task_updater.submit()  # submitted 상태 추가
await task_updater.start_work()  # working 상태로 전이
```

#### 1.3 에러 코드 표준화

```python
from a2a.server.errors import (
    InvalidParamsError,
    InternalError,
    TaskNotFoundError,
    MethodNotFoundError
)

# 적절한 에러 사용
if not message_text:
    raise ServerError(InvalidParamsError("Message text is required"))
```

### 2. 중장기 개선 사항

#### 2.1 인증 시스템 구현

- Bearer 토큰 기반 인증
- API 키 관리 시스템
- Rate limiting

#### 2.2 모니터링 및 로깅

- 구조화된 로깅 (JSON 형식)
- 메트릭 수집 (Prometheus)
- 분산 추적 (OpenTelemetry)

#### 2.3 확장성 개선

- Redis 기반 Task Store
- 메시지 큐 통합 (RabbitMQ/Kafka)
- 수평적 확장 지원

#### 2.4 프로토콜 완전 준수

- BaseAgentExecutor 패턴으로 통일
- Push Notifications 구현
- 파일 처리 지원

### 3. 코드 품질 개선

#### 3.1 타입 안정성

```python
from typing import Protocol

class AgentProtocol(Protocol):
    async def process(self, query: str) -> Dict[str, Any]:
        ...
```

#### 3.2 테스트 커버리지

- 단위 테스트 작성
- 통합 테스트 자동화
- 엔드-투-엔드 테스트

#### 3.3 문서화

- API 문서 자동 생성 (OpenAPI)
- 코드 주석 개선
- 사용 예제 확충

## 참고 자료

- [A2A Protocol Specification v0.2.2](https://github.com/a2a-lab/protocol)
- [A2A SDK Documentation](https://pypi.org/project/a2a-sdk/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [프로젝트 GitHub 저장소](https://github.com/your-repo) 