import socketio
from fastapi import FastAPI

from routers.board_router import router as board_router
from routers.health_router import router as health_router
from sio_server.socket_server import sio

app = FastAPI(title="Chinese Chess API")

app.include_router(health_router)
app.include_router(board_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "FastAPI backend is running"}


combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
