from fastapi import APIRouter, Request

from schemas.board_sync_schema import BoardDrawRequest, BoardSyncResponse
from services.board_sync import BoardSync
from sio_server.socket_server import sio

router = APIRouter(prefix="/board", tags=["board"])

@router.post("/draw", response_model=BoardSyncResponse)
async def draw_board(request: BoardDrawRequest, req: Request) -> BoardSyncResponse:
    game_manager = req.app.state.game_manager
    # Use existing board_sync logic but update game state if needed
    board_sync = BoardSync(sio)
    
    # Also update our game engine state for persistence
    game = game_manager.get_or_create_game(request.room_number)
    game.board = request.board_state
    
    return await board_sync.draw(request.room_number, request.board_state)
