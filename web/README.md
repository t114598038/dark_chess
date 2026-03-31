# web/

暗棋競技平台的 Web 應用程式，包含 FastAPI 後端與 Vue 3 前端。

詳細說明請參考[專案根目錄 README](../README.md)。

## 快速啟動

```bash
# 後端
source ../.venv/bin/activate
pip install -r backend/requirements.txt
uvicorn main:combined_app --reload --app-dir backend     # :8000 + TCP :8888

# 前端
cd frontend && npm install && npm run dev                  # :5173

# 測試
cd backend && pytest
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
