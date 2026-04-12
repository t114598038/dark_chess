import asyncio

import socketio

from services.auto_ai import BanqiAI
from services.room_manager import RoomManager, Room, AI_PLAYER_ID
from services.board_sync import BoardSync

DISCONNECT_TIMEOUT_SECONDS = 10


class TcpServer:
    def __init__(
        self,
        room_manager: RoomManager,
        board_sync: BoardSync,
        sio: socketio.AsyncServer,
        banqi_ai: BanqiAI,
        host: str = "0.0.0.0",
        port: int = 8888,
    ):
        self.room_manager = room_manager
        self.board_sync = board_sync
        self.sio = sio
        self.banqi_ai = banqi_ai
        self.host = host
        self.port = port
        self._server: asyncio.Server | None = None

    async def _broadcast_room_state(self, room: Room) -> None:
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
        await self.sio.emit("room_state", data, room=f"{room.room_id}-board")

    async def _run_ai_turn(self, room: Room) -> None:
        game = room.game
        if not game or room.state != "playing":
            return

        while game.current_turn == game.get_player_name(AI_PLAYER_ID):
            await asyncio.sleep(0.5)
            board = game.get_public_board()
            move_str = self.banqi_ai.get_move(board, AI_PLAYER_ID, game.color_table)
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

            await self.board_sync.broadcast(room.room_id, game.get_public_board())
            await self._broadcast_room_state(room)

            status = game.check_game_over()
            if status != "Playing":
                room.state = "finished"
                room.winner_message = status
                await self.sio.emit(
                    "game_over",
                    {"room_id": room.room_id, "result": status},
                    room=f"{room.room_id}-board",
                )
                break

    async def _handle_disconnect_timeout(self, room_id: str, player_id: str) -> None:
        await asyncio.sleep(DISCONNECT_TIMEOUT_SECONDS)
        room = self.room_manager.get_room(room_id)
        if not room or room.state != "playing":
            return

        remaining = [s for s in room.player_sids if s != player_id]
        if remaining:
            winner_sid = remaining[0]
            self.room_manager.set_disconnect_winner(room_id, winner_sid)

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        addr = writer.get_extra_info("peername")
        player_id = f"{addr[0]}:{addr[1]}"
        print(f"TCP Client connected: {player_id}")

        room_id = None
        room = None

        try:
            while True:
                data = await reader.read(100)
                if not data:
                    break

                message = data.decode().strip()
                parts = message.split()

                if not parts:
                    continue

                success = False
                res_msg = ""

                # Handle JOIN command
                if parts[0].upper() == "JOIN":
                    if len(parts) < 2:
                        res_msg = "Usage: JOIN <room_number>"
                    else:
                        room_id = parts[1]
                        try:
                            room_obj = self.room_manager.join_room(room_id, player_id)
                            room = room_obj
                            success = True
                            res_msg = f"Joined room {room_id} as Player {len(room.player_sids)}"
                            await self.sio.emit(
                                "player_joined",
                                {
                                    "room_id": room_id,
                                    "player_count": len(room.player_sids),
                                },
                                room=f"{room_id}-board",
                            )
                            await self._broadcast_room_state(room)
                        except ValueError as e:
                            res_msg = str(e)
                            room_id = None
                            room = None

                elif room and room.game and len(parts) == 2:
                    # Flip: x1 y1
                    try:
                        x, y = map(int, parts)
                        success, res_msg = room.game.action(player_id, x, y)
                    except ValueError:
                        res_msg = "Invalid coordinates"

                elif room and room.game and len(parts) == 4:
                    # Move: x1 y1 x2 y2
                    try:
                        x1, y1, x2, y2 = map(int, parts)
                        success, res_msg = room.game.action(player_id, x1, y1, x2, y2)
                    except ValueError:
                        res_msg = "Invalid coordinates"

                elif not room:
                    res_msg = "Please join a room first: JOIN <room_number>"
                elif not room.game:
                    res_msg = "Game has not started yet"
                else:
                    res_msg = "Invalid command format. Use 'x1 y1' or 'x1 y1 x2 y2'"

                response = f"{'SUCCESS' if success else 'FAIL'} {res_msg}\n"
                writer.write(response.encode())
                await writer.drain()

                if success and room_id and room and room.game:
                    await self.board_sync.broadcast(
                        room_id, room.game.get_public_board()
                    )
                    await self._broadcast_room_state(room)

                    status = room.game.check_game_over()
                    if status != "Playing":
                        room.state = "finished"
                        room.winner_message = status
                        await self.sio.emit(
                            "game_over",
                            {"room_id": room_id, "result": status},
                            room=f"{room_id}-board",
                        )
                    elif room.mode == "ai":
                        await self._run_ai_turn(room)

        except Exception as e:
            print(f"TCP Error: {e}")
        finally:
            # Handle disconnect timeout for active games
            if room and room.state == "playing" and player_id in room.player_sids:
                task = asyncio.create_task(
                    self._handle_disconnect_timeout(room.room_id, player_id)
                )
                room.disconnect_tasks[player_id] = task

            writer.close()
            await writer.wait_closed()

    async def start(self):
        self._server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        print(f"TCP Server started on {self.host}:{self.port}")
        await self._server.serve_forever()

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
