"""Planning Agent A2A Server V3 - Currency Agent 패턴 정확히 구현"""
import os
from typing import Optional, AsyncGenerator, Dict, Any
from uuid import uuid4
import logging

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.utils.errors import ServerError
from a2a.types import InvalidParamsError, InternalError
from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    Part,
    TextPart,
    DataPart,
    Task,
    TaskState,
    TaskStatus,
)

from agents.agent.planning_agent import PlanningAgent, PlanningState
from agents.graph_builders import create_azure_llm
from langgraph.checkpoint.memory import InMemorySaver

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlanningAgentWrapper:
    """Planning Agent를 Currency Agent 패턴으로 래핑"""
    
    def __init__(self):
        self.agent = None
        self.graph = None
        self._initialize()
    
    def _initialize(self):
        """에이전트 초기화"""
        try:
            llm = create_azure_llm()
            checkpointer = InMemorySaver()
            
            self.agent = PlanningAgent(
                model=llm,
                state_schema=PlanningState,
                checkpointer=checkpointer,
                is_debug=True
            )
            self.graph = self.agent.build_graph()
            logger.info("PlanningAgentWrapper initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PlanningAgentWrapper: {e}")
            raise
    
    async def stream(self, query: str, context_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Currency Agent 패턴의 stream 메서드"""
        logger.debug(f"Starting stream for query: {query[:50]}..., context_id: {context_id}")
        
        try:
            # 초기 상태 생성
            initial_state = PlanningState(
                user_request=query,
                messages=[]
            )
            
            # 중간 상태 업데이트 전송
            yield {
                'is_task_complete': False,
                'require_user_input': False,
                'content': '사용자 요청을 분석 중입니다...'
            }
            
            # LangGraph 실행 (스트리밍으로 변경)
            final_state = {}
            step_count = 0
            
            # graph가 None이 아닌지 확인
            if not self.graph:
                raise Exception("Graph not initialized")
                
            async for chunk in self.graph.astream(
                initial_state,
                config={"configurable": {"thread_id": context_id}}
            ):
                step_count += 1
                logger.debug(f"Stream chunk {step_count}: {list(chunk.keys())}")
                
                # 상태 업데이트
                final_state.update(chunk)
                
                # 중간 진행 상황 전송
                if "analyzed_intent" in chunk and chunk["analyzed_intent"]:
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': '요청 분석이 완료되었습니다. 작업 계획을 수립 중입니다...'
                    }
                elif "tasks" in chunk and chunk["tasks"]:
                    task_count = len(chunk["tasks"])
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': f'{task_count}개의 작업을 계획했습니다...'
                    }
            
            # 최종 결과 생성
            result = {
                "analyzed_intent": final_state.get("analyzed_intent", ""),
                "tasks": [task.dict() for task in final_state.get("tasks", [])] if final_state.get("tasks") else [],
                "execution_plan": final_state.get("execution_plan", ""),
                "is_plan_approved": final_state.get("is_plan_approved", False)
            }
            
            logger.info(f"Stream completed successfully with {step_count} steps")
            
            # 최종 응답
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': final_state.get("execution_plan", "계획 수립이 완료되었습니다."),
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error in planning agent stream: {str(e)}", exc_info=True)
            # 에러 시에도 완료 상태로 전송 (Currency Agent 패턴)
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': f'오류가 발생했습니다: {str(e)}'
            }


class PlanningAgentExecutorV3(AgentExecutor):
    """Planning Agent를 위한 A2A Agent Executor V3"""
    
    def __init__(self):
        self.agent = PlanningAgentWrapper()
    
    def _validate_request(self, context: RequestContext) -> tuple[str, Optional[Task]]:
        """요청 검증 및 쿼리 추출"""
        if not context.message or not context.message.parts:
            raise ServerError(InvalidParamsError())
        
        query = ""
        for part in context.message.parts:
            if isinstance(part.root, TextPart):
                query += part.root.text
        
        if not query:
            raise ServerError(InvalidParamsError())
        
        task = None  # DefaultRequestHandler가 태스크를 관리함
        return query, task
    
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        """Currency Agent 패턴의 execute 메서드"""
        logger.info("Execute method called")
        task_updater = None
        
        try:
            # 요청 검증
            query, task = self._validate_request(context)
            logger.debug(f"Query: {query[:50]}..., Task: {task}")
            
            # 태스크가 없으면 새로 생성
            if not task:
                task = self._new_task(context)
                await event_queue.enqueue_event(task)
                logger.info(f"Created new task: {task.id}")
            
            # TaskUpdater 생성
            task_updater = TaskUpdater(event_queue, task.id, task.contextId)
            
            # Task 상태 전이: submitted → working
            await task_updater.submit()
            await task_updater.start_work()
            
            # 에이전트 스트림 처리
            item_count = 0
            async for item in self.agent.stream(query, task.contextId):
                item_count += 1
                logger.debug(f"Processing stream item {item_count}: is_complete={item.get('is_task_complete')}")
                
                is_task_complete = item['is_task_complete']
                require_user_input = item.get('require_user_input', False)
                
                if not is_task_complete and not require_user_input:
                    # 작업 진행 중
                    await task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            parts=[Part(root=TextPart(text=item['content']))]
                        )
                    )
                elif require_user_input:
                    # 사용자 입력 필요
                    await task_updater.update_status(
                        TaskState.input_required,
                        message=task_updater.new_agent_message(
                            parts=[Part(root=TextPart(text=item['content']))]
                        )
                    )
                    break
                else:
                    # 태스크 완료
                    parts = [Part(root=TextPart(text=item['content']))]
                    if 'data' in item:
                        parts.append(Part(root=DataPart(data=item['data'])))
                    
                    await task_updater.update_status(
                        TaskState.completed,
                        message=task_updater.new_agent_message(parts=parts),
                        final=True  # Queue 종료를 명시
                    )
            
            logger.info(f"Execute completed successfully after {item_count} items")
                    
        except ServerError:
            logger.error("ServerError in execute")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in execute: {str(e)}", exc_info=True)
            # 에러 발생 시 태스크 실패 상태로 업데이트
            if task_updater:
                try:
                    await task_updater.update_status(
                        TaskState.failed,
                        message=task_updater.new_agent_message(
                            parts=[Part(root=TextPart(text=f"에러가 발생했습니다: {str(e)}"))]
                        ),
                        final=True  # Queue 종료를 명시
                    )
                except Exception as update_error:
                    logger.error(f"Failed to update task status: {update_error}")
            raise ServerError(InternalError())
    
    def _new_task(self, context: RequestContext) -> Task:
        """새 태스크 생성"""
        return Task(
            id=context.task_id or str(uuid4()),
            contextId=context.context_id or str(uuid4()),
            status=TaskStatus(state=TaskState.working)
        )
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """태스크 취소"""
        task_id = context.task_id or str(uuid4())
        context_id = context.context_id or str(uuid4())
        task_updater = TaskUpdater(event_queue, task_id, context_id)
        await task_updater.update_status(
            TaskState.canceled,
            message=task_updater.new_agent_message(
                parts=[Part(root=TextPart(text="태스크가 취소되었습니다."))]
            ),
            final=True  # Queue 종료를 명시
        )


# A2A 서버 생성 및 실행
if __name__ == '__main__':
    # Agent Skill 정의
    skill = AgentSkill(
        id='planning_agent_v3',
        name='계획 수립 V3',
        description='사용자 요청을 분석하고 작업 계획을 수립합니다',
        tags=['planning', 'task-breakdown', 'project-management'],
        examples=['LangGraph 멀티 에이전트 시스템 구축 계획', 'AI 챗봇 서비스 개발 계획'],
    )
    
    # Agent Card 정의
    agent_card = AgentCard(
        name='Planning Agent V3',
        description='사용자 요청을 분석하고 실행 가능한 작업 계획을 수립하는 에이전트',
        url=f'http://localhost:{os.getenv("PLANNING_AGENT_PORT", "8003")}/',
        version='3.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text', 'application/json'],
        capabilities=AgentCapabilities(
            streaming=True
        ),
        skills=[skill],
    )

    # Task Store 생성
    task_store = InMemoryTaskStore()
    
    # Request Handler 생성
    request_handler = DefaultRequestHandler(
        agent_executor=PlanningAgentExecutorV3(),
        task_store=task_store
    )
    
    # A2A Server 생성
    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )
    application = app.build()
    
    # 서버 시작
    import uvicorn
    port = int(os.getenv('PLANNING_AGENT_PORT', '8003'))
    logger.info(f'Planning Agent A2A Server V3 starting on port {port}')
    
    uvicorn.run(application, host='0.0.0.0', port=port)