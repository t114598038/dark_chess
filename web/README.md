# web/

暗棋競技平台的 Web 應用程式，包含 FastAPI 後端與 Vue 3 前端。

詳細說明請參考[專案根目錄 README](../README.md)。

## 快速啟動

### 一鍵部署

```bash
# 在專案根目錄執行
./deploy.sh
```

自動安裝依賴、打包前端、啟動伺服器。部署後訪問 `http://localhost:8000` 即可使用。

按 `Ctrl+C` 停止伺服器。

### 開發模式（前後端分離）

```bash
# 後端
source ../.venv/bin/activate
pip install -r backend/requirements.txt
uvicorn main:combined_app --reload --app-dir backend     # Web :8000 + TCP :8888

# 前端（另開終端）
cd frontend && npm install && npm run dev                  # :5173

# 測試
cd backend && pytest
```

開發模式下前端運行在 `http://localhost:5173`。

## 使用方式

1. **啟動後端與前端**
2. **加入房間**：
   - 開啟前端頁面 `http://localhost:5173`。
   - 輸入房間號碼並選擇模式（PVP 或 AI）。
   - 按下「加入」進入等待大廳。
3. **遊戲開始**：
   - 當人數到齊後，房主按下「開始遊戲」。
   - 若為 AI 模式，Player B 將由伺服器端 AI 自動接管。
4. **進行對局**：
   - 點擊隱藏棋子進行「翻牌」。
   - 點擊己方棋子後再點擊目標位置進行「移動」或「吃子」。

## 終端機 C 語言客戶端 (TCP)

本平台支援 C 語言編寫的 AI 或手動客戶端透過 TCP (:8888) 連線對弈：

```bash
# 在 client_socket 目錄編譯並執行
gcc player_a.c -o player_a.exe -lws2_32
./player_a.exe
```

連線後可使用以下指令：
- `JOIN <room_id>`: 加入房間
- `START`: 開始遊戲（房主限定）
- `x y`: 翻牌 (例如 `1 3`)
- `x1 y1 x2 y2`: 移動/吃子 (例如 `1 3 1 4`)

## 棋子通訊格式 (JSON)

所有狀態更新透過 Socket.IO 與 TCP 同步，格式範例：

```json
{
  "room_id": "123",
  "state": "playing",
  "current_turn_role": "A",
  "board": ["Covered", "Red_King", "Null", ...],
  "color_table": {"A": "Red", "B": "Black"},
  "total_moves": 5
}
```

### 棋子種類
- 未翻開：`Covered`
- 空地：`Null`
- 種類：`King` (帥/將), `Guard` (仕/士), `Elephant` (相/象), `Car` (俥/車), `Horse` (傌/馬), `Cannon` (炮/砲), `Soldier` (兵/卒)
- 前綴：`Red_` 或 `Black_`
