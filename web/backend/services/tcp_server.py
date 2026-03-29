import asyncio
import socketio
from typing import Dict
from .game_engine import GameEngine

class GameManager:
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self.games: Dict[str, GameEngine] = {}
        self.room_clients: Dict[str, list] = {} # room_number -> [reader, writer]

    def get_or_create_game(self, room_number: str) -> GameEngine:
        if room_number not in self.games:
            self.games[room_number] = GameEngine()
        return self.games[room_number]

    async def broadcast_board(self, room_number: str):
        game = self.games.get(room_number)
        if game:
            room_name = f"{room_number}-board"
            await self.sio.emit("board_update", game.get_public_board(), room=room_name)

class TcpServer:
    def __init__(self, game_manager: GameManager, host: str = "0.0.0.0", port: int = 8888):
        self.game_manager = game_manager
        self.host = host
        self.port = port
        self.clients = []

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        player_id = f"{addr[0]}:{addr[1]}"
        print(f"TCP Client connected: {player_id}")
        
        room_number = None
        game = None
        
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
                        room_number = parts[1]
                        game = self.game_manager.get_or_create_game(room_number)
                        if game.register_player(player_id):
                            success = True
                            res_msg = f"Joined room {room_number} as Player {len(game.players)}"
                        else:
                            res_msg = f"Room {room_number} is full"
                            room_number = None
                            game = None
                
                elif game and len(parts) == 2:
                    # Flip: x1 y1
                    try:
                        x, y = map(int, parts)
                        success, res_msg = game.action(player_id, x, y)
                    except ValueError:
                        res_msg = "Invalid coordinates"
                
                elif game and len(parts) == 4:
                    # Move: x1 y1 x2 y2
                    try:
                        x1, y1, x2, y2 = map(int, parts)
                        success, res_msg = game.action(player_id, x1, y1, x2, y2)
                    except ValueError:
                        res_msg = "Invalid coordinates"
                
                elif not game:
                    res_msg = "Please join a room first: JOIN <room_number>"
                else:
                    res_msg = "Invalid command format. Use 'x1 y1' or 'x1 y1 x2 y2'"

                response = f"{'SUCCESS' if success else 'FAIL'} {res_msg}\n"
                writer.write(response.encode())
                await writer.drain()
                
                if success and room_number:
                    await self.game_manager.broadcast_board(room_number)
                    
        except Exception as e:
            print(f"TCP Error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"TCP Server started on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()
