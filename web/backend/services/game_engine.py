import random
from typing import List, Optional, Tuple

BOARD_ROWS = 4
BOARD_COLS = 8

# 階級定義：帥(7) > 仕(6) > 象(5) > 俥(4) > 傌(3) > 炮(2) > 兵(1)
RANK = {
    'King': 7, 'Guard': 6, 'Elephant': 5, 'Car': 4, 
    'Horse': 3, 'Cannon': 2, 'Soldier': 1
}

PIECE_POOL_INIT = [
    'Red_King', 
    'Red_Guard', 'Red_Guard',
    'Red_Elephant', 'Red_Elephant',
    'Red_Car', 'Red_Car',
    'Red_Horse', 'Red_Horse',
    'Red_Cannon', 'Red_Cannon',
    'Red_Soldier', 'Red_Soldier', 'Red_Soldier', 'Red_Soldier', 'Red_Soldier',
    'Black_King', 
    'Black_Guard', 'Black_Guard',
    'Black_Elephant', 'Black_Elephant',
    'Black_Car', 'Black_Car',
    'Black_Horse', 'Black_Horse',
    'Black_Cannon', 'Black_Cannon',
    'Black_Soldier', 'Black_Soldier', 'Black_Soldier', 'Black_Soldier', 'Black_Soldier'
]

class GameEngine:
    def __init__(self):
        self.checkerboard_display = [['Covered'] * 8 for _ in range(4)]
        self.piece_pool = PIECE_POOL_INIT.copy()
        random.shuffle(self.piece_pool)
        self.color_table = {}  # "A" or "B" -> "Red" or "Black"
        self.move_count_since_action = 0
        self.current_turn = random.choice(["A", "B"])
        self.players = []  # List of player identifiers (e.g., sid or addr)
        self.winner = None

    def register_player(self, player_id: str) -> bool:
        if len(self.players) >= 2:
            return False
        if player_id not in self.players:
            self.players.append(player_id)
        return True

    def get_public_board(self) -> List[List[str]]:
        return self.checkerboard_display

    def get_player_name(self, player_id: str) -> str:
        if player_id in self.players:
            return "A" if self.players.index(player_id) == 0 else "B"
        return "Unknown"

    def action(self, player_id: str, x1: int, y1: int, x2: int = -1, y2: int = -1) -> Tuple[bool, str]:
        status = self.check_game_over()
        if status != "Playing":
            return False, f"Game over: {status}"
        
        name = self.get_player_name(player_id)
        if name == "Unknown":
            return False, "You are not a registered player in this room"

        valid, message = self.isValid(name, x1, y1, x2, y2)
        
        if valid:
            if x2 == -1:
                # 翻牌邏輯
                piece = self.piece_pool.pop()
                self.checkerboard_display[x1][y1] = piece
                
                # 第一次翻牌決定陣營
                if not self.color_table:
                    p_color = piece.split('_')[0]
                    other_name = "B" if name == "A" else "A"
                    self.color_table[name] = p_color
                    self.color_table[other_name] = "Black" if p_color == "Red" else "Red"
                
                self.move_count_since_action = 0 
                res_msg = f"Flipped {piece}"
            else:
                # 移動或吃子邏輯
                target = self.checkerboard_display[x2][y2]
                if target != 'Null':
                    self.move_count_since_action = 0
                    res_msg = f"Ate {target}"
                else:
                    self.move_count_since_action += 1
                    res_msg = "Moved"
                
                self.checkerboard_display[x2][y2] = self.checkerboard_display[x1][y1]
                self.checkerboard_display[x1][y1] = 'Null'
            
            # 切換回合
            self.current_turn = "B" if self.current_turn == "A" else "A"
            
            # 檢查勝負
            status = self.check_game_over()
            if status != "Playing":
                self.winner = status

            return True, res_msg
        
        return False, message

    def isValid(self, name, x1, y1, x2, y2):
        if name != self.current_turn:
            return False, f"Not your turn (Current: {self.current_turn})"

        if not (0 <= x1 < 4 and 0 <= y1 < 8): return False, "Out of bounds"
        if x2 != -1 and not (0 <= x2 < 4 and 0 <= y2 < 8): return False, "Out of bounds"
        
        piece = self.checkerboard_display[x1][y1]
        
        # --- 翻牌邏輯 ---
        if x2 == -1:
            return (piece == 'Covered'), "Can only flip covered pieces"

        # --- 移動/吃子邏輯 ---
        if piece == 'Covered' or piece == 'Null': return False, "Invalid source"
        
        p_color = self.color_table.get(name)
        if not p_color:
            return False, "Must flip a piece first to determine colors"
            
        if not piece.startswith(p_color): 
            return False, f"Not your piece (You are {p_color})"
        
        target = self.checkerboard_display[x2][y2]
        if target.startswith(p_color): return False, "Cannot eat your own piece"
        
        dist = abs(x1 - x2) + abs(y1 - y2)
        
        # 1. 處理「砲」的特殊規則 (無視階級，隔子跳吃)
        if "Cannon" in piece:
            if target == 'Null':
                return (dist == 1), "Cannon moves 1 step if not eating"
            elif target == 'Covered':
                return False, "Cannon cannot eat unknown pieces"
            else:
                # 跳吃判斷
                if x1 == x2: # 水平
                    count = sum(1 for y in range(min(y1, y2) + 1, max(y1, y2)) if self.checkerboard_display[x1][y] != 'Null')
                elif y1 == y2: # 垂直
                    count = sum(1 for x in range(min(x1, x2) + 1, max(x1, x2)) if self.checkerboard_display[x][y1] != 'Null')
                else:
                    return False, "Cannon must move in straight line to eat"
                
                if count == 1:
                    return True, "Cannon jump-eats"
                return False, "Cannon needs exactly 1 piece to jump over"

        # 2. 一般棋子移動與吃子
        if dist != 1: return False, "Must move 1 step"
        if target == 'Null': return True, "Safe move"
        if target == 'Covered': return False, "Cannot eat covered piece"
        
        p1_type = piece.split('_')[1]
        p2_type = target.split('_')[1]
        
        # 特殊規則：兵吃帥，帥不吃兵
        if p1_type == 'Soldier' and p2_type == 'King': return True, "Soldier eats King"
        if p1_type == 'King' and p2_type == 'Soldier': return False, "King cannot eat Soldier"
        
        # 一般階級比較 (兵(1) 無法吃 砲(2)/馬(3)/車(4) 等，符合規則)
        return (RANK[p1_type] >= RANK[p2_type]), f"Rank too low ({p1_type} vs {p2_type})"

    def check_game_over(self) -> str:
        # 1. 50步和局
        if self.move_count_since_action >= 50:
            return "Draw (50 moves no capture)"
            
        if not self.color_table:
            return "Playing"

        # 2. 統計雙方剩餘棋子 (場上 + 牌堆)
        red_total = 0
        black_total = 0

        # 場上統計
        for row in self.checkerboard_display:
            for p in row:
                if p.startswith('Red_'): red_total += 1
                elif p.startswith('Black_'): black_total += 1
        
        # 牌堆統計
        for p in self.piece_pool:
            if p.startswith('Red_'): red_total += 1
            elif p.startswith('Black_'): black_total += 1

        if red_total == 0:
            winner_name = [name for name, color in self.color_table.items() if color == "Black"][0]
            return f"Player {winner_name} (Black) Win"
        elif black_total == 0:
            winner_name = [name for name, color in self.color_table.items() if color == "Red"][0]
            return f"Player {winner_name} (Red) Win"
            
        return "Playing"
