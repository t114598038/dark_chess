# 暗棋 (Dark Chess)

使用 FastAPI + Vue 3 + Socket.IO 實現的即時暗棋棋盤同步系統。

## 專案結構

```
backend/          # FastAPI 後端
frontend/         # Vue 3 + Tailwind CSS 前端
```

## 環境需求

- Python 3.13+
- Node.js 18+
- npm

## 安裝與啟動

### 1. 建立 Python 虛擬環境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 安裝後端依賴

```bash
cd backend
pip install -r requirements.txt
```

### 3. 啟動後端

```bash
cd backend
source ../.venv/bin/activate
uvicorn main:combined_app --reload
```

後端預設運行在 `http://localhost:8000`。

### 4. 安裝前端依賴

```bash
cd frontend
npm install
```

### 5. 啟動前端

```bash
cd frontend
npm run dev
```

前端預設運行在 `http://localhost:5173`。

## 使用方式

1. 開啟前端頁面
2. 輸入房間號碼，按「加入」
3. 透過 API 發送棋盤狀態，前端會即時同步顯示

### 測試棋盤同步

```bash
curl -X POST http://localhost:8000/board/draw \
  -H "Content-Type: application/json" \
  -d '{
    "room_number": "123",
    "board_state": [
      ["Covered","Covered","Covered","Covered","Covered","Covered","Covered","Black_Elephant"],
      ["Covered","Covered","Covered","Covered","Covered","Covered","Covered","Covered"],
      ["Covered","Covered","Covered","Covered","Covered","Covered","Covered","Black_Soldier"],
      ["Covered","Covered","Covered","Covered","Covered","Covered","Covered","Red_King"]
    ]
  }'
```

## 棋子通訊格式

| 狀態   | 代碼          | 範例              |
| ------ | ------------- | ----------------- |
| 未翻開 | `Covered`     | —                 |
| 空地   | `Null`        | —                 |
| 紅方   | `Red_` 前綴   | `Red_King` (帥)   |
| 黑方   | `Black_` 前綴 | `Black_King` (將) |

棋子種類：`King`、`Guard`、`Elephant`、`Car`、`Horse`、`Cannon`、`Soldier`
