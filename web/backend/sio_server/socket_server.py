import asyncio

import socketio

from services.auto_ai import BanqiAI
from services.board_sync import BoardSync
from services.room_manager import RoomManager, Room, AI_PLAYER_ID

DISCONNECT_TIMEOUT_SECONDS = 10

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
room_manager = RoomManager()
board_sync = BoardSync(sio)
banqi_ai = BanqiAI()


# ── helpers ──────────────────────────────────────────────────────────


async def _broadcast_room_state(room: Room) -> None:
    board = room.game.get_public_board() if room.game else []
    current_turn = room.game.current_turn if room.game else None
    data = {
        "room_id": room.room_id,
        "state": room.state,
        "mode": room.mode,
        "player_count": len(room.player_sids),
        "current_turn": current_turn,
        "board": board,
    }
    room_name = f"{room.room_id}-board"
    await sio.emit("room_state", data, room=room_name)


async def _run_ai_turn(room: Room) -> None:
    game = room.game
    if not game or room.state != "playing":
        return

    while game.current_turn == game.get_player_name(AI_PLAYER_ID):
        await asyncio.sleep(0.5)
        board = game.get_public_board()
        move_str = banqi_ai.get_move(board, AI_PLAYER_ID, game.color_table)
        if not move_str:
            break

        parts = move_str.split()
        coords = list(map(int, parts))
        if len(coords) == 2:
            game.action(AI_PLAYER_ID, coords[0], coords[1])
        elif len(coords) == 4:
            game.action(AI_PLAYER_ID, coords[0], coords[1], coords[2], coords[3])
        else:
            break

        await board_sync.broadcast(room.room_id, game.get_public_board())

        status = game.check_game_over()
        if status != "Playing":
            room.state = "finished"
            room.winner_message = status
            await sio.emit(
                "game_over",
                {"room_id": room.room_id, "result": status},
                room=f"{room.room_id}-board",
            )
            break


async def _handle_disconnect_timeout(room_id: str, disconnected_sid: str) -> None:
    await asyncio.sleep(DISCONNECT_TIMEOUT_SECONDS)
    room = room_manager.get_room(room_id)
    if not room or room.state != "playing":
        return

    remaining = [s for s in room.player_sids if s != disconnected_sid]
    if remaining:
        winner_sid = remaining[0]
        updated = room_manager.set_disconnect_winner(room_id, winner_sid)
        if updated:
            await sio.emit(
                "game_over",
                {"room_id": room_id, "result": updated.winner_message},
                room=f"{room_id}-board",
            )
            await _broadcast_room_state(updated)


# ── Socket.IO events ────────────────────────────────────────────────


@sio.event
async def connect(sid: str, environ: dict) -> None:
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid: str) -> None:
    print(f"Client disconnected: {sid}")
    room = room_manager.find_room_by_sid(sid)
    if not room:
        return

    # spectator leaves
    if sid in room.spectator_sids:
        room_manager.remove_spectator(room.room_id, sid)
        return

    # player disconnects during active game → start timeout
    if room.state == "playing" and sid in room.player_sids:
        await sio.emit(
            "player_disconnected",
            {"room_id": room.room_id},
            room=f"{room.room_id}-board",
        )
        task = asyncio.create_task(_handle_disconnect_timeout(room.room_id, sid))
        room.disconnect_tasks[sid] = task


@sio.event
async def create_room(sid: str, data: dict) -> None:
    room_id = data.get("room_id", "")
    mode = data.get("mode", "")
    try:
        room = room_manager.create_room(room_id, mode, sid)
        await sio.enter_room(sid, f"{room_id}-board")
        await sio.emit("room_created", {"room_id": room_id, "mode": mode}, room=sid)
        await _broadcast_room_state(room)
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def join_room(sid: str, data: dict) -> None:
    room_id = data.get("room_id", "")
    try:
        room = room_manager.join_room(room_id, sid)
        await sio.enter_room(sid, f"{room_id}-board")
        await sio.emit(
            "player_joined",
            {"room_id": room_id, "player_count": len(room.player_sids)},
            room=f"{room_id}-board",
        )
        await _broadcast_room_state(room)
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def spectate_room(sid: str, data: dict) -> None:
    room_id = data.get("room_id", "")
    try:
        room = room_manager.spectate_room(room_id, sid)
        await sio.enter_room(sid, f"{room_id}-board")
        await _broadcast_room_state(room)
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def start_game(sid: str, data: dict) -> None:
    room_id = data.get("room_id", "")
    try:
        room = room_manager.start_game(room_id, sid)
        board = room.game.get_public_board()
        await sio.emit(
            "game_started",
            {"room_id": room_id, "board": board},
            room=f"{room_id}-board",
        )
        await _broadcast_room_state(room)

        if room.mode == "ai":
            await _run_ai_turn(room)
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def make_move(sid: str, data: dict) -> None:
    room_id = data.get("room_id", "")
    room = room_manager.get_room(room_id)
    if not room:
        await sio.emit("error", {"message": f"Room {room_id} does not exist"}, room=sid)
        return

    if room.state != "playing":
        await sio.emit("error", {"message": "Game is not in progress"}, room=sid)
        return

    if sid not in room.player_sids:
        await sio.emit(
            "error", {"message": "You are not a player in this room"}, room=sid
        )
        return

    game = room.game
    x1 = data.get("x1", -1)
    y1 = data.get("y1", -1)
    x2 = data.get("x2", -1)
    y2 = data.get("y2", -1)

    success, message = game.action(sid, x1, y1, x2, y2)

    status = game.check_game_over()
    current_turn = game.current_turn

    await sio.emit(
        "move_result",
        {
            "success": success,
            "message": message,
            "current_turn": current_turn,
            "game_status": status,
        },
        room=sid,
    )

    if success:
        await board_sync.broadcast(room_id, game.get_public_board())
        await _broadcast_room_state(room)

        if status != "Playing":
            room.state = "finished"
            room.winner_message = status
            await sio.emit(
                "game_over",
                {"room_id": room_id, "result": status},
                room=f"{room_id}-board",
            )
        elif room.mode == "ai":
            await _run_ai_turn(room)


@sio.event
async def terminate_match(sid: str, data: dict) -> None:
    room_id = data.get("room_id", "")
    try:
        room = room_manager.terminate_match(room_id, sid)
        await sio.emit(
            "game_over",
            {"room_id": room_id, "result": room.winner_message},
            room=f"{room_id}-board",
        )
        await _broadcast_room_state(room)
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def end_match(sid: str, data: dict) -> None:
    room_id = data.get("room_id", "")
    try:
        room_manager.end_match(room_id)
        await sio.emit("room_ended", {"room_id": room_id}, room=f"{room_id}-board")
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, room=sid)
