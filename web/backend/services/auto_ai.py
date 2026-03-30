import random
from typing import List, Tuple, Optional

class BanqiAI:
    # 階級定義 (Rank)
    RANK = {
        'King': 7, 'Guard': 6, 'Elephant': 5, 'Car': 4, 
        'Horse': 3, 'Cannon': 2, 'Soldier': 1
    }

    def __init__(self):
        self.rows = 4
        self.cols = 8

    def get_move(self, board: List[List[str]], player_name: str, color_table: dict) -> str:
        """
        根據規格書實作的核心決策函式。
        回傳格式: "x y" (翻牌) 或 "x1 y1 x2 y2" (移動/吃子)
        """
        my_color = color_table.get(player_name)
        opp_color = "Black" if my_color == "Red" else "Red" if my_color == "Black" else None

        # 1. 如果尚未決定陣營 (第一手)，優先翻牌 (通常翻中間)
        if not my_color:
            covered_indices = [(r, c) for r in range(self.rows) for c in range(self.cols) if board[r][c] == "Covered"]
            if covered_indices:
                r, c = random.choice(covered_indices)
                return f"{r} {c}"
            return "JOIN 123" # 防呆

        # 2. 獲取所有合法動作並進行評分
        moves = self._get_all_legal_moves(board, my_color, opp_color)
        
        if not moves:
            # 沒有可移動的棋子，嘗試翻牌
            covered_indices = [(r, c) for r in range(self.rows) for c in range(self.cols) if board[r][c] == "Covered"]
            if covered_indices:
                r, c = random.choice(covered_indices)
                return f"{r} {c}"
            return "" # 無路可走

        # 3. 評分策略：吃子價值 > 逃跑 (簡單版) > 翻牌 > 隨機移動
        # 這裡我們按權重排序
        moves.sort(key=lambda x: x[1], reverse=True)
        best_move = moves[0][0]
        
        if len(best_move) == 2:
            return f"{best_move[0]} {best_move[1]}"
        else:
            return f"{best_move[0]} {best_move[1]} {best_move[2]} {best_move[3]}"

    def _get_all_legal_moves(self, board, my_color, opp_color) -> List[Tuple[Tuple, int]]:
        """
        回傳格式: [((x1, y1, x2, y2), score), ...]
        """
        legal_moves = []

        for r in range(self.rows):
            for c in range(self.cols):
                piece = board[r][c]
                if piece == "Covered" or piece == "Null" or not piece.startswith(my_color):
                    continue
                
                p_type = piece.split('_')[1]

                # 檢查移動與吃子
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        target = board[nr][nc]
                        
                        # 移動到空地
                        if target == "Null":
                            legal_moves.append(((r, c, nr, nc), 5)) # 基本移動分
                        
                        # 嘗試吃子 (一般棋子)
                        elif target.startswith(opp_color) and p_type != "Cannon":
                            can_eat, score = self._can_eat(p_type, target.split('_')[1])
                            if can_eat:
                                legal_moves.append(((r, c, nr, nc), score + 100))

                # 特別處理「砲」的跳吃
                if p_type == "Cannon":
                    # 四個方向掃描
                    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        bridge_found = False
                        nr, nc = r + dr, c + dc
                        while 0 <= nr < self.rows and 0 <= nc < self.cols:
                            target = board[nr][nc]
                            if not bridge_found:
                                if target != "Null": # 找到砲架 (無論明暗)
                                    bridge_found = True
                            else:
                                if target != "Null":
                                    if target.startswith(opp_color): # 找到敵方棋子
                                        # 砲可以吃任何等級
                                        target_type = target.split('_')[1]
                                        score = self.RANK.get(target_type, 0) * 10
                                        legal_moves.append(((r, c, nr, nc), score + 150))
                                    break # 砲架後只能跳吃一個，遇到第二個障礙物就停止
                            nr += dr
                            nc += dc

        # 隨機加入翻牌動作作為備選 (權重較低)
        covered_indices = [(r, c) for r in range(self.rows) for c in range(self.cols) if board[r][c] == "Covered"]
        for r, c in covered_indices:
            legal_moves.append(((r, c), 10)) # 翻牌的基本價值高於移動

        return legal_moves

    def _can_eat(self, my_type: str, opp_type: str) -> Tuple[bool, int]:
        """
        根據階級與特殊規則判斷是否可吃子
        """
        # 特殊規則：兵吃帥
        if my_type == 'Soldier' and opp_type == 'King':
            return True, 70
        # 特殊規則：帥不吃兵
        if my_type == 'King' and opp_type == 'Soldier':
            return False, 0
        
        # 一般階級比較
        my_rank = self.RANK.get(my_type, 0)
        opp_rank = self.RANK.get(opp_type, 0)
        
        if my_rank >= opp_rank:
            return True, opp_rank * 10
        
        return False, 0
