import asyncio
import json
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


async def _get_room_state_data(room: Room) -> dict:
    board = room.game.get_public_board() if room.game else []
    
    current_turn_role = room.game.current_turn if room.game else None
    current_turn_id = None
    if room.game and current_turn_role:
        idx = 0 if current_turn_role == "A" else 1
        if idx < len(room.game.players):
            current_turn_id = room.game.players[idx]

    return {
        "room_id": room.room_id,
        "state": room.state,
        "mode": room.mode,
        "player_count": len(room.player_sids),
        "current_turn": current_turn_id,
        "current_turn_role": current_turn_role,
        "board": board,
        "color_table": room.game.color_table if room.game else {},
        "total_moves": room.game.total_moves if room.game else 0,
    }


async def _broadcast_room_state(room: Room) -> None:
    data = await _get_room_state_data(room)
    room_name = f"{room.room_id}-board"
    await sio.emit("room_state", data, room=room_name)

    # Broadcast to TCP clients if any
    if hasattr(room, 'tcp_clients'):
        tcp_message = f"UPDATE {json.dumps(data)}\n"
        for pid, writer in list(room.tcp_clients.items()):
            try:
                writer.write(tcp_message.encode())
                await writer.drain()
            except Exception as e:
                print(f"TCP Push to {pid} failed: {e}")


async def _run_ai_turn(room: Room) -> None:
    game = room.game
    if not game or room.state != "playing":
        return

    while game.current_turn == game.get_player_name(AI_PLAYER_ID):
        await asyncio.sleep(0.8)
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
        await _broadcast_room_state(room)

        status = game.check_game_over()
        if status != "Playing":
            room.state = "finished"
            room.winner_message = status
            await sio.emit(
                "game_over",
                {"room_id": room.room_id, "result": status},
                room=f"{room.room_id}-board",
            )
            await _broadcast_room_state(room)
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
        await sio.emit("player_role", {"role": "first"}, room=sid)
        await _broadcast_room_state(room)
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def join_room(sid: str, data: dict) -> None:
    room_id = data.get("room_id", "")
    try:
        room = room_manager.join_room(room_id, sid)
        await sio.enter_room(sid, f"{room_id}-board")
        
        role = "first" if room.player_sids.index(sid) == 0 else "second"
        await sio.emit("player_role", {"role": role}, room=sid)

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
        # Only send state to the new spectator, don't broadcast to everyone
        state_data = await _get_room_state_data(room)
        await sio.emit("room_state", state_data, room=sid)
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
            await _broadcast_room_state(room)
        elif room.mode == "ai":
            await _run_ai_turn(room)
    else:
        # Even if move failed, check if game over (violation loss)
        if status != "Playing":
            room.state = "finished"
            room.winner_message = status
            await sio.emit(
                "game_over",
                {"room_id": room_id, "result": status},
                room=f"{room_id}-board",
            )
            await _broadcast_room_state(room)
        else:
            await sio.emit("error", {"message": message}, room=sid)


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
