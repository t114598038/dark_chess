import socketio

from schemas.board_sync_schema import BoardSyncResponse

BOARD_ROWS = 4
BOARD_COLS = 8


class BoardSync:
    def __init__(self, sio: socketio.AsyncServer) -> None:
        self._sio = sio

    async def draw(
        self, room_number: str, board_state: list[list[str]]
    ) -> BoardSyncResponse:
        try:
            if len(board_state) != BOARD_ROWS:
                return BoardSyncResponse(
                    status="fail",
                    message="",
                    error=f"Board must have {BOARD_ROWS} rows, got {len(board_state)}",
                )

            for i, row in enumerate(board_state):
                if len(row) != BOARD_COLS:
                    return BoardSyncResponse(
                        status="fail",
                        message="",
                        error=f"Row {i} must have {BOARD_COLS} columns, got {len(row)}",
                    )

            room_name = f"{room_number}-board"
            await self._sio.emit("board_update", board_state, room=room_name)

            return BoardSyncResponse(
                status="success",
                message="Board state sent",
                error="",
            )
        except Exception as e:
            return BoardSyncResponse(
                status="fail",
                message="",
                error=str(e),
            )
