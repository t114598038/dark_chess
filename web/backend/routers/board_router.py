from fastapi import APIRouter, Request

from schemas.board_sync_schema import BoardDrawRequest, BoardSyncResponse

router = APIRouter(prefix="/board", tags=["board"])


@router.post("/draw", response_model=BoardSyncResponse)
async def draw_board(request: BoardDrawRequest, req: Request) -> BoardSyncResponse:
    room_manager = req.app.state.room_manager
    board_sync = req.app.state.board_sync

    room = room_manager.get_room(request.room_number)
    if not room or not room.game:
        return BoardSyncResponse(
            status="fail",
            message="",
            error=f"Room {request.room_number} has no active game",
        )

    room.game.checkerboard_display = request.board_state
    return await board_sync.draw(request.room_number, request.board_state)
