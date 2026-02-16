from pydantic import BaseModel
class Event(BaseModel):
    user_id: int
    item_id: int
    action: str
