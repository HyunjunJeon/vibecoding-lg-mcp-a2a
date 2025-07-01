from pydantic import BaseModel
from typing import Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class BaseState(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages]
    
    
class BaseInputState(BaseState):
    ...
    
class BaseOutputState(BaseState):
    ...