"""Report Writing Agent A2A Server - 보고서 작성 에이전트를 A2A 서버로 래핑"""
import os
import json
from typing import AsyncGenerator
from datetime import datetime
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
    TaskStatus,
    TaskState,
    Message,
    Role,
    TextPart,
    DataPart,
    Part,
    GetTaskRequest,
    GetTaskSuccessResponse,
    GetTaskResponse,
    CancelTaskRequest,
    CancelTaskSuccessResponse,
    CancelTaskResponse,
    TaskResubscriptionRequest,
    JSONRPCErrorResponse,
    TaskNotFoundError,
    UnsupportedOperationError,
)

from agents.agent.report_writing_agent import ReportWritingAgent, ReportWritingState
from agents.graph_builders import create_azure_llm
from langgraph.checkpoint.memory import InMemorySaver


class ReportWritingAgentExecutor(AgentExecutor):
    """Report Writing Agent를 위한 A2A Agent Executor"""
    
    def __init__(self):
        self.agent = None
        self.graph = None
        self.active_tasks = {}
    
    async def initialize(self):
        """에이전트 초기화"""
        if self.agent is None:
            llm = create_azure_llm()
            checkpointer = InMemorySaver()
            
            self.agent = ReportWritingAgent(
                model=llm,
                state_schema=ReportWritingState,
                checkpointer=checkpointer,
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
            # 메시지에서 데이터 추출
            project_name = ""
            execution_plan = {}
            research_summary = ""
            
            if context.message and context.message.parts:
                for part in context.message.parts:
                    if isinstance(part.root, TextPart):
                        project_name = part.root.text
                    elif isinstance(part.root, DataPart):
                        data = part.root.data
                        if isinstance(data, dict):
                            if "project_name" in data:
                                project_name = data["project_name"]
                            if "execution_plan" in data:
                                execution_plan = data["execution_plan"]
                            if "research_summary" in data:
                                research_summary = data["research_summary"]
            
            # LangGraph 에이전트 실행
            initial_state = ReportWritingState(
                topic=project_name,  # topic 파라미터 사용
                # research_data 파라미터 사용
                research_data=json.dumps({
                    "execution_plan": execution_plan,
                    "research_summary": research_summary
                }),
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
            report_content = final_state.get("final_report", {})
            result = {
                "project_name": project_name,
                "report_title": report_content.get("title", f"{project_name} 프로젝트 보고서"),
                "report_content": report_content,
                "report_sections": list(report_content.keys()) if isinstance(report_content, dict) else [],
                "generated_at": datetime.now().isoformat()
            }
            
            # 응답 메시지 생성
            summary_text = f"{project_name} 프로젝트의 보고서가 성공적으로 작성되었습니다."
            
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
        self, 
        request: SendMessageRequest, 
        task: Task | None
    ) -> SendMessageResponse:
        """일반 메시지 처리 (비스트리밍)"""
        # 에이전트 초기화
        await self.initialize()
        
        # 메시지에서 데이터 추출
        project_name = ""
        execution_plan = {}
        research_summary = ""
        
        for part in request.params.message.parts:
            if isinstance(part.root, TextPart):
                project_name = part.root.text
            elif isinstance(part.root, DataPart):
                data = part.root.data
                if isinstance(data, dict):
                    if "project_name" in data:
                        project_name = data["project_name"]
                    if "execution_plan" in data:
                        execution_plan = data["execution_plan"]
                    if "research_summary" in data:
                        research_summary = data["research_summary"]
        
        # 새로운 태스크 생성 (태스크는 핸들러가 관리)
        task_id = str(uuid4())
        
        # 태스크 정보 저장
        self.active_tasks[task_id] = {
            "project_name": project_name,
            "started_at": datetime.now()
        }
        
        try:
            # LangGraph 에이전트 실행
            initial_state = ReportWritingState(
                topic=project_name,  # topic 파라미터 사용
                research_data={  # research_data 파라미터 사용
                    "execution_plan": execution_plan,
                    "research_summary": research_summary
                },
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
            report_content = final_state.get("final_report", {})
            result = {
                "project_name": project_name,
                "report_title": report_content.get("title", f"{project_name} 프로젝트 보고서"),
                "report_content": report_content,
                "report_sections": list(report_content.keys()) if isinstance(report_content, dict) else [],
                "generated_at": datetime.now().isoformat()
            }
            
            # 응답 메시지 생성
            summary_text = f"{project_name} 프로젝트의 보고서가 성공적으로 작성되었습니다."
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
        self,
        request: SendStreamingMessageRequest,
        task: Task | None
    ) -> AsyncGenerator[SendStreamingMessageResponse, None]:
        """스트리밍 메시지 처리"""
        # 에이전트 초기화
        await self.initialize()
        
        # 메시지에서 데이터 추출
        project_name = ""
        execution_plan = {}
        research_summary = ""
        
        for part in request.params.message.parts:
            if isinstance(part.root, TextPart):
                project_name = part.root.text
            elif isinstance(part.root, DataPart):
                data = part.root.data
                if isinstance(data, dict):
                    if "project_name" in data:
                        project_name = data["project_name"]
                    if "execution_plan" in data:
                        execution_plan = data["execution_plan"]
                    if "research_summary" in data:
                        research_summary = data["research_summary"]
        
        # 새로운 태스크 생성
        task_id = str(uuid4())
        if not task:
            task = Task(
                id=task_id,
                contextId=str(uuid4()),
                status=TaskStatus(state=TaskState.working)
            )
        
        # 태스크 정보 저장
        self.active_tasks[task_id] = {
            "task": task,
            "project_name": project_name,
            "started_at": datetime.now()
        }
        
        # 초기 태스크 상태 전송
        yield SendStreamingMessageResponse(
            root=SendStreamingMessageSuccessResponse(
                id=request.id,
                result=task
            )
        )
        
        try:
            # LangGraph 에이전트 실행
            initial_state = ReportWritingState(
                topic=project_name,  # topic 파라미터 사용
                research_data={  # research_data 파라미터 사용
                    "execution_plan": execution_plan,
                    "research_summary": research_summary
                },
                messages=[]
            )
            
            # graph가 None이 아닌지 확인
            if self.graph is None:
                await self.initialize()
            
            # 스트리밍으로 실행
            async for chunk in self.graph.astream(
                initial_state,
                config={"configurable": {"thread_id": task_id}}
            ):
                # 중간 상태 업데이트 전송
                if "executive_summary" in chunk and chunk["executive_summary"]:
                    update_message = Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(text="경영진 요약 작성 중..."))],
                        messageId=str(uuid4())
                    )
                    yield SendStreamingMessageResponse(
                        root=SendStreamingMessageSuccessResponse(
                            id=request.id,
                            result=update_message
                        )
                    )
                    
                elif "sections" in chunk and chunk["sections"]:
                    section_count = len(chunk["sections"])
                    update_message = Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=f"보고서 섹션 작성 중: {section_count}개 섹션 완료"))],
                        messageId=str(uuid4())
                    )
                    yield SendStreamingMessageResponse(
                        root=SendStreamingMessageSuccessResponse(
                            id=request.id,
                            result=update_message
                        )
                    )
                    
                elif "final_report" in chunk and chunk["final_report"]:
                    update_message = Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(text="최종 보고서 생성 중..."))],
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
            report_content = final_state.values.get("final_report", {})
            result = {
                "project_name": project_name,
                "report_title": report_content.get("title", f"{project_name} 프로젝트 보고서"),
                "report_content": report_content,
                "report_sections": list(report_content.keys()) if isinstance(report_content, dict) else [],
                "generated_at": datetime.now().isoformat()
            }
            
            # 최종 결과 전송
            summary_text = f"{project_name} 프로젝트의 보고서가 성공적으로 작성되었습니다."
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
    
    async def on_get_task(
        self, 
        request: GetTaskRequest
    ) -> GetTaskResponse:
        """태스크 조회"""
        task_id = request.params.id
        
        if task_id not in self.active_tasks:
            # 태스크를 찾을 수 없음
            return GetTaskResponse(
                root=JSONRPCErrorResponse(
                    id=request.id,
                    error=TaskNotFoundError()
                )
            )
        
        task_info = self.active_tasks[task_id]
        task = task_info.get("task")
        
        if not task:
            # 이전 버전 호환성을 위한 처리
            task = Task(
                id=task_id,
                contextId=str(uuid4()),
                status=TaskStatus(state=TaskState.completed)
            )
        
        return GetTaskResponse(
            root=GetTaskSuccessResponse(
                id=request.id,
                result=task
            )
        )
    
    async def on_cancel(
        self, 
        request: CancelTaskRequest
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
        self, 
        request: TaskResubscriptionRequest
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
    skills = [
        AgentSkill(
            id="comprehensive_report",
            name="종합 보고서 작성",
            description="프로젝트 전반에 대한 종합적인 보고서를 작성합니다",
            tags=["report", "documentation", "synthesis", "writing"],
            examples=[
                "AI 프로젝트 구현 보고서",
                "기술 검토 종합 보고서"
            ]
        ),
        AgentSkill(
            id="executive_summary",
            name="경영진 요약",
            description="프로젝트의 핵심 내용을 경영진을 위해 요약합니다",
            tags=["summary", "executive", "management"]
        ),
        AgentSkill(
            id="technical_documentation",
            name="기술 문서화",
            description="프로젝트의 기술적 세부사항을 문서화합니다",
            tags=["technical", "documentation", "architecture"]
        ),
        AgentSkill(
            id="recommendation_report",
            name="권고사항 작성",
            description="프로젝트 진행을 위한 권고사항과 다음 단계를 제시합니다",
            tags=["recommendation", "next-steps", "action-items"]
        )
    ]
    
    # Agent Card 정의
    agent_card = AgentCard(
        name="report_writing_agent",
        description="프로젝트 계획과 연구 결과를 바탕으로 종합 보고서를 작성하는 에이전트",
        url=f"http://localhost:{os.getenv('REPORT_WRITING_AGENT_PORT', '8004')}/",
        version="1.0.0",
        defaultInputModes=["text", "application/json"],
        defaultOutputModes=["text", "application/json"],
        capabilities=AgentCapabilities(
            streaming=True
        ),
        skills=skills,
    )
    
    # Task Store 생성
    task_store = InMemoryTaskStore()
    
    # Request Handler 생성
    request_handler = DefaultRequestHandler(
        agent_executor=ReportWritingAgentExecutor(),
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
    port = int(os.getenv('REPORT_WRITING_AGENT_PORT', '8004'))
    print(f'Report Writing Agent A2A Server starting on port {port}')
    
    uvicorn.run(application, host='0.0.0.0', port=port)