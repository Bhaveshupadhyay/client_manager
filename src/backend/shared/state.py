import operator
from typing import Annotated

from pydantic import BaseModel
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class GlobalState(BaseModel):
    # 1. APPEND-ONLY FIELDS (Reducers)
    # The add_messages reducer ensures new AI/User messages are appended to the thread.
    messages: Annotated[list[AnyMessage], add_messages]

    # We can also create a custom reducer for lists, like appending new features
    # without deleting the ones the previous agent extracted.
    requirements_list: Annotated[list[str], operator.add]

    # 2. OVERWRITE FIELDS (Standard)
    # These hold the current snapshot of the project. Any node returning these keys will overwrite the value.
    project_id: str | None
    client_budget: int | None
    estimated_cost: int | None

    # 3. ROUTING/METADATA FIELDS
    # Used by the Supervisor to know who is talking or where to route next.
    active_agent: str | None
    next_action: str | None