import asyncio
import signal
import socketio
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from routers.board_router import router as board_router
from routers.health_router import router as health_router
from sio_server.socket_server import sio, room_manager, board_sync, banqi_ai
from tcp.tcp_server import TcpServer

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    tcp_server = TcpServer(room_manager, board_sync, sio, banqi_ai, port=8888)
    task = asyncio.create_task(tcp_server.start())

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(_shutdown(s, task, tcp_server))
        )

    yield

    await tcp_server.stop()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def _shutdown(sig: signal.Signals, task: asyncio.Task, tcp_server: TcpServer):
    await tcp_server.stop()
    task.cancel()
    raise SystemExit(0)


app = FastAPI(title="Chinese Chess API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.room_manager = room_manager
app.state.board_sync = board_sync

app.include_router(health_router)
app.include_router(board_router)

if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")
else:

    @app.get("/")
    def read_root() -> dict[str, str]:
        return {
            "message": "FastAPI backend is running with TCP Game Server on port 8888"
        }


combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
