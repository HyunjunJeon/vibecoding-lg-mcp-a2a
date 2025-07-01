"""
A2A Agent Executor Template - Based on A2A SDK v0.2.9
This template demonstrates the latest patterns and best practices for implementing A2A agents.
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from uuid import uuid4

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.utils.errors import ServerError
from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    Part,
    TextPart,
    DataPart,
    TaskState,  
    InvalidParamsError,
    InternalError,
)

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Literal
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example State Schema for LangGraph
class AgentState(TypedDict):
    """State schema for the agent's LangGraph workflow"""
    user_input: str
    processing_steps: list[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    require_user_input: bool
    is_complete: bool


# Response Format for structured outputs
class ResponseFormat(BaseModel):
    """Structured response format following A2A patterns"""
    status: Literal['input_required', 'completed', 'error']
    message: str
    data: Optional[Dict[str, Any]] = None
    next_steps: Optional[list[str]] = None


class MyAgentExecutor(AgentExecutor):
    """
    A2A Agent Executor following latest v0.2.9 patterns.
    
    This executor demonstrates:
    - Proper task state management (submitted → working → completed/failed)
    - Streaming updates with proper event handling
    - Error handling with A2A specific error codes
    - Integration with LangGraph for agent logic
    """
    
    def __init__(self):
        """Initialize the agent executor"""
        self.agent = None
        self.graph = None
        self._initialize_lock = asyncio.Lock()
    
    async def _initialize(self):
        """Lazy initialization of agent components"""
        async with self._initialize_lock:
            if self.agent is not None:
                return
                
            logger.info("Initializing agent components...")
            
            # Initialize your LLM here
            # llm = create_your_llm()
            
            # Initialize checkpointer for conversation memory
            self.checkpointer = InMemorySaver()
            
            # Build the LangGraph workflow
            self.graph = self._build_graph()
            
            logger.info("Agent initialization complete")
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("process_input", self._process_input)
        workflow.add_node("execute_task", self._execute_task)
        workflow.add_node("format_response", self._format_response)
        
        # Define edges
        workflow.set_entry_point("process_input")
        workflow.add_edge("process_input", "execute_task")
        workflow.add_edge("execute_task", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _process_input(self, state: AgentState) -> AgentState:
        """Process user input and plan execution"""
        state["processing_steps"].append("Analyzing user input...")
        # Add your input processing logic here
        return state
    
    async def _execute_task(self, state: AgentState) -> AgentState:
        """Execute the main task logic"""
        state["processing_steps"].append("Executing task...")
        # Add your task execution logic here
        state["result"] = {"example": "result"}
        state["is_complete"] = True
        return state
    
    async def _format_response(self, state: AgentState) -> AgentState:
        """Format the final response"""
        state["processing_steps"].append("Formatting response...")
        # Add response formatting logic here
        return state
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute the agent's logic for a given request context.
        
        This method follows the A2A v0.2.9 patterns:
        1. Extract and validate input
        2. Initialize task with proper state transitions
        3. Execute agent logic (potentially streaming)
        4. Handle errors appropriately
        5. Ensure task completion or failure state
        """
        # Ensure agent is initialized
        await self._initialize()
        
        # Create TaskUpdater for managing task state
        task_id = context.task_id or str(uuid4())
        context_id = context.context_id or str(uuid4())
        task_updater = TaskUpdater(event_queue, task_id, context_id)
        
        try:
            # 1. Submit task (creates task in 'submitted' state)
            await task_updater.submit()
            
            # 2. Start work (transitions to 'working' state)
            await task_updater.start_work()
            
            # 3. Extract and validate input
            message_text = self._extract_message_text(context)
            if not message_text:
                raise ServerError(InvalidParamsError(message="No message text provided"))
            
            # 4. Initialize state for LangGraph
            initial_state: AgentState = {
                "user_input": message_text,
                "processing_steps": [],
                "result": None,
                "error": None,
                "require_user_input": False,
                "is_complete": False,
            }
            
            # 5. Execute agent logic with streaming updates
            final_state = None
            step_count = 0
            
            if not self.graph:
                raise ServerError(InternalError(message="Agent graph not initialized"))
            
            async for chunk in self.graph.astream(
                initial_state,
                config={"configurable": {"thread_id": task_id}}
            ):
                step_count += 1
                
                # Send intermediate updates
                if "processing_steps" in chunk and chunk["processing_steps"]:
                    latest_step = chunk["processing_steps"][-1]
                    await task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            parts=[Part(root=TextPart(text=f"Step {step_count}: {latest_step}"))]
                        )
                    )
                
                # Check for user input requirement
                if chunk.get("require_user_input", False):
                    await task_updater.update_status(
                        TaskState.input_required,
                        message=task_updater.new_agent_message(
                            parts=[Part(root=TextPart(text="Additional input required"))]
                        )
                    )
                    return
                
                final_state = chunk
            
            # 6. Process final result
            if not final_state or not final_state.get("is_complete"):
                raise ServerError(InternalError(message="Agent did not complete execution"))
            
            # 7. Send final response
            result_data = final_state.get("result", {})
            summary_text = self._generate_summary(final_state if isinstance(final_state, dict) else {})
            
            parts = [Part(root=TextPart(text=summary_text))]
            if result_data:
                parts.append(Part(root=DataPart(data=result_data)))
            
            # Important: Include 'final' flag for streaming completion
            await task_updater.update_status(
                TaskState.completed,
                message=task_updater.new_agent_message(parts=parts),
                final=True  # This indicates stream end
            )
            
        except ServerError:
            # Re-raise A2A specific errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in agent execution: {str(e)}", exc_info=True)
            
            # Update task to failed state
            await task_updater.update_status(
                TaskState.failed,
                message=task_updater.new_agent_message(
                    parts=[Part(root=TextPart(text=f"Error: {str(e)}"))]
                ),
                final=True
            )
            
            # Raise as InternalError for proper error handling
            raise ServerError(InternalError(message=str(e)))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Request the agent to cancel an ongoing task.
        
        Following A2A v0.2.9 patterns for task cancellation.
        """
        task_id = context.task_id or str(uuid4())
        context_id = context.context_id or str(uuid4())
        task_updater = TaskUpdater(event_queue, task_id, context_id)
        
        try:
            # Attempt to cancel any ongoing operations
            # Add your cancellation logic here
            
            # Update task state to canceled
            await task_updater.update_status(
                TaskState.canceled,
                message=task_updater.new_agent_message(
                    parts=[Part(root=TextPart(text="Task canceled by user request"))]
                ),
                final=True
            )
            
        except Exception as e:
            logger.error(f"Error during task cancellation: {str(e)}", exc_info=True)
            # Even on error, try to mark as canceled
            await task_updater.update_status(
                TaskState.canceled,
                message=task_updater.new_agent_message(
                    parts=[Part(root=TextPart(text=f"Task canceled with error: {str(e)}"))]
                ),
                final=True
            )
    
    def _extract_message_text(self, context: RequestContext) -> Optional[str]:
        """Extract text from message parts"""
        if not context.message or not context.message.parts:
            return None
            
        text_parts = []
        for part in context.message.parts:
            if isinstance(part.root, TextPart):
                text_parts.append(part.root.text)
        
        return " ".join(text_parts) if text_parts else None
    
    def _generate_summary(self, state: Dict[str, Any]) -> str:
        """Generate a summary from the final state"""
        if state.get("error"):
            return f"Task failed: {state['error']}"
        
        steps = state.get("processing_steps", [])
        result = state.get("result", {})
        
        summary = "Task completed successfully.\n"
        if steps:
            summary += f"Completed {len(steps)} steps.\n"
        if result:
            summary += f"Generated {len(result)} results."
        
        return summary


def create_a2a_server(
    agent_executor: AgentExecutor,
    agent_name: str = "My A2A Agent",
    agent_version: str = "1.0.0",
    port: int = 8000,
) -> A2AStarletteApplication:
    """
    Create a complete A2A server with proper configuration.
    
    This follows A2A v0.2.9 patterns for server setup.
    """
    
    # Define agent skills
    skills = [
        AgentSkill(
            id='main_skill',
            name='Main Processing',
            description='Process user requests and generate responses',
            tags=['processing', 'analysis', 'generation'],
            examples=[
                'Analyze this data and provide insights',
                'Generate a report based on the following information'
            ],
        )
    ]
    
    # Define agent capabilities
    capabilities = AgentCapabilities(
        streaming=True,  # Enable streaming responses
        pushNotifications=False,  # Set to True if implementing webhooks
        stateTransitionHistory=True,  # Track state changes
    )
    
    # Create agent card with all required fields
    agent_card = AgentCard(
        name=agent_name,
        description='An A2A agent following v0.2.9 patterns',
        url=f'http://localhost:{port}/',
        version=agent_version,
        defaultInputModes=['text', 'application/json'],
        defaultOutputModes=['text', 'application/json'],
        capabilities=capabilities,
        skills=skills,
        # Authentication configuration (important for production)
        # securitySchemes={
        #     'bearerAuth': {
        #         'type': 'http',
        #         'scheme': 'bearer',
        #         'bearerFormat': 'JWT'
        #     }
        # },
        # security=[{'bearerAuth': []}],
    )
    
    # Create task store (use Redis for production)
    task_store = InMemoryTaskStore()
    
    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
        # Add these for advanced features:
        # queue_manager=YourQueueManager(),
        # push_notifier=YourPushNotifier(),
    )
    
    # Create and return the A2A application
    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )
    
    return app


# Example usage
if __name__ == '__main__':
    import uvicorn
    
    # Create agent executor
    executor = MyAgentExecutor()
    
    # Create A2A server
    app = create_a2a_server(
        agent_executor=executor,
        agent_name="Example A2A Agent",
        agent_version="1.0.0",
        port=8000
    )
    
    # Build the ASGI application
    application = app.build()
    
    # Start the server
    logger.info("Starting A2A Agent Server on port 8000")
    uvicorn.run(application, host='0.0.0.0', port=8000) 