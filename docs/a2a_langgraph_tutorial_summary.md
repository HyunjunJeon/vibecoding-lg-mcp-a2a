# A2A 프로토콜과 LangGraph 연동 가이드 요약

## 사용자 요청

사용자는 A2A(Agent-to-Agent) 프로토콜 튜토리얼 문서를 모두 읽고, LangGraph와 A2A를 연동할 때의 주의사항을 정리해달라고 요청했습니다. 특히 버전에 주의하면서 작성하고, 하위 문서들까지 꼼꼼하게 읽어달라고 강조했습니다.

## 조사된 주요 내용

### 1. A2A 프로토콜 개요

- **버전**: 현재 사양 버전은 0.2.2
- **목적**: 서로 다른 프레임워크나 벤더로 만들어진 독립적인 AI 에이전트 시스템 간의 통신과 상호 운용성을 위한 개방형 표준
- **핵심 원칙**: 
  - 단순성 (HTTP, JSON-RPC 2.0, SSE 사용)
  - 엔터프라이즈 준비 (인증, 권한, 보안 지원)
  - 비동기 우선 (장시간 실행 작업 지원)
  - 모달리티 무관 (텍스트, 파일, 구조화된 데이터 지원)
  - 불투명 실행 (내부 상태 공유 없이 협업)

### 2. 핵심 구성 요소

- **Agent Card**: 에이전트의 메타데이터 (이름, 버전, 기능, 스킬, 엔드포인트 URL, 인증 요구사항)
- **Task**: A2A의 기본 작업 단위 (고유 ID, 상태 라이프사이클 관리)
- **Message**: 클라이언트와 에이전트 간의 통신 단위 (role: "user" 또는 "agent")
- **Part**: 메시지 내의 콘텐츠 단위 (TextPart, FilePart, DataPart)
- **Streaming (SSE)**: Server-Sent Events를 통한 실시간 업데이트
- **Push Notifications**: 웹훅을 통한 비동기 작업 업데이트

### 3. 프로토콜 메서드

- `message/send`: 동기식 메시지 전송
- `message/stream`: SSE를 통한 스트리밍 메시지
- `tasks/get`: 작업 상태 조회
- `tasks/cancel`: 작업 취소
- `tasks/resubscribe`: SSE 스트림 재연결

### 4. LangGraph 연동 예제 분석

**Currency Agent 예제 (enso-labs/a2a-langgraph)**:

- Python 3.13 이상 필요
- UV 패키지 매니저 사용
- LangGraph의 ReAct 에이전트 패턴 사용
- Google Gemini 모델 통합
- 스트리밍 지원 및 멀티턴 대화 구현

**주요 구현 패턴**:
```python
# Agent 생성
self.graph = create_react_agent(
    self.model,
    tools=self.tools,
    checkpointer=memory,
    prompt=self.SYSTEM_INSTRUCTION,
    response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
)

# Task 상태 관리
class ResponseFormat(BaseModel):
    status: Literal['input_required', 'completed', 'error']
    message: str
```

### 5. LangGraph와 A2A 연동 시 주의사항

#### 5.1 버전 호환성

- Python >= 3.12 (일부 예제는 3.13 필요)
- a2a-sdk >= 0.2.5
- langchain-google-genai >= 2.1.4
- langgraph >= 0.4.1

#### 5.2 아키텍처 설계

- `AgentExecutor` 클래스를 통해 LangGraph 에이전트를 A2A 프로토콜에 맞게 래핑
- `on_message_send`와 `on_message_stream` 메서드 구현 필수
- Task 상태 관리 (submitted → working → input-required/completed)

#### 5.3 스트리밍 구현

- SSE를 통한 실시간 업데이트 지원
- `TaskStatusUpdateEvent`와 `TaskArtifactUpdateEvent` 이벤트 처리
- `final: true` 플래그로 스트림 종료 표시

#### 5.4 멀티턴 대화

- `contextId`를 통한 세션 유지
- `TaskState.input_required` 상태로 추가 입력 요청
- LangGraph의 checkpointer를 통한 메모리 관리

#### 5.5 에러 처리

- JSON-RPC 2.0 표준 에러 코드 사용
- A2A 특정 에러 코드 (-32001 ~ -32006)
- 적절한 HTTP 상태 코드 반환

#### 5.6 보안 고려사항

- HTTPS 사용 필수 (프로덕션)
- Bearer 토큰 또는 API 키를 통한 인증
- Agent Card에 민감한 정보 포함 금지

#### 5.7 구현 체크리스트

- Agent Card 정의 (capabilities, skills, authentication)
- AgentExecutor 구현 (BaseAgentExecutor 상속)
- Task 생성 및 상태 업데이트 로직
- 스트리밍 응답 처리 (선택사항)
- 테스트 클라이언트 작성

#### 5.8 일반적인 구현 패턴

