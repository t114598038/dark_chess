import asyncio
import socketio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from routers.board_router import router as board_router
from routers.health_router import router as health_router
from sio_server.socket_server import sio, room_manager, board_sync, banqi_ai
from tcp.tcp_server import TcpServer


@asynccontextmanager
async def lifespan(app: FastAPI):
    tcp_server = TcpServer(room_manager, board_sync, sio, banqi_ai, port=8888)
    task = asyncio.create_task(tcp_server.start())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Chinese Chess API", lifespan=lifespan)

app.state.room_manager = room_manager
app.state.board_sync = board_sync

app.include_router(health_router)
app.include_router(board_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "FastAPI backend is running with TCP Game Server on port 8888"}


combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
