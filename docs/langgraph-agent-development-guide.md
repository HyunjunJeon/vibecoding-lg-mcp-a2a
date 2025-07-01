# LangGraph 에이전트 개발 가이드

이 문서는 `agents/base/` 모듈을 활용하여 표준화된 LangGraph 에이전트를 개발하는 방법을 설명합니다.

## 목차

1. [개요](#개요)
2. [BaseAgent 아키텍처](#baseagent-아키텍처)
3. [에이전트 개발 단계별 가이드](#에이전트-개발-단계별-가이드)
4. [상태 관리](#상태-관리)
5. [노드와 엣지 구성](#노드와-엣지-구성)
6. [고급 패턴](#고급-패턴)
7. [베스트 프랙티스](#베스트-프랙티스)
8. [예제](#예제)

## 개요

LangGraph 에이전트는 상태 기반의 그래프 구조로 작동하는 AI 에이전트입니다. 이 프로젝트에서는 `BaseAgent` 클래스를 통해 표준화된 에이전트 개발 패턴을 제공합니다.

### 핵심 개념

- **노드(Node)**: 특정 작업을 수행하는 함수 (async)
- **엣지(Edge)**: 노드 간의 연결 및 흐름 제어
- **상태(State)**: 노드 간에 공유되는 데이터
- **그래프(Graph)**: 노드와 엣지로 구성된 워크플로우

## BaseAgent 아키텍처

### BaseAgent 클래스 구조

```python
from agents.base import BaseAgent, BaseState

class BaseAgent:
    """모든 LangGraph 에이전트의 기반 클래스"""
    
    def __init__(self, ...):
        """에이전트 초기화 및 그래프 빌드"""
        
    def build_graph(self):
        """그래프 구조 생성"""
        
    def init_nodes(self, graph: StateGraph):
        """노드 초기화 - 서브클래스에서 구현 필수"""
        
    def init_edges(self, graph: StateGraph):
        """엣지 초기화 - 서브클래스에서 구현 필수"""
```

### 라이프사이클

1. **초기화**: `__init__` 메서드에서 필수 구성요소 설정
2. **그래프 빌드**: `build_graph()` 자동 호출
3. **노드 등록**: `init_nodes()` 실행
4. **엣지 연결**: `init_edges()` 실행
5. **컴파일**: 그래프 컴파일 및 실행 준비 완료

## 에이전트 개발 단계별 가이드

### 1단계: 템플릿 복사

```bash
# 템플릿 파일 복사
cp agents/agent/template/base_agent_template.py agents/agent/my_new_agent.py
```

### 2단계: 클래스 정의

```python
from typing import Any, ClassVar
from agents.base import BaseAgent, BaseState

class MyNewAgent(BaseAgent):
    """새로운 에이전트 설명"""
    
    # 노드 이름 상수 정의
    NODE_NAMES: ClassVar[dict[str, str]] = {
        "PROCESS": "process_data",
        "VALIDATE": "validate_result",
        "OUTPUT": "generate_output"
    }
```

### 3단계: 상태 스키마 정의

```python
from pydantic import BaseModel, Field
from typing import Optional

class MyAgentState(BaseState):
    """에이전트 상태 정의"""
    
    # 기본 messages 필드는 BaseState에서 상속
    
    # 커스텀 필드 추가
    input_data: str = Field(description="입력 데이터")
    processed_data: Optional[str] = Field(default=None, description="처리된 데이터")
    validation_result: Optional[bool] = Field(default=None, description="검증 결과")
    final_output: Optional[str] = Field(default=None, description="최종 출력")
```

### 4단계: 노드 초기화

```python
def init_nodes(self, graph: StateGraph):
    """그래프에 노드 추가"""
    
    # get_node_name() 메서드로 노드 이름 가져오기
    process_node = self.get_node_name("PROCESS")
    validate_node = self.get_node_name("VALIDATE")
    output_node = self.get_node_name("OUTPUT")
    
    # 노드 추가
    graph.add_node(process_node, self.process_data)
    graph.add_node(validate_node, self.validate_result)
    graph.add_node(output_node, self.generate_output)
```

### 5단계: 엣지 구성

```python
def init_edges(self, graph: StateGraph):
    """노드 간 연결 설정"""
    
    process_node = self.get_node_name("PROCESS")
    validate_node = self.get_node_name("VALIDATE")
    output_node = self.get_node_name("OUTPUT")
    
    # 진입점 설정
    graph.set_entry_point(process_node)
    
    # 순차적 연결
    graph.add_edge(process_node, validate_node)
    
    # 조건부 연결
    graph.add_conditional_edges(
        validate_node,
        self.decide_next_step,  # 조건 함수
        {
            "retry": process_node,  # 재시도
            "success": output_node  # 성공
        }
    )
    
    # 종료점 설정
    graph.set_finish_point(output_node)
```

### 6단계: 노드 함수 구현

```python
async def process_data(self, state: MyAgentState, config: RunnableConfig):
    """데이터 처리 노드"""
    try:
        # LLM 호출 예시
        response = await self.model.ainvoke(
            f"Process this data: {state.input_data}",
            config=config
        )
        
        # 상태 업데이트
        state.processed_data = response.content
        
        # 메시지 추가 (선택적)
        state.messages.append(
            AIMessage(content=f"Processed: {response.content}")
        )
        
        return state
        
    except Exception as e:
        self.logger.error(f"Processing failed: {e}")
        raise

async def validate_result(self, state: MyAgentState, config: RunnableConfig):
    """결과 검증 노드"""
    # 검증 로직
    if state.processed_data and len(state.processed_data) > 10:
        state.validation_result = True
    else:
        state.validation_result = False
    
    return state

async def generate_output(self, state: MyAgentState, config: RunnableConfig):
    """최종 출력 생성 노드"""
    state.final_output = f"Final result: {state.processed_data}"
    return state
```

### 7단계: 조건부 엣지 함수

```python
def decide_next_step(self, state: MyAgentState, config: RunnableConfig) -> str:
    """검증 결과에 따른 다음 단계 결정"""
    
    if state.validation_result:
        return "success"
    else:
        # 재시도 횟수 체크 (선택적)
        retry_count = state.get("retry_count", 0)
        if retry_count < self.max_retry_attempts:
            state["retry_count"] = retry_count + 1
            return "retry"
        else:
            return "success"  # 최대 재시도 후 진행
```

## 상태 관리

### 상태 타입

1. **BaseState**: 기본 상태 (messages 필드 포함)
2. **BaseInputState**: 입력 전용 상태
3. **BaseOutputState**: 출력 전용 상태

### 상태 업데이트 패턴

```python
# 1. 직접 할당
state.field = value

# 2. 메시지 추가 (add_messages reducer 자동 적용)
state.messages.append(HumanMessage(content="..."))
state.messages.append(AIMessage(content="..."))

# 3. 딕셔너리 스타일 (선택적 필드)
state["optional_field"] = value
```

### 상태 유효성 검증

```python
from pydantic import validator

class MyAgentState(BaseState):
    score: float
    
    @validator('score')
    def validate_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Score must be between 0 and 100')
        return v
```

## 노드와 엣지 구성

### 노드 타입

1. **처리 노드**: 데이터 변환, LLM 호출 등
2. **검증 노드**: 조건 확인, 유효성 검증
3. **분기 노드**: 조건부 라우팅
4. **집계 노드**: 여러 결과 통합

### 엣지 패턴

#### 순차적 흐름
```python
graph.add_edge("node1", "node2")
graph.add_edge("node2", "node3")
```

#### 조건부 분기
```python
graph.add_conditional_edges(
    "decision_node",
    lambda state: "path_a" if state.condition else "path_b",
    {
        "path_a": "node_a",
        "path_b": "node_b"
    }
)
```

#### 병렬 실행
```python
# 팬아웃
graph.add_edge("start", ["parallel1", "parallel2", "parallel3"])

# 팬인
graph.add_edge(["parallel1", "parallel2", "parallel3"], "merge")
```

#### 순환 구조
```python
graph.add_edge("process", "check")
graph.add_conditional_edges(
    "check",
    lambda state: "continue" if state.needs_retry else "done",
    {
        "continue": "process",  # 다시 처리
        "done": "finish"
    }
)
```

## 고급 패턴

### 1. 서브그래프 활용

```python
class ComplexAgent(BaseAgent):
    def init_nodes(self, graph: StateGraph):
        # 서브그래프 생성
        sub_graph = self.create_sub_workflow()
        graph.add_node("sub_workflow", sub_graph)
    
    def create_sub_workflow(self):
        """독립적인 서브 워크플로우 생성"""
        sub = StateGraph(MyAgentState)
        # 서브그래프 구성
        return sub.compile()
```

### 2. 도구(Tool) 통합

```python
from langchain.tools import Tool

class ToolAgent(BaseAgent):
    def __init__(self, *args, tools: list[Tool], **kwargs):
        self.tools = tools
        super().__init__(*args, **kwargs)
    
    async def use_tools(self, state: BaseState, config: RunnableConfig):
        """도구 사용 노드"""
        tool_output = await self.tools[0].ainvoke(
            state.input_data,
            config=config
        )
        state.tool_result = tool_output
        return state
```

### 3. 스트리밍 응답

```python
async def streaming_node(self, state: BaseState, config: RunnableConfig):
    """스트리밍 응답 생성"""
    async for chunk in self.model.astream(
        state.messages,
        config=config
    ):
        # 청크 단위로 처리
        yield {"partial_output": chunk.content}
```

### 4. 체크포인트 활용

```python
class CheckpointAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        # 체크포인터 설정
        kwargs['checkpointer'] = MemorySaver()
        super().__init__(*args, **kwargs)
    
    async def save_checkpoint(self, state: BaseState, config: RunnableConfig):
        """중간 상태 저장"""
        # 체크포인트는 자동으로 저장됨
        state.checkpoint_saved = True
        return state
```

### 5. 에러 처리 및 복구

```python
async def resilient_node(self, state: BaseState, config: RunnableConfig):
    """에러 처리가 포함된 노드"""
    try:
        result = await self.risky_operation(state)
        state.result = result
    except SpecificError as e:
        # 특정 에러 처리
        state.error = str(e)
        state.should_retry = True
    except Exception as e:
        # 일반 에러 처리
        self.logger.error(f"Unexpected error: {e}")
        state.error = "처리 중 오류 발생"
        state.should_skip = True
    
    return state
```

## 베스트 프랙티스

### 1. 노드 설계 원칙

- **단일 책임**: 각 노드는 하나의 명확한 작업만 수행
- **멱등성**: 같은 입력에 대해 항상 같은 결과
- **상태 불변성**: 필요한 필드만 수정
- **에러 처리**: 예상 가능한 에러는 명시적으로 처리

### 2. 상태 관리 원칙

- **최소 상태**: 필요한 데이터만 상태에 포함
- **타입 안전성**: Pydantic 모델로 타입 검증
- **기본값 설정**: Optional 필드는 기본값 지정
- **검증 로직**: validator로 데이터 무결성 보장

### 3. 성능 최적화

- **비동기 처리**: I/O 작업은 async/await 활용
- **병렬 실행**: 독립적인 작업은 병렬로 처리
- **캐싱**: 반복적인 LLM 호출은 캐싱 고려
- **조기 종료**: 불필요한 노드 실행 방지

### 4. 디버깅 및 모니터링

```python
class DebuggableAgent(BaseAgent):
    def __init__(self, *args, is_debug: bool = True, **kwargs):
        super().__init__(*args, is_debug=is_debug, **kwargs)
    
    async def debug_node(self, state: BaseState, config: RunnableConfig):
        """디버그 정보 출력"""
        if self.is_debug:
            self.logger.debug(f"Current state: {state.model_dump()}")
            self.logger.debug(f"Config: {config}")
        
        # 실제 처리
        result = await self.process(state)
        
        if self.is_debug:
            self.logger.debug(f"Result: {result}")
        
        return result
```

### 5. 테스트 작성

```python
import pytest
from langchain_core.messages import HumanMessage

@pytest.mark.asyncio
async def test_agent_workflow():
    """에이전트 워크플로우 테스트"""
    
    # 에이전트 생성
    agent = MyNewAgent(
        model=MockChatModel(),
        state_schema=MyAgentState
    )
    
    # 초기 상태 설정
    initial_state = {
        "messages": [HumanMessage(content="Test input")],
        "input_data": "Test data"
    }
    
    # 워크플로우 실행
    result = await agent.graph.ainvoke(initial_state)
    
    # 결과 검증
    assert result["final_output"] is not None
    assert result["validation_result"] is True
```

## 예제

### 간단한 에이전트 예제

```python
from typing import ClassVar
from agents.base import BaseAgent, BaseState
from langchain_core.messages import AIMessage
from pydantic import Field

class SimpleAnalysisAgent(BaseAgent):
    """텍스트 분석을 수행하는 간단한 에이전트"""
    
    NODE_NAMES: ClassVar[dict[str, str]] = {
        "ANALYZE": "analyze_text",
        "SUMMARIZE": "summarize_result"
    }
    
    class State(BaseState):
        input_text: str = Field(description="분석할 텍스트")
        analysis: str = Field(default="", description="분석 결과")
        summary: str = Field(default="", description="요약")
    
    def init_nodes(self, graph: StateGraph):
        graph.add_node(self.get_node_name("ANALYZE"), self.analyze_text)
        graph.add_node(self.get_node_name("SUMMARIZE"), self.summarize_result)
    
    def init_edges(self, graph: StateGraph):
        analyze = self.get_node_name("ANALYZE")
        summarize = self.get_node_name("SUMMARIZE")
        
        graph.set_entry_point(analyze)
        graph.add_edge(analyze, summarize)
        graph.set_finish_point(summarize)
    
    async def analyze_text(self, state: State, config: RunnableConfig):
        """텍스트 분석"""
        response = await self.model.ainvoke(
            f"다음 텍스트를 분석해주세요: {state.input_text}",
            config=config
        )
        state.analysis = response.content
        state.messages.append(AIMessage(content=f"분석 완료: {response.content}"))
        return state
    
    async def summarize_result(self, state: State, config: RunnableConfig):
        """결과 요약"""
        response = await self.model.ainvoke(
            f"다음 분석 결과를 한 문장으로 요약해주세요: {state.analysis}",
            config=config
        )
        state.summary = response.content
        state.messages.append(AIMessage(content=f"요약: {response.content}"))
        return state
```

### 복잡한 에이전트 예제

```python
class AdvancedResearchAgent(BaseAgent):
    """다단계 연구를 수행하는 고급 에이전트"""
    
    NODE_NAMES: ClassVar[dict[str, str]] = {
        "PARSE_QUERY": "parse_research_query",
        "SEARCH": "perform_search",
        "VALIDATE": "validate_sources",
        "ANALYZE": "analyze_findings",
        "SYNTHESIZE": "synthesize_report",
        "REVIEW": "review_quality"
    }
    
    class State(BaseState):
        query: str = Field(description="연구 질의")
        parsed_query: dict = Field(default_factory=dict)
        search_results: list = Field(default_factory=list)
        valid_sources: list = Field(default_factory=list)
        analysis: dict = Field(default_factory=dict)
        report: str = Field(default="")
        quality_score: float = Field(default=0.0)
        needs_revision: bool = Field(default=False)
        revision_count: int = Field(default=0)
    
    def init_nodes(self, graph: StateGraph):
        for key, method_name in self.NODE_NAMES.items():
            node_name = self.get_node_name(key)
            graph.add_node(node_name, getattr(self, method_name))
    
    def init_edges(self, graph: StateGraph):
        # 노드 이름 가져오기
        parse = self.get_node_name("PARSE_QUERY")
        search = self.get_node_name("SEARCH")
        validate = self.get_node_name("VALIDATE")
        analyze = self.get_node_name("ANALYZE")
        synthesize = self.get_node_name("SYNTHESIZE")
        review = self.get_node_name("REVIEW")
        
        # 기본 플로우
        graph.set_entry_point(parse)
        graph.add_edge(parse, search)
        graph.add_edge(search, validate)
        graph.add_edge(validate, analyze)
        graph.add_edge(analyze, synthesize)
        graph.add_edge(synthesize, review)
        
        # 조건부 플로우 (품질 검토 후)
        graph.add_conditional_edges(
            review,
            self.check_quality,
            {
                "revise": analyze,  # 품질 미달 시 재분석
                "complete": END     # 품질 충족 시 종료
            }
        )
    
    def check_quality(self, state: State, config: RunnableConfig) -> str:
        """품질 검토 결과에 따른 라우팅"""
        if state.quality_score < 0.8 and state.revision_count < 2:
            state.needs_revision = True
            state.revision_count += 1
            return "revise"
        return "complete"
    
    # 각 노드 메서드 구현...
```

## 마무리

이 가이드는 LangGraph 에이전트 개발의 기본 패턴과 베스트 프랙티스를 다룹니다. 실제 개발 시에는 프로젝트의 요구사항에 맞게 이러한 패턴을 조정하여 사용하세요.

추가 리소스:
- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [프로젝트 예제 코드](/agents/agent/)
- [BaseAgent 소스 코드](/agents/base/base_agent.py)