"""새로운 에이전트를 위한 템플릿으로 Copy & Paste 후 사용하세요"""
from typing import Any, ClassVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.store.base import BaseStore

from src.agent.base import BaseAgent, BaseState


class NewAgentTemplate(BaseAgent):
    NODE_NAMES: ClassVar[dict[str, str]] = {
        "DEFAULT": "new_node_function",
    }

    def __init__(
        self,
        model: BaseChatModel,
        state_schema: Any,
        config_schema: Any | None = None,
        input_schema: Any | None = None,
        output_schema: Any | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        store: BaseStore | None = None,
        max_retry_attempts: int = 2,
        agent_name: str | None = None,
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
        """Initialize nodes in the graph"""
        default_node = self.get_node_name("DEFAULT")
        assert default_node is not None, "DEFAULT node name must be defined"
        graph.add_node(default_node, self.new_node_function)

    def init_edges(self, graph: StateGraph):
        """Initialize edges in the graph"""
        default_node = self.get_node_name("DEFAULT")
        assert default_node is not None, "DEFAULT node name must be defined"
        graph.set_entry_point(default_node)
        graph.set_finish_point(default_node)

    async def new_node_function(self, state: BaseState, config: RunnableConfig):
        """새로운 노드 함수 정의(Async)"""
        try:
            pass
        except Exception as e:
            raise e

    def new_conditional_edge(self, state: BaseState, config: RunnableConfig):
        """새로운 조건부 Edge 정의(Sync)"""
        pass
