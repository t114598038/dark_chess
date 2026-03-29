from pydantic import BaseModel


class BoardDrawRequest(BaseModel):
    room_number: str
    board_state: list[list[str]]


class BoardSyncResponse(BaseModel):
    status: str
    message: str
    error: str
