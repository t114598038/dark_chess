暗棋比賽平台 (Dark Chess Competition Platform)這是一個基於 FastAPI 與 Socket 建立的自動化暗棋對戰平台。開發者（學生）可以使用 C 語言撰寫 AI 程式，透過 Socket 連接至平台 Server 進行雙人對弈或與電腦 AI 對戰。🛠 系統架構圖本平台由 Python 核心、FastAPI 網頁服務與 C 語言客戶端組成：程式碼片段
📜 遊戲規則 (Game Rules)本平台嚴格執行以下暗棋規範：開局與顏色：誰先翻開棋子就決定該玩家的陣營顏色 。翻牌限制：棋子必須翻開後才能被移動或被吃 。移動規則：除了「炮/砲」以外，所有棋子一次只能移動一格 。連吃限制：禁止連續吃子（須輪流行動） 。和局判定：若連續 50 步沒有發生「吃子」或「翻牌」動作，判定為和局 。
💻 介面定義 (Interface Definition)
1. 棋盤狀態 (Board State)使用 get_checkboard() 函式可獲得一個 4x8 的二維陣列 ：未翻開：Covered 。空地：Null 。棋子格式：陣營_名稱（例如：Red_King, Black_Soldier） 。
2. 客戶端指令 (Socket Command)學生端 C 程式需透過 Socket 發送座標指令給 Server：翻牌：x1 y1（一組座標） 。移動/吃子：x1 y1 x2 y2（兩組座標） 。驗證機制：Server 呼叫 client_action(name, x1, y1, x2, y2) 檢查行動是否合法 。

🚀 快速啟動 (Quick Start)
1. 安裝環境需求
pip install fastapi uvicorn
2. 啟動平台
python main.py
3. 編譯並執行學生端 AI (以 Windows 為例)
gcc -o player_a.exe player_a.c -lws2_32
./player_a.exe