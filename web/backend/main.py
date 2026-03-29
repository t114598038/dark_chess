import asyncio
import socketio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from routers.board_router import router as board_router
from routers.health_router import router as health_router
from sio_server.socket_server import sio, game_manager
from services.tcp_server import TcpServer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start TCP Server
    tcp_server = TcpServer(game_manager, port=8888)
    task = asyncio.create_task(tcp_server.start())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Chinese Chess API", lifespan=lifespan)

# Attach game_manager to app state for access in routers
app.state.game_manager = game_manager

app.include_router(health_router)
app.include_router(board_router)

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "FastAPI backend is running with TCP Game Server on port 8888"}

combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
