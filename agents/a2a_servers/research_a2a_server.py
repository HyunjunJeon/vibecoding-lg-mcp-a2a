"""Research Agent A2A Server - 자료조사 에이전트를 A2A 서버로 래핑"""
import os
from typing import AsyncGenerator
from uuid import uuid4

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageResponse,
    SendStreamingMessageSuccessResponse,
    Task,
    TaskState,
    TaskStatus,
    Message,
    Role,
    Part,
    TextPart,
    DataPart,
    CancelTaskRequest,
    CancelTaskResponse,
    TaskResubscriptionRequest,
    JSONRPCErrorResponse,
    UnsupportedOperationError,
)

from agents.agent.research_agent import ResearchAgent, ResearchState
from agents.graph_builders import create_azure_llm
from agents.tools.mcp_client import get_mcp_client
from langgraph.checkpoint.memory import InMemorySaver


class ResearchAgentExecutor(AgentExecutor):
    """Research Agent를 위한 A2A Agent Executor"""
    
    def __init__(self):
        self.agent = None
        self.graph = None
        self.mcp_client = None
    
    async def initialize(self):
        """에이전트 초기화"""
        if self.agent is None:
            llm = create_azure_llm()
            checkpointer = InMemorySaver()
            
            # MCP 클라이언트 초기화 (선택사항)
            try:
                self.mcp_client = await get_mcp_client()
            except Exception as e:
                print(f"MCP 클라이언트 초기화 실패: {e}")
                self.mcp_client = None
            
            self.agent = ResearchAgent(
                model=llm,
                state_schema=ResearchState,
                checkpointer=checkpointer,
                mcp_client=self.mcp_client,
                is_debug=True
            )
            self.graph = self.agent.build_graph()
    
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        """A2A 프로토콜에 따른 execute 메서드 구현"""
        # 에이전트 초기화
        await self.initialize()
        
        # TaskUpdater 생성
        task_id = context.task_id or str(uuid4())
        context_id = context.context_id or str(uuid4())
        task_updater = TaskUpdater(event_queue, task_id, context_id)
        await task_updater.submit()
        await task_updater.start_work()
        
        try:
            # 메시지에서 연구 주제 추출
            message_text = ""
            
            if context.message and context.message.parts:
                for part in context.message.parts:
                    if isinstance(part.root, TextPart):
                        message_text += part.root.text
            
            # LangGraph 에이전트 실행
            initial_state = ResearchState(
                research_query=message_text,
                messages=[]
            )
            
            # graph가 None이 아닌지 확인
            if self.graph is None:
                await self.initialize()
            
            # 비동기적으로 실행
            final_state = await self.graph.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": task_id}}
            )
            
            # 결과 구성
            result = {
                "search_keywords": final_state.get("search_keywords", []),
                "web_results": [r.dict() for r in final_state.get("web_results", [])],
                "vector_results": [r.dict() for r in final_state.get("vector_results", [])],
                "aggregated_results": [r.dict() for r in final_state.get("aggregated_results", [])],
                "research_summary": final_state.get("research_summary", ""),
                "sources_cited": final_state.get("sources_cited", [])
            }
            
            # 응답 메시지 생성
            summary_text = final_state.get("research_summary", "조사가 완료되었습니다.")
            
            # 태스크 완료
            await task_updater.update_status(
                TaskState.completed,
                message=task_updater.new_agent_message(
                    parts=[
                        Part(root=TextPart(text=summary_text)),
                        Part(root=DataPart(data=result))
                    ]
                ),
                final=True  # Queue 종료를 명시
            )
            
        except Exception as e:
            # 오류 처리
            await task_updater.update_status(
                TaskState.failed,
                message=task_updater.new_agent_message(
                    parts=[Part(root=TextPart(text=f"오류가 발생했습니다: {str(e)}"))]
                ),
                final=True  # Queue 종료를 명시
            )
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """A2A 프로토콜에 따른 cancel 메서드 구현"""
        # 태스크 취소 로직
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
    
    async def on_message_send(
        self, request: SendMessageRequest, task: Task | None
    ) -> SendMessageResponse:
        """일반 메시지 처리 (비스트리밍)"""
        # 에이전트 초기화
        await self.initialize()
        
        # 메시지에서 연구 주제 추출
        message_text = ""
        for part in request.params.message.parts:
            if isinstance(part.root, TextPart):
                message_text += part.root.text
        
        # 새로운 태스크 생성 (태스크는 핸들러가 관리)
        task_id = str(uuid4())
        
        try:
            # LangGraph 에이전트 실행
            initial_state = ResearchState(
                research_query=message_text,
                messages=[]
            )
            
            # graph가 None이 아닌지 확인
            if self.graph is None:
                await self.initialize()
            
            # 비동기적으로 실행
            final_state = await self.graph.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": task_id}}
            )
            
            # 결과 구성
            result = {
                "search_keywords": final_state.get("search_keywords", []),
                "web_results": [r.dict() for r in final_state.get("web_results", [])],
                "vector_results": [r.dict() for r in final_state.get("vector_results", [])],
                "aggregated_results": [r.dict() for r in final_state.get("aggregated_results", [])],
                "research_summary": final_state.get("research_summary", ""),
                "sources_cited": final_state.get("sources_cited", [])
            }
            
            # 응답 메시지 생성
            summary_text = final_state.get("research_summary", "조사가 완료되었습니다.")
            response_message = Message(
                role=Role.agent,
                parts=[
                    Part(root=TextPart(text=summary_text)),
                    Part(root=DataPart(data=result))
                ],
                messageId=str(uuid4())
            )
            
            return SendMessageResponse(
                root=SendMessageSuccessResponse(
                    id=request.id,
                    result=response_message
                )
            )
            
        except Exception as e:
            # 오류 처리
            error_message = Message(
                role=Role.agent,
                parts=[Part(root=TextPart(text=f"오류가 발생했습니다: {str(e)}"))],
                messageId=str(uuid4())
            )
            
            return SendMessageResponse(
                root=SendMessageSuccessResponse(
                    id=request.id,
                    result=error_message
                )
            )
    
    async def on_message_stream(
        self, request: SendStreamingMessageRequest, task: Task | None
    ) -> AsyncGenerator[SendStreamingMessageResponse, None]:
        """스트리밍 메시지 처리"""
        # 에이전트 초기화
        await self.initialize()
        
        # 메시지에서 연구 주제 추출
        message_text = ""
        for part in request.params.message.parts:
            if isinstance(part.root, TextPart):
                message_text += part.root.text
        
        # 새로운 태스크 생성
        task_id = str(uuid4())
        if not task:
            task = Task(
                id=task_id,
                contextId=str(uuid4()),
                status=TaskStatus(state=TaskState.working)
            )
        
        # 초기 태스크 상태 전송
        yield SendStreamingMessageResponse(
            root=SendStreamingMessageSuccessResponse(
                id=request.id,
                result=task
            )
        )
        
        try:
            # LangGraph 에이전트 실행
            initial_state = ResearchState(
                research_query=message_text,
                messages=[]
            )
            
            # graph가 None이 아닌지 확인
            if self.graph is None:
                await self.initialize()
            
            # 스트리밍으로 실행
            async for chunk in self.graph.astream_events(
                initial_state,
                config={"configurable": {"thread_id": task_id}}
            ):
                # 중간 상태 업데이트 전송
                if "search_keywords" in chunk and chunk["search_keywords"]:
                    keywords = ", ".join(chunk["search_keywords"][:3])
                    update_message = Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=f"검색 키워드 추출: {keywords}..."))],
                        messageId=str(uuid4())
                    )
                    yield SendStreamingMessageResponse(
                        root=SendStreamingMessageSuccessResponse(
                            id=request.id,
                            result=update_message
                        )
                    )
                    
                elif "web_results" in chunk and chunk["web_results"]:
                    count = len(chunk["web_results"])
                    update_message = Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=f"웹 검색 완료: {count}개 결과"))],
                        messageId=str(uuid4())
                    )
                    yield SendStreamingMessageResponse(
                        root=SendStreamingMessageSuccessResponse(
                            id=request.id,
                            result=update_message
                        )
                    )
                    
                elif "vector_results" in chunk and chunk["vector_results"]:
                    count = len(chunk["vector_results"])
                    update_message = Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=f"벡터 검색 완료: {count}개 결과"))],
                        messageId=str(uuid4())
                    )
                    yield SendStreamingMessageResponse(
                        root=SendStreamingMessageSuccessResponse(
                            id=request.id,
                            result=update_message
                        )
                    )
                    
                elif "research_summary" in chunk and chunk["research_summary"]:
                    update_message = Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(text="조사 결과 요약 중..."))],
                        messageId=str(uuid4())
                    )
                    yield SendStreamingMessageResponse(
                        root=SendStreamingMessageSuccessResponse(
                            id=request.id,
                            result=update_message
                        )
                    )
            
            # 최종 상태 가져오기
            final_state = await self.graph.aget_state(
                config={"configurable": {"thread_id": task_id}}
            )
            
            # 결과 구성
            result = {
                "search_keywords": final_state.values.get("search_keywords", []),
                "web_results": [r.dict() for r in final_state.values.get("web_results", [])],
                "vector_results": [r.dict() for r in final_state.values.get("vector_results", [])],
                "aggregated_results": [r.dict() for r in final_state.values.get("aggregated_results", [])],
                "research_summary": final_state.values.get("research_summary", ""),
                "sources_cited": final_state.values.get("sources_cited", [])
            }
            
            # 최종 결과 전송
            summary_text = final_state.values.get("research_summary", "조사가 완료되었습니다.")
            final_message = Message(
                role=Role.agent,
                parts=[
                    Part(root=TextPart(text=summary_text)),
                    Part(root=DataPart(data=result))
                ],
                messageId=str(uuid4())
            )
            
            yield SendStreamingMessageResponse(
                root=SendStreamingMessageSuccessResponse(
                    id=request.id,
                    result=final_message
                )
            )
            
        except Exception as e:
            # 오류 메시지 전송
            error_message = Message(
                role=Role.agent,
                parts=[Part(root=TextPart(text=f"오류가 발생했습니다: {str(e)}"))],
                messageId=str(uuid4())
            )
            yield SendStreamingMessageResponse(
                root=SendStreamingMessageSuccessResponse(
                    id=request.id,
                    result=error_message
                )
            )
    
    async def on_cancel(
        self, request: CancelTaskRequest, task: Task
    ) -> CancelTaskResponse:
        """태스크 취소"""
        # 미지원 작업
        return CancelTaskResponse(
            root=JSONRPCErrorResponse(
                id=request.id,
                error=UnsupportedOperationError()
            )
        )
    
    async def on_resubscribe(
        self, request: TaskResubscriptionRequest, task: Task
    ) -> JSONRPCErrorResponse:
        """태스크 재구독"""
        # 미지원 작업
        return JSONRPCErrorResponse(
            id=request.id,
            error=UnsupportedOperationError()
        )


# A2A 서버 생성 및 실행
if __name__ == '__main__':
    # Agent Skill 정의
    skill = AgentSkill(
        id='research_agent',
        name='자료 조사',
        description='웹 검색과 벡터 DB 검색을 통해 정보를 수집하고 요약합니다',
        tags=['research', 'web-search', 'vector-search', 'information-gathering'],
        examples=['LangGraph에 대해 조사해주세요', 'AI 에이전트 시스템의 최신 동향'],
    )
    
    # Agent Card 정의
    agent_card = AgentCard(
        name='Research Agent',
        description='웹 검색과 벡터 DB 검색을 통해 정보를 수집하고 요약하는 에이전트',
        url=f'http://localhost:{os.getenv("RESEARCH_AGENT_PORT", "8001")}/',
        version='1.0.0',
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
        agent_executor=ResearchAgentExecutor(),
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
    port = int(os.getenv('RESEARCH_AGENT_PORT', '8001'))
    print(f'Research Agent A2A Server starting on port {port}')
    
    uvicorn.run(application, host='0.0.0.0', port=port)