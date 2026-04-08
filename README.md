# 暗棋競技平台 (Chinese Dark Chess / Banqi)

使用 **FastAPI + Vue 3 + Socket.IO** 打造的即時暗棋對弈平台，支援 AI 對戰、雙人對戰與觀戰模式。

## 系統架構

```
┌─────────────────┐     Socket.IO (ws)      ┌──────────────────────┐
│   Vue 3 前端    │ ◄──────────────────────► │   FastAPI 後端       │
│   :5173         │                          │   :8000              │
└─────────────────┘                          │                      │
                                             │  ┌─ sio_server/      │
┌─────────────────┐     TCP :8888            │  │  Socket.IO 事件   │
│  C Socket 客戶端│ ◄──────────────────────► │  ├─ tcp/             │
│  (client_socket)│                          │  │  TCP 遊戲伺服器   │
└─────────────────┘                          │  ├─ services/        │
                                             │  │  game_engine      │
                                             │  │  room_manager     │
                                             │  │  board_sync       │
                                             │  │  auto_ai          │
                                             │  │  move_generator   │
                                             │  └─ routers/         │
                                             │     REST API 路由    │
                                             └──────────────────────┘
```

### 運作方式

1. **後端啟動時**同時開啟 FastAPI HTTP 伺服器 (`:8000`) 與 TCP 遊戲伺服器 (`:8888`)。
2. **Web 使用者**透過前端 Socket.IO 建立房間、加入對戰或觀戰，前端即時接收棋盤更新並渲染。
3. **C 客戶端**透過 TCP 連線加入房間，以文字指令操作翻牌與移動，適合用來模擬 AI 程式對接。
4. **房間機制**：玩家建立房間並選擇模式 (`ai` 或 `pvp`)，等待對手加入後由創建者開始遊戲。
5. **遊戲引擎**處理所有暗棋規則（翻牌、移動、吃子、砲跳吃、勝負判定、50 步和局）。

### 兩種對戰模式

| 模式  | 說明                                                 |
| ----- | ---------------------------------------------------- |
| `ai`  | 玩家 vs 內建 AI，AI 自動回應每一手                   |
| `pvp` | 雙人對戰，兩位玩家透過 Socket.IO 或 TCP 加入同一房間 |

## 專案結構

```
dark_chess/
├── web/
│   ├── backend/                 # FastAPI + python-socketio 後端
│   │   ├── main.py              # 入口，啟動 HTTP (:8000) + TCP (:8888)
│   │   ├── routers/             # REST API 路由
│   │   │   ├── board_router.py  # 棋盤繪製 API
│   │   │   └── health_router.py # 健康檢查
│   │   ├── schemas/             # Pydantic 資料模型
│   │   │   └── board_sync_schema.py
│   │   ├── services/            # 核心業務邏輯
│   │   │   ├── game_engine.py   # 暗棋遊戲引擎（規則、勝負判定）
│   │   │   ├── room_manager.py  # 房間管理（建立、加入、觀戰）
│   │   │   ├── board_sync.py    # 棋盤同步廣播
│   │   │   ├── auto_ai.py       # AI 決策調度器 (負責編譯並調用 move_generator.c )
│   │   │   └── move_generator.c # 核心移動生成引擎 (負責權重與路徑演算)
│   │   ├── sio_server/          # Socket.IO 事件處理
│   │   │   └── socket_server.py
│   │   ├── tcp/                 # TCP 伺服器（供 C 客戶端連線）
│   │   │   └── tcp_server.py
│   │   └── test/                # pytest 測試
│   └── frontend/                # Vue 3 + Vite + Tailwind CSS 前端
│       ├── src/
│       │   ├── components/      # chessBoard, roomJoin, gameControls
│       │   ├── composables/     # useBoard
│       │   └── services/        # socketService
│       └── vite.config.ts       # 開發代理 /socket.io → :8000
├── client_socket/               # C TCP 客戶端（模擬用，勿編輯）
│   ├── dark_chess_client.h      # 通訊封裝文件(包含連線、加入房間邏輯)
│   ├── player_a.c               # Windows 版本
│   ├── player_a_sample.c        # 客戶端開發範本 (Windows 基礎框架)
│   └── player_mac.c             # macOS 版本(簡單指令輸入版本)
└── README.md
```

## 環境需求

- Python 3.13+
- Node.js 18+
- GCC（編譯 C 客戶端用）

## 安裝與啟動

### 1. 建立 Python 虛擬環境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 啟動後端

```bash
source .venv/bin/activate
pip install -r web/backend/requirements.txt
uvicorn main:combined_app --reload --app-dir web/backend
```

後端運行於 `http://localhost:8000`，同時開啟 TCP 伺服器於 `:8888`。

### 3. 啟動前端

```bash
cd web/frontend
npm install
npm run dev
```

前端運行於 `http://localhost:5173`，自動代理 Socket.IO 請求到後端。

### 4. 執行測試

```bash
source .venv/bin/activate
cd web/backend
pytest
```

## 使用 C 客戶端模擬對戰 (client_socket)

`client_socket/` 提供 C 語言的 TCP 客戶端，連線到後端的 TCP 伺服器 (`:8888`)，可以模擬玩家操作或對接自訂 AI 程式。

### 編譯與執行

**macOS / Linux：**

```bash
cd client_socket
gcc player_mac.c -o player_mac
./player_mac
```

**Windows：**

```bash
cd client_socket
gcc player_a.c -o player_a.exe -lws2_32
player_a.exe
```

### TCP 指令格式

連線成功後，使用以下文字指令操作：

| 指令      | 格式              | 說明                                  | 範例       |
| --------- | ----------------- | ------------------------------------- | ---------- |
| 加入房間  | `JOIN <房間號碼>` | 加入指定房間（需先透過 Web 建立房間） | `JOIN 123` |
| 翻牌      | `x y`             | 翻開座標 (x, y) 的蓋住棋子            | `0 3`      |
| 移動/吃子 | `x1 y1 x2 y2`     | 將 (x1, y1) 的棋子移到 (x2, y2)       | `0 3 1 3`  |

### 模擬流程範例

1. **啟動後端**（HTTP + TCP 伺服器）
2. **開啟前端**，在 Web UI 建立房間（例如房間號 `123`，模式選 `pvp`）
3. **執行 C 客戶端**，輸入 `JOIN 123` 加入房間
4. 在 Web 端開始遊戲後，雙方輪流操作
5. C 客戶端收到的回應格式為 `SUCCESS <訊息>` 或 `FAIL <原因>`

### 回應格式

```
SUCCESS Joined room 123 as Player 2
SUCCESS Flipped Red_King
SUCCESS Moved
SUCCESS Ate Black_Soldier
FAIL Not your turn (Current: A)
FAIL Rank too low (Soldier vs Car)
```

## 棋子通訊格式

| 狀態     | 代碼              | 說明                    |
| -------- | ----------------- | ----------------------- |
| 未翻開   | `Covered`         | 棋子尚未翻開            |
| 空地     | `Null`            | 該位置沒有棋子          |
| 紅方棋子 | `Red_` + 棋子名   | 例如 `Red_King`（帥）   |
| 黑方棋子 | `Black_` + 棋子名 | 例如 `Black_King`（將） |

### 棋子種類

| 棋子  | 英文代碼   | 紅方 | 黑方 | 階級      |
| ----- | ---------- | ---- | ---- | --------- |
| 帥/將 | `King`     | 帥   | 將   | 7（最高） |
| 仕/士 | `Guard`    | 仕   | 士   | 6         |
| 相/象 | `Elephant` | 相   | 象   | 5         |
| 俥/車 | `Car`      | 俥   | 車   | 4         |
| 傌/馬 | `Horse`    | 傌   | 馬   | 3         |
| 炮/砲 | `Cannon`   | 炮   | 砲   | 2         |
| 兵/卒 | `Soldier`  | 兵   | 卒   | 1（最低） |

### 特殊規則

- **兵/卒**可以吃**帥/將**，但帥/將不能吃兵/卒
- **炮/砲**移動時走一步，吃子時需隔一個棋子跳吃（無視階級）
- 連續 50 步無吃子則判和局

## API 端點

| 方法   | 路徑          | 說明                             |
| ------ | ------------- | -------------------------------- |
| `GET`  | `/`           | 伺服器狀態                       |
| `GET`  | `/health`     | 健康檢查                         |
| `POST` | `/board/draw` | 手動設定棋盤狀態（需有活躍遊戲） |

## Socket.IO 事件

### 客戶端 → 伺服器

| 事件              | 資料                          | 說明                 |
| ----------------- | ----------------------------- | -------------------- |
| `create_room`     | `{ room_id, mode }`           | 建立房間             |
| `join_room`       | `{ room_id }`                 | 加入房間             |
| `spectate_room`   | `{ room_id }`                 | 觀戰房間             |
| `start_game`      | `{ room_id }`                 | 開始遊戲（僅創建者） |
| `make_move`       | `{ room_id, x1, y1, x2, y2 }` | 翻牌或移動           |
| `terminate_match` | `{ room_id }`                 | 終止比賽（僅創建者） |
| `end_match`       | `{ room_id }`                 | 結束並刪除房間       |

### 伺服器 → 客戶端

| 事件                  | 說明                         |
| --------------------- | ---------------------------- |
| `room_created`        | 房間建立成功                 |
| `room_state`          | 房間狀態更新（含棋盤、回合） |
| `player_joined`       | 玩家加入通知                 |
| `game_started`        | 遊戲開始                     |
| `board_update`        | 棋盤狀態更新                 |
| `move_result`         | 操作結果                     |
| `game_over`           | 遊戲結束                     |
| `player_disconnected` | 玩家斷線                     |
| `room_ended`          | 房間已刪除                   |
| `error`               | 錯誤訊息                     |
