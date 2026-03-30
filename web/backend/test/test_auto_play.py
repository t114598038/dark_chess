import sys
import os
import time

# 將 backend 目錄加入 python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.game_engine import GameEngine
from services.auto_player import auto_play_step

def print_board(board):
    print("-" * 33)
    for row in board:
        print("|", end="")
        for p in row:
            # 簡化顯示名稱
            display = p.replace("Red_", "R-").replace("Black_", "B-").replace("Covered", "???").replace("Null", "   ")
            print(f" {display:4} |", end="")
        print("\n" + "-" * 33)

def run_auto_game():
    game = GameEngine()
    
    # 註冊兩個虛擬玩家
    game.register_player("AI_Player_1")
    game.register_player("AI_Player_2")
    
    print("Game Started!")
    print(f"Initial Turn: {game.current_turn}")
    
    step_count = 0
    max_steps = 200 # 防止無限迴圈
    
    while step_count < max_steps:
        step_count += 1
        print(f"\n--- Step {step_count} ---")
        
        # 執行 AI 動作
        success = auto_play_step(game)
        
        # 印出當前棋盤
        print_board(game.get_public_board())
        
        # 檢查是否結束
        status = game.check_game_over()
        if status != "Playing":
            print(f"\nGAME OVER! Result: {status}")
            break
            
        if not success:
            print("AI could not make a move. Potential stalemate.")
            break
            
        # 稍微停頓方便觀察
        # time.sleep(0.5)

    if step_count >= max_steps:
        print("\nReached max steps. Game terminated.")

if __name__ == "__main__":
    run_auto_game()