```python
# 1. Agent Card 정의
capabilities = AgentCapabilities(streaming=True, pushNotifications=False)
skill = AgentSkill(
    id='skill_id',
    name='Skill Name',
    description='Description',
    tags=['tag1', 'tag2'],
    examples=['example1']
)

# 2. LangGraph 에이전트 생성
agent = create_react_agent(model, tools=tools, checkpointer=memory)

# 3. A2A 프로토콜 응답 변환
def update_task_with_agent_response(task: Task, agent_response: dict):
    if agent_response['require_user_input']:
        task.status.state = TaskState.input_required
    else:
        task.status.state = TaskState.completed
```

이러한 주의사항들을 고려하여 LangGraph 기반 에이전트를 A2A 프로토콜과 성공적으로 통합할 수 있습니다.

---

# A2A와 LangGraph 연동 가이드 및 주의사항

## 1. 버전 요구사항

### Python 버전

- **최소 요구사항**: Python 3.10 이상 (공식 튜토리얼)
- **권장 버전**: Python 3.12 이상 (LangGraph 예제의 pyproject.toml)
- **현재 사용 중**: Python 3.13 (문제없음)

### A2A SDK 버전

- **예제에서 사용**: a2a-sdk 0.2.8
- **현재 프로젝트**: a2a 0.2.9 (큰 차이 없을 것으로 예상)

## 2. LangGraph와 A2A 통합 패턴

### 2.1 핵심 아키텍처

```bash
LangGraph Agent → AgentExecutor → A2A Server
```

### 2.2 Currency Agent 예제 분석

#### Agent 구현 (agent.py)

```python
class CurrencyAgent:
    def __init__(self):
        # LangGraph agent 생성
        self.agent_executor = create_react_agent(
            llm,
            tools,
            messages_modifier=system_instructions,
            checkpointer=MemorySaver(),
        )
    
    async def stream(self, query: str, context_id: str):
        """스트리밍 응답 생성"""
        # 1. 초기 상태 업데이트
        yield {
            'is_task_complete': False,
            'require_user_input': False,
            'content': '환율을 확인하고 있습니다...'
        }
        
        # 2. LangGraph 에이전트 실행
        result = await self.agent_executor.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            config={"configurable": {"thread_id": context_id}}
        )
        
        # 3. 최종 응답
        yield {
            'is_task_complete': True,
            'require_user_input': False,
            'content': result['content']
        }
```

#### AgentExecutor 구현 (agent_executor.py)

```python
class CurrencyAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = CurrencyAgent()
    
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        # 1. 요청 검증
        query, task = self._validate_request(context)
        
        # 2. 태스크 관리
        if not task:
            task = self._new_task(context)
            event_queue.enqueue_event(task)
        
        # 3. TaskUpdater 생성
        task_updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        # 4. 스트리밍 처리
        async for item in self.agent.stream(query, task.contextId):
            if not item['is_task_complete']:
                # 중간 상태 업데이트
                await task_updater.update_status(
                    TaskState.working,
                    message=task_updater.new_agent_message(
                        parts=[Part(root=TextPart(text=item['content']))]
                    )
                )
            else:
                # 최종 응답
                parts = [Part(root=TextPart(text=item['content']))]
                if 'data' in item:
                    parts.append(Part(root=DataPart(data=item['data'])))
                
                await task_updater.update_status(
                    TaskState.completed,
                    message=task_updater.new_agent_message(parts=parts)
                )
```

## 3. "Queue is closed" 오류 원인 분석

### 3.1 가능한 원인들

1. **EventQueue 라이프사이클 문제**
   - EventQueue가 execute 메서드 완료 전에 닫힘
   - 비동기 처리 중 EventQueue 참조 유실

2. **TaskUpdater 사용 문제**
   - TaskUpdater의 내부 큐 관리 문제
   - 태스크 상태 업데이트 순서 문제

3. **스트리밍 구현 문제**
   - async generator에서 EventQueue 접근 시점 문제
   - 스트리밍 완료 후 EventQueue 사용 시도

### 3.2 해결 방안

#### 방안 1: Currency Agent 패턴 정확히 따르기

```python
# 1. stream 메서드에서 직접 EventQueue 사용하지 않기
# 2. TaskUpdater를 통해서만 이벤트 큐 접근
# 3. 태스크 완료 시 명시적으로 상태 업데이트
```

#### 방안 2: 에러 핸들링 강화

```python
try:
    async for item in self.agent.stream(query, context_id):
        # 처리
except Exception as e:
    logger.error(f"Stream error: {e}")
    # 에러 상태로 태스크 업데이트
    await task_updater.update_status(
        TaskState.failed,
        message=task_updater.new_agent_message(
            parts=[Part(root=TextPart(text=f"Error: {str(e)}"))]
        )
    )
```

## 4. 주요 차이점 및 수정 필요사항

