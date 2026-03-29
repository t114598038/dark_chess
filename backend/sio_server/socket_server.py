import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid: str, environ: dict) -> None:
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid: str) -> None:
    print(f"Client disconnected: {sid}")


@sio.event
async def subscribe_board(sid: str, data: dict) -> None:
    room_number = data.get("room_number", "")
    room_name = f"{room_number}-board"
    await sio.enter_room(sid, room_name)
    print(f"Client {sid} joined room: {room_name}")
