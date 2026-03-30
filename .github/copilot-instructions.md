---
description: "Use when working on any file under the /web directory. Provides project overview, folder structure, run commands, agent delegation, and conventions for this Chinese Dark Chess (Banqi) platform."
applyTo: "web/**"
---

# Project Overview

Chinese Dark Chess (Banqi) competition platform. Vue + Vite frontend, FastAPI backend, real-time via Socket.IO.

- Spectators watch live matches by entering a room number in the web UI.
- Participants create rooms to play AI or challenge others via Socket.IO.

**Never edit files under `client_socket/`** — C socket client managed externally.

## Agent Delegation

- Backend → **FastAPI Backend Clean Code Engineer** (`fastapi.agent`)
- Frontend → **Expert Vue.js Frontend Engineer** (`vuejs-expert.agent`)

## Existing Instructions

- **naming-conventions** — `snake_case` backend, `camelCase` frontend; map at boundary.
- **python-venv** — Activate `.venv` before any Python command.

## Structure

```
web/
  backend/              # FastAPI + python-socketio
    main.py             # Entry point, starts TCP server on :8888
    routers/            # API routes (board_router, health_router)
    schemas/            # Pydantic models (board_sync_schema)
    services/           # Business logic (game_engine, auto_ai, board_sync, room_manager)
    sio_server/         # Socket.IO event handlers
    tcp/                # TCP server for C socket clients
    test/               # pytest tests
  frontend/             # Vue 3 + Vite + Tailwind CSS
    src/
      components/       # chessBoard, roomJoin, gameControls
      composables/      # useBoard
      services/         # socketService
    vite.config.ts      # Proxies /socket.io → backend
client_socket/          # C TCP clients for simulation (do not edit)
```

## Run Commands

Prerequisites: Python 3.13+, Node.js 18+. Always activate venv first.

```bash
source .venv/bin/activate

# Backend
pip install -r web/backend/requirements.txt
uvicorn main:combined_app --reload --app-dir web/backend   # :8000

# Frontend
cd web/frontend && npm install && npm run dev               # :5173

# Tests
cd web/backend && pytest
```

### Running Tests

```bash
source .venv/bin/activate
cd web/backend
pytest
```
