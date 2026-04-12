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


def _get_room_state_data(room: Room) -> dict:
    return room.get_state_data()


async def _broadcast_room_state(room: Room) -> None:
    data = _get_room_state_data(room)
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
    if not game:
        print(f"AI ERROR: Room {room.room_id} has no game instance.")
        room.ai_task = None
        return
    
    # 診斷資訊
    current = game.current_turn
    ai_role = game.get_player_name(AI_PLAYER_ID)
    print(f"AI Check (Room {room.room_id}): Current Turn={current}, AI Role={ai_role}, Room State={room.state}")

    if room.state != "playing":
        print(f"AI Turn skipped: Room is in state '{room.state}' (not 'playing')")
        room.ai_task = None
        return

    if current != ai_role:
        print(f"AI Turn finished: It is currently Player {current}'s turn, not AI ({ai_role}). Waiting for player action...")
        room.ai_task = None
        return

    print(f"AI Turn sequence STARTING for room {room.room_id}")
    try:
        while game.current_turn == ai_role and room.state == "playing":
            print(f"AI is thinking... (Looping while current_turn == {ai_role})")
            await asyncio.sleep(1.5)
            board = game.get_public_board()
            
            print(f"AI calling move generator for role {ai_role}")
            move_str = banqi_ai.get_move(board, ai_role, game.color_table, room_id=room.room_id)
            print(f"AI move generator returned: '{move_str}'")
            
            success = False
            message = ""
            
            if move_str:
                parts = move_str.split()
                try:
                    coords = list(map(int, parts))
                    if len(coords) == 2:
                        success, message = game.action(AI_PLAYER_ID, coords[0], coords[1])
                    elif len(coords) == 4:
                        success, message = game.action(AI_PLAYER_ID, coords[0], coords[1], coords[2], coords[3])
                except Exception as parse_err:
                    message = f"Parse error: {parse_err}"
            
            if success:
                print(f"AI ACTION SUCCESS: {message}")
                await board_sync.broadcast(room.room_id, game.get_public_board())
                await _broadcast_room_state(room)
            else:
                print(f"AI ACTION FAILED ('{move_str}'): {message}. Attempting emergency fallback...")
                fallback_move = banqi_ai._get_fallback_move(board)
                if fallback_move:
                    print(f"AI executing emergency flip: {fallback_move}")
                    f_parts = list(map(int, fallback_move.split()))
                    success, message = game.action(AI_PLAYER_ID, f_parts[0], f_parts[1])
                    if success:
                        await board_sync.broadcast(room.room_id, game.get_public_board())
                        await _broadcast_room_state(room)
                
                if not success:
                    print(f"AI CRITICAL: Both primary and fallback actions failed. Breaking sequence to prevent hang.")
                    break

            status = game.check_game_over()
            if status != "Playing":
                print(f"AI Turn sequence ENDED: Game Over ({status})")
                room.state = "finished"
                room.winner_message = status
                await sio.emit("game_over", {"room_id": room.room_id, "result": status}, room=f"{room.room_id}-board")
                await _broadcast_room_state(room)
                break
            
            # 更新目前狀態，準備下一輪 while 檢查
            current = game.current_turn
            print(f"AI Action cycle complete. Next turn is: {current}")

    except Exception as e:
        print(f"AI EXCEPTION in room {room.room_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        room.ai_task = None
        print(f"AI Sequence EXITED for room {room.room_id}")


def _trigger_ai(room: Room) -> None:
    if room.mode == "ai" and room.ai_task is None:
        room.ai_task = asyncio.create_task(_run_ai_turn(room))


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

        _trigger_ai(room)
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
            _trigger_ai(room)
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
