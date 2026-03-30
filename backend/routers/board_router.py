from fastapi import APIRouter

from schemas.board_sync_schema import BoardDrawRequest, BoardSyncResponse
from services.board_sync import BoardSync
from sio_server.socket_server import sio

router = APIRouter(prefix="/board", tags=["board"])

board_sync = BoardSync(sio)


@router.post("/draw", response_model=BoardSyncResponse)
async def draw_board(request: BoardDrawRequest) -> BoardSyncResponse:
    return await board_sync.draw(request.room_number, request.board_state)
