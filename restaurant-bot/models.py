from pydantic import BaseModel
from typing import Optional

class UserAccountContext (BaseModel):
    customer_id : int
    name: str
    tier : str = "basic"
    email: Optional[str] = None

class InputGuardRailOutput(BaseModel):

    is_off_topic : bool
    reason : str

class AgentOutputGuardrail(BaseModel):
    contains_menu_data: bool = False
    contains_order_data: bool = False
    contains_reservation_data: bool = False
    reason: str
class HandoffData (BaseModel):
    to_agent_name : str
    issue_type:str
    issue_description:str
    reason:str
