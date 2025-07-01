"""계획 수립 에이전트: 사용자 요청을 분석하고 작업 계획을 수립하는 에이전트"""
from typing import Any, ClassVar, List, Dict, Literal, cast
from enum import Enum

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph, END
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field

from agents.base import BaseAgent, BaseState


class TaskType(str, Enum):
    """작업 유형 정의"""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    REPORT = "report"
    SUMMARY = "summary"
    COMPARISON = "comparison"


class Task(BaseModel):
    """개별 작업 정의"""
    id: str = Field(description="작업 ID")
    type: TaskType = Field(description="작업 유형")
    description: str = Field(description="작업 설명")
    priority: int = Field(description="우선순위 (1-5, 5가 가장 높음)")
    dependencies: List[str] = Field(default_factory=list, description="선행 작업 ID 목록")
    assigned_agent: str = Field(description="할당된 에이전트")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="작업 파라미터")


class PlanningState(BaseState):
    """계획 수립 에이전트의 상태"""
    user_request: str = Field(description="사용자의 원본 요청")
    analyzed_intent: str = Field(default="", description="분석된 사용자 의도")
    tasks: List[Task] = Field(default_factory=list, description="생성된 작업 목록")
    execution_plan: str = Field(default="", description="실행 계획 설명")
    is_plan_approved: bool = Field(default=False, description="계획 승인 여부")


class PlanningAgent(BaseAgent):
    """계획 수립 에이전트"""
    
    NODE_NAMES: ClassVar[dict[str, str]] = {
        "ANALYZE": "analyze_request",
        "CREATE_PLAN": "create_plan",
        "REVIEW_PLAN": "review_plan",
        "DELEGATE": "delegate_tasks",
    }

    def __init__(
        self,
        model: BaseChatModel,
        state_schema: Any = PlanningState,
        config_schema: Any | None = None,
        input_schema: Any | None = None,
        output_schema: Any | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        store: BaseStore | None = None,
        max_retry_attempts: int = 2,
        agent_name: str = "PlanningAgent",
        is_debug: bool = True,
    ) -> None:
        super().__init__(
            model=model,
            state_schema=state_schema,
            config_schema=config_schema,
            input_schema=input_schema,
            output_schema=output_schema,
            checkpointer=checkpointer,
            store=store,
            max_retry_attempts=max_retry_attempts,
            agent_name=agent_name,
            is_debug=is_debug,
        )

    def init_nodes(self, graph: StateGraph):
        """그래프에 노드 초기화"""        
        graph.add_node(self.get_node_name("ANALYZE"), self.analyze_request)
        graph.add_node(self.get_node_name("CREATE_PLAN"), self.create_plan)
        graph.add_node(self.get_node_name("REVIEW_PLAN"), self.review_plan)
        graph.add_node(self.get_node_name("DELEGATE"), self.delegate_tasks)

    def init_edges(self, graph: StateGraph):
        """그래프에 엣지 초기화"""
        # 워크플로우 정의
        graph.set_entry_point(self.get_node_name("ANALYZE"))
        graph.add_edge(self.get_node_name("ANALYZE"), self.get_node_name("CREATE_PLAN"))
        graph.add_edge(self.get_node_name("CREATE_PLAN"), self.get_node_name("REVIEW_PLAN"))
        
        # 조건부 엣지: 계획 검토 후 승인되면 위임, 아니면 다시 계획
        graph.add_conditional_edges(
            self.get_node_name("REVIEW_PLAN"),
            self.should_delegate,
            {
                "delegate": self.get_node_name("DELEGATE"),
                "revise": self.get_node_name("CREATE_PLAN"),
            }
        )
        
        graph.add_edge(self.get_node_name("DELEGATE"), END)

    async def analyze_request(self, state: PlanningState, config: RunnableConfig) -> PlanningState:
        """사용자 요청 분석"""
        try:
            prompt = f"""다음 사용자 요청을 분석하고 주요 의도와 목표를 파악하세요:

사용자 요청: {state.user_request}

다음 사항을 분석하세요:
1. 주요 목표는 무엇인가?
2. 어떤 유형의 작업이 필요한가? (조사, 분석, 보고서 작성 등)
3. 특별한 제약사항이나 요구사항이 있는가?
4. 예상되는 결과물의 형태는 무엇인가?

분석 결과를 간결하게 요약하세요."""

            response = await self.model.ainvoke([HumanMessage(content=prompt)], config)
            state.analyzed_intent = response.content
            
            if self.is_debug:
                print(f"[{self.agent_name}] 요청 분석 완료:")
                print(f"  의도: {state.analyzed_intent[:100]}...")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 요청 분석 중 오류: {e}")
            raise e

    async def create_plan(self, state: PlanningState, config: RunnableConfig) -> PlanningState:
        """작업 계획 생성"""
        try:
            prompt = f"""다음 분석된 의도를 바탕으로 구체적인 작업 계획을 수립하세요:

원본 요청: {state.user_request}
분석된 의도: {state.analyzed_intent}

다음 형식으로 작업들을 생성하세요:
1. 각 작업은 명확한 목표와 설명을 가져야 합니다
2. 작업 간 의존성을 고려하세요
3. 적절한 에이전트에게 할당하세요 (research_agent, report_writing_agent)
4. 우선순위를 설정하세요 (1-5)

JSON 형식으로 작업 목록을 반환하세요:
[
  {{
    "id": "task_1",
    "type": "research",
    "description": "작업 설명",
    "priority": 5,
    "dependencies": [],
    "assigned_agent": "research_agent",
    "parameters": {{}}
  }}
]"""

            response = await self.model.ainvoke([HumanMessage(content=prompt)], config)
            
            # 응답을 파싱하여 작업 목록 생성
            import json
            import re
            
            # JSON 블록 추출
            json_match = re.search(r'\[.*\]', str(response.content), re.DOTALL)
            if json_match:
                tasks_data = json.loads(json_match.group())
                state.tasks = [Task(**task_data) for task_data in tasks_data]
            
            # 실행 계획 설명 생성
            plan_prompt = f"""다음 작업들에 대한 전체 실행 계획을 간단히 설명하세요:

작업 목록:
{json.dumps([task.dict() for task in state.tasks], ensure_ascii=False, indent=2)}

계획을 2-3문장으로 요약하세요."""

            plan_response = await self.model.ainvoke([HumanMessage(content=plan_prompt)], config)
            state.execution_plan = cast(str, plan_response.content)
            
            if self.is_debug:
                print(f"[{self.agent_name}] 계획 생성 완료:")
                print(f"  작업 수: {len(state.tasks)}")
                print(f"  실행 계획: {state.execution_plan[:100]}...")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 계획 생성 중 오류: {e}")
            raise e

    async def review_plan(self, state: PlanningState, config: RunnableConfig) -> PlanningState:
        """계획 검토 및 승인"""
        try:
            # 계획 품질 검토
            review_prompt = f"""다음 계획을 검토하고 품질을 평가하세요:

원본 요청: {state.user_request}
분석된 의도: {state.analyzed_intent}
실행 계획: {state.execution_plan}
작업 수: {len(state.tasks)}

다음 기준으로 평가하세요:
1. 계획이 사용자 요청을 충족하는가?
2. 작업들이 논리적 순서로 배열되어 있는가?
3. 필요한 모든 단계가 포함되어 있는가?
4. 작업 할당이 적절한가?

계획이 적절하면 "승인", 수정이 필요하면 "수정필요"로 답하고 이유를 설명하세요."""

            response = await self.model.ainvoke([HumanMessage(content=review_prompt)], config)
            
            # 승인 여부 판단
            if "승인" in response.content and "수정필요" not in response.content:
                state.is_plan_approved = True
            else:
                state.is_plan_approved = False
                # 피드백을 상태에 추가하여 다음 계획 생성에 활용
                state.analyzed_intent += f"\n\n검토 피드백: {response.content}"
            
            if self.is_debug:
                print(f"[{self.agent_name}] 계획 검토 완료:")
                print(f"  승인 여부: {state.is_plan_approved}")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 계획 검토 중 오류: {e}")
            raise e

    async def delegate_tasks(self, state: PlanningState, config: RunnableConfig) -> PlanningState:
        """작업 위임"""
        try:
            # 실제 구현에서는 여기서 다른 에이전트들에게 작업을 전달
            # 현재는 로깅만 수행
            
            if self.is_debug:
                print(f"[{self.agent_name}] 작업 위임 시작:")
                for task in state.tasks:
                    print(f"  - {task.id}: {task.description} -> {task.assigned_agent}")
            
            # 상태에 위임 완료 표시
            state.messages.append(
                AIMessage(content=f"계획이 수립되었습니다. 총 {len(state.tasks)}개의 작업을 할당했습니다.")
            )
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 작업 위임 중 오류: {e}")
            raise e

    def should_delegate(self, state: PlanningState) -> Literal["delegate", "revise"]:
        """계획 승인 여부에 따라 다음 단계 결정"""
        return "delegate" if state.is_plan_approved else "revise"