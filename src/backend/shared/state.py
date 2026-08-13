import operator
from typing import Annotated, Any

from pydantic import BaseModel
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

from backend.schemas.chat import ServerActionType
from backend.shared.constants import RouteAction

def add_messages_limited(left: list[AnyMessage], right: list[AnyMessage] | AnyMessage) -> list[AnyMessage]:
    return add_messages(left, right)[-2:]  # type: ignore

class GlobalState(BaseModel):
    # 1. APPEND-ONLY FIELDS (Reducers)
    # The add_messages_limited reducer ensures only the last 2 conversation messages are stored.
    messages: Annotated[list[AnyMessage], add_messages_limited] = []

    # We can also create a custom reducer for lists, like appending new features
    # without deleting the ones the previous agent extracted.
    requirements_list: Annotated[list[str], operator.add] = []

    # 2. OVERWRITE FIELDS (Standard)
    # These hold the current snapshot of the project. Any node returning these keys will overwrite the value.
    project_id: str | None = None
    client_budget: float | None = None
    estimated_cost: float | None = None
    action: ServerActionType | None = None

    # 3. ROUTING/METADATA FIELDS
    # Used by the Supervisor to know who is talking or where to route next.
    active_agent: str | None = None
    next_action: RouteAction | None = None

    def get_updates(self) -> dict[str, Any]:
        """Returns a dict of fields that were explicitly set, preserving raw object values."""
        return {field: getattr(self, field) for field in self.model_fields_set}