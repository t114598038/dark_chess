---
description: "Use when creating or refactoring backend FastAPI Python code and frontend Vue/TypeScript code. Enforces naming conventions: FastAPI/Python standard naming and camelCase for frontend."
name: "Backend and Frontend Naming Conventions"
applyTo:
  - "web/backend/**/*.py"
  - "web/frontend/**/*.ts"
  - "web/frontend/**/*.tsx"
  - "web/frontend/**/*.js"
  - "web/frontend/**/*.jsx"
  - "web/frontend/**/*.vue"
---

# Naming Conventions

## Backend (Python + FastAPI)

Follow Python and FastAPI naming conventions.

- Files and modules: snake_case, for example game_router.py, room_service.py.
- Functions and methods: snake_case, for example create_room, list_active_games.
- Variables and parameters: snake_case, for example room_id, player_name.
- Classes and Pydantic models: PascalCase, for example RoomCreateRequest, GameStateResponse.
- Constants: UPPER_SNAKE_CASE, for example MAX_PLAYERS_PER_ROOM.
- Router instances: use router as the variable name for APIRouter.
- URL paths: use lowercase with hyphen separators when needed, for example /game-rooms and /match-history.

## Frontend (Vue + TypeScript)

Use camelCase for frontend naming.

- Variables, functions, methods, props, emits, and composable return keys: camelCase.
- File names in frontend source code: camelCase, for example gameRoomApi.ts, useMatchSocket.ts, roomCard.vue.
- Object keys and API mapping fields used in frontend code: camelCase.
- Avoid snake_case and kebab-case in frontend code identifiers unless required by an external API contract.
- Styling: use Tailwind CSS utility classes directly in templates. Prefer Tailwind classes over scoped CSS or inline styles.

## Cross-Layer Rule

- If backend returns snake_case fields, map them to camelCase at the frontend boundary (API client or adapter) before use in UI logic.