### 4.1 우리 구현과 Currency Agent의 차이

1. **Agent 래퍼 클래스**
   - Currency Agent: 별도의 CurrencyAgent 클래스로 LangGraph 래핑
   - 우리 구현: AgentExecutor에서 직접 LangGraph 사용

2. **스트리밍 패턴**
   - Currency Agent: yield로 상태 객체 반환
   - 우리 구현: LangGraph의 astream 직접 사용

3. **에러 처리**
   - Currency Agent: try-except로 전체 스트림 감싸기
   - 우리 구현: 부분적 에러 처리

### 4.2 수정 방향

1. **Agent 래퍼 클래스 생성**

```python
class PlanningAgentWrapper:
    def __init__(self):
        self.agent = PlanningAgent(...)
        self.graph = self.agent.build_graph()
    
    async def stream(self, query: str, context_id: str):
        # Currency Agent 패턴 따르기
```

2. **스트리밍 응답 표준화**

```python
{
    'is_task_complete': bool,
    'require_user_input': bool,
    'content': str,
    'data': dict  # optional
}
```

3. **EventQueue 사용 최소화**
   - TaskUpdater를 통해서만 접근
   - 직접 enqueue_event 호출 피하기

## 5. 디버깅 제안

1. **로깅 강화**

```python
logger.debug(f"EventQueue state before stream: {event_queue}")
logger.debug(f"Task state: {task}")
```

2. **단순화된 테스트**
   - LangGraph 없이 단순 메시지만 반환하는 버전 테스트
   - 점진적으로 복잡도 증가

3. **SDK 버전 확인**
   - a2a-sdk 0.2.8로 다운그레이드 테스트
   - Python 3.12로 테스트 (필요시)

## 6. 결론

"Queue is closed" 오류는 EventQueue의 라이프사이클 관리 문제로 보입니다. Currency Agent 예제의 패턴을 정확히 따라 구현하면 해결될 가능성이 높습니다. 특히:

1. Agent 래퍼 클래스 사용
2. 표준화된 스트리밍 응답 형식
3. TaskUpdater를 통한 일관된 이벤트 큐 접근
4. 완전한 에러 핸들링

이러한 수정사항을 적용하면 A2A와 LangGraph의 안정적인 통합이 가능할 것으로 예상됩니다.

## 7. "Queue is closed" 오류 최종 분석

### 7.1 오류 근본 원인

테스트 결과, 문제의 핵심은:
1. **RequestContext 속성 변경**: `context.task` → `context.current_task`
2. **TaskStatus 임포트 및 사용 방식**: 올바른 TaskStatus 타입 사용 필요
3. **EventQueue 생명주기**: A2A SDK 내부의 비동기 처리 문제

### 7.2 즉시 적용 가능한 수정사항

```python
# 1. RequestContext 속성 수정
task = context.current_task or self._new_task(context)

# 2. TaskStatus 올바른 사용
from a2a.types import TaskState, TaskStatus
# TaskStatus.working 대신 TaskState.working 사용

# 3. 비동기 이벤트 큐 호출
await event_queue.enqueue_event(task)  # enqueue_event도 await 필요
```

### 7.3 SDK 버전 및 Python 버전

- **Python 버전**: 3.13도 문제없으나, 안정성을 위해 3.12 권장
- **A2A SDK**: 0.2.9와 0.2.8 간 주요 차이점은 없을 것으로 예상
- **실제 문제**: SDK 사용 패턴과 API 호출 방식

### 7.4 대안 접근 방법

"Queue is closed" 오류가 지속될 경우:

1. **직접 HTTP/JSON-RPC 구현**
   - A2A SDK 없이 FastAPI로 직접 구현
   - JSON-RPC 2.0 프로토콜 수동 구현

2. **Google ADK 활용**
   - A2A 서버 대신 ADK 기반 에이전트로 구현
   - 더 안정적인 통신 레이어 제공

3. **gRPC 기반 구현**
   - 더 강력한 타입 안전성
   - 스트리밍 지원 내장

### 7.5 프로덕션 권장사항

1. **단계적 마이그레이션**
   - 단순한 echo 서버부터 시작
   - 점진적으로 LangGraph 통합

2. **로깅 및 모니터링**
   - 모든 A2A 메서드에 상세 로깅
   - EventQueue 상태 추적

3. **타임아웃 설정**
   - 장기 실행 작업에 대한 적절한 타임아웃
   - 클라이언트 재시도 로직

### 7.6 결론

A2A와 LangGraph 통합은 기술적으로 가능하지만, 현재 SDK의 "Queue is closed" 오류는 내부 구현 문제로 보입니다. Currency Agent 예제 패턴을 정확히 따르고, RequestContext 속성을 올바르게 사용하며, 필요시 대안 구현을 고려하는 것이 현실적인 접근법입니다.