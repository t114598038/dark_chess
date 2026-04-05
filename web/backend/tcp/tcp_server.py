import asyncio
import socketio
import json
from services.auto_ai import BanqiAI
from services.room_manager import RoomManager, Room, AI_PLAYER_ID
from services.board_sync import BoardSync
from sio_server.socket_server import trigger_ai

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

    # --- 關鍵：主動推播給所有連線 (網頁 + TCP) ---
    async def _broadcast_room_state(self, room: Room) -> None:
        data = room.get_state_data()
        # 1. 廣播給網頁 (SIO)
        await self.sio.emit("room_state", data, room=f"{room.room_id}-board")

        # 2. 廣播給 TCP C語言玩家
        if hasattr(room, 'tcp_clients'):
            tcp_message = f"UPDATE {json.dumps(data)}\n" 
            for pid, writer in list(room.tcp_clients.items()):
                try:
                    writer.write(tcp_message.encode())
                    await writer.drain()
                except Exception as e:
                    print(f"TCP Push to {pid} failed: {e}")

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        player_id = f"{addr[0]}:{addr[1]}"
        print(f"TCP Client connected: {player_id}")

        room = None
        try:
            while True:
                data = await reader.read(100)
                if not data: break

                message = data.decode().strip()
                parts = message.split()
                if not parts: continue

                command = parts[0].upper()

                # --- 1. 處理 JOIN ---
                if command == "JOIN":
                    if len(parts) < 2:
                        writer.write(b"FAIL Usage: JOIN <room_id>\n")
                        await writer.drain()
                        continue
                    
                    room_id = parts[1]
                    try:
                        room = self.room_manager.join_room(room_id, player_id)
                        
                        # 註冊 TCP Client 到該房間
                        if not hasattr(room, 'tcp_clients'):
                            room.tcp_clients = {}
                        room.tcp_clients[player_id] = writer
                        
                        # Determine role
                        role = "first" if room.player_sids.index(player_id) == 0 else "second"
                        writer.write(f"SUCCESS Joined room {room_id} ROLE {role}\n".encode())
                        await writer.drain()

                        # 加入後延遲一下再廣播，避免 SUCCESS 和 UPDATE 被黏在一起導致 C Client 漏看
                        await asyncio.sleep(0.1)
                        await self._broadcast_room_state(room)
                    except Exception as e:
                        writer.write(f"FAIL {str(e)}\n".encode())
                        await writer.drain()

                # --- 2. 處理 START ---
                elif command == "START":
                    if room:
                        try:
                            # 1. 啟動遊戲引擎
                            self.room_manager.start_game(room.room_id, player_id)
                            
                            # 2. 立刻廣播
                            await self._broadcast_room_state(room)
                            trigger_ai(room)
                            
                            writer.write(b"SUCCESS Game Started\n")
                            await writer.drain()
                        except Exception as e:
                            writer.write(f"FAIL {str(e)}\n".encode())
                            await writer.drain()
                    else:
                        writer.write(b"FAIL Please JOIN a room first\n")
                        await writer.drain()

                # --- 3. 處理移動邏輯 ---
                elif room and room.game:
                    success = False
                    res_msg = ""
                    try:
                        if len(parts) == 2: # 翻棋
                            x, y = map(int, parts)
                            success, res_msg = room.game.action(player_id, x, y)
                        elif len(parts) == 4: # 移動
                            x1, y1, x2, y2 = map(int, parts)
                            success, res_msg = room.game.action(player_id, x1, y1, x2, y2)
                        else:
                            res_msg = "Invalid command format"

                        status = room.game.check_game_over()

                        # 動作成功則同步給所有人
                        if success:
                            response = f"SUCCESS {res_msg}\n"
                            writer.write(response.encode())
                            await writer.drain()
                            await self._broadcast_room_state(room)
                            trigger_ai(room)
                            
                            if status != "Playing":
                                room.state = "finished"
                                room.winner_message = status
                                await self.sio.emit(
                                    "game_over",
                                    {"room_id": room.room_id, "result": status},
                                    room=f"{room.room_id}-board",
                                )
                                await self._broadcast_room_state(room)
                        else:
                            if status != "Playing":
                                room.state = "finished"
                                room.winner_message = status
                                response = f"FAIL {res_msg} - GAME OVER: {status}\n"
                                writer.write(response.encode())
                                await writer.drain()
                                await self.sio.emit(
                                    "game_over",
                                    {"room_id": room.room_id, "result": status},
                                    room=f"{room.room_id}-board",
                                )
                                await self._broadcast_room_state(room)
                            else:
                                response = f"FAIL {res_msg}\n"
                                writer.write(response.encode())
                                await writer.drain()

                    except Exception as e:
                        writer.write(f"FAIL {str(e)}\n".encode())
                        await writer.drain()
                
                else:
                    writer.write(b"FAIL Unknown command or not in room\n")
                    await writer.drain()

        finally:
            if room and hasattr(room, 'tcp_clients') and player_id in room.tcp_clients:
                del room.tcp_clients[player_id]
                print(f"TCP Client {player_id} removed from room {room.room_id}")
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"TCP Server started on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()
