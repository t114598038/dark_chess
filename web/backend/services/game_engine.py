import random
from typing import List, Optional, Tuple

BOARD_ROWS = 4
BOARD_COLS = 8

PIECES = [
    "Red_King", "Black_King",
    "Red_Guard", "Red_Guard", "Black_Guard", "Black_Guard",
    "Red_Elephant", "Red_Elephant", "Black_Elephant", "Black_Elephant",
    "Red_Car", "Red_Car", "Black_Car", "Black_Car",
    "Red_Horse", "Red_Horse", "Black_Horse", "Black_Horse",
    "Red_Cannon", "Red_Cannon", "Black_Cannon", "Black_Cannon",
    "Red_Soldier", "Red_Soldier", "Red_Soldier", "Red_Soldier", "Red_Soldier",
    "Black_Soldier", "Black_Soldier", "Black_Soldier", "Black_Soldier", "Black_Soldier"
]

RANK_MAP = {
    "King": 7,
    "Guard": 6,
    "Elephant": 5,
    "Car": 4,
    "Horse": 3,
    "Cannon": 2,
    "Soldier": 1
}

class GameEngine:
    def __init__(self):
        self.board = [["Covered" for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        self.hidden_board = self._initialize_board()
        self.turn = "None"  # Red, Black, or None (before first flip)
        self.no_action_steps = 0
        self.winner = None
        self.players = []  # List of player identifiers (e.g., sid or addr)
        self.player_colors = {} # identifier -> "Red" or "Black"

    def register_player(self, player_id: str) -> bool:
        if len(self.players) >= 2:
            return False
        if player_id not in self.players:
            self.players.append(player_id)
        return True

    def _initialize_board(self) -> List[List[str]]:
        pieces = PIECES.copy()
        random.shuffle(pieces)
        board = []
        for i in range(BOARD_ROWS):
            board.append(pieces[i*BOARD_COLS : (i+1)*BOARD_COLS])
        return board

    def get_public_board(self) -> List[List[str]]:
        return self.board

    def action(self, player_id: str, x1: int, y1: int, x2: int = -1, y2: int = -1) -> Tuple[bool, str]:
        if self.winner:
            return False, f"Game over. Winner: {self.winner}"
        
        if player_id not in self.players:
            return False, "You are not a registered player in this room"

        # If colors are assigned, check if it's this player's turn
        if self.turn != "None":
            assigned_color = self.player_colors.get(player_id)
            if assigned_color and self.turn != assigned_color:
                return False, f"Not your turn (You are {assigned_color}, current turn: {self.turn})"

        # Flip piece
        if x2 == -1 and y2 == -1:
            return self._flip(player_id, x1, y1)
        
        # Move or Eat
        return self._move_or_eat(player_id, x1, y1, x2, y2)

    def _flip(self, player_id: str, x: int, y: int) -> Tuple[bool, str]:
        if not (0 <= x < BOARD_ROWS and 0 <= y < BOARD_COLS):
            return False, "Out of bounds"
        if self.board[x][y] != "Covered":
            return False, "Already flipped"
        
        piece = self.hidden_board[x][y]
        self.board[x][y] = piece
        color = piece.split("_")[0]
        
        # First flip determines player colors
        if self.turn == "None":
            # The player who flips gets THIS color
            self.player_colors[player_id] = color
            # The other player gets the OTHER color
            other_player = [p for p in self.players if p != player_id]
            if other_player:
                self.player_colors[other_player[0]] = "Black" if color == "Red" else "Red"
            
            # After flip, it's the other color's turn
            self.turn = "Black" if color == "Red" else "Red"
        else:
            self.turn = "Black" if self.turn == "Red" else "Red"

        self.no_action_steps = 0
        return True, f"Flipped {piece}"

    def _move_or_eat(self, player_id: str, x1: int, y1: int, x2: int, y2: int) -> Tuple[bool, str]:
        if self.turn == "None":
            return False, "Must flip a piece first to determine colors"
        
        assigned_color = self.player_colors.get(player_id)
        if not assigned_color:
            return False, "Color not assigned"

        if not (0 <= x1 < BOARD_ROWS and 0 <= y1 < BOARD_COLS and 
                0 <= x2 < BOARD_ROWS and 0 <= y2 < BOARD_COLS):
            return False, "Out of bounds"
        
        p1 = self.board[x1][y1]
        if p1 == "Covered" or p1 == "Null":
            return False, "Invalid source"
        
        color1, type1 = p1.split("_")
        if assigned_color != color1:
            return False, f"Cannot move opponent's piece ({color1})"
        
        if self.turn != color1:
            return False, f"Not {color1}'s turn"

        p2 = self.board[x2][y2]
        
        # Move to empty space
        if p2 == "Null":
            if abs(x1 - x2) + abs(y1 - y2) != 1:
                return False, "Can only move 1 step"
            self.board[x2][y2] = p1
            self.board[x1][y1] = "Null"
            self.turn = "Black" if self.turn == "Red" else "Red"
            self.no_action_steps += 1
            self._check_draw()
            return True, "Moved"

        # Eat piece
        if p2 == "Covered":
            return False, "Cannot eat covered piece"
        
        color2, type2 = p2.split("_")
        if color1 == color2:
            return False, "Cannot eat own piece"

        dist = abs(x1 - x2) + abs(y1 - y2)
        
        if type1 == "Cannon":
            # Cannon rules: jump over exactly one piece (covered or flipped)
            count = 0
            if x1 == x2:
                step = 1 if y2 > y1 else -1
                for y in range(y1 + step, y2, step):
                    if self.board[x1][y] != "Null":
                        count += 1
            elif y1 == y2:
                step = 1 if x2 > x1 else -1
                for x in range(x1 + step, x2, step):
                    if self.board[x][y1] != "Null":
                        count += 1
            else:
                return False, "Cannon must move straight"
            
            if count != 1:
                return False, "Cannon must jump over exactly one piece"
        else:
            # Normal pieces: move 1 step
            if dist != 1:
                return False, "Can only move 1 step"
            
            # Rank rules
            r1 = RANK_MAP[type1]
            r2 = RANK_MAP[type2]
            
            if type1 == "King" and type2 == "Soldier":
                return False, "King cannot eat Soldier"
            if type1 == "Soldier" and type2 == "King":
                pass # Soldier can eat King
            elif r1 < r2:
                return False, f"{type1} cannot eat {type2}"

        self.board[x2][y2] = p1
        self.board[x1][y1] = "Null"
        self.turn = "Black" if self.turn == "Red" else "Red"
        self.no_action_steps = 0
        self._check_win()
        return True, f"Ate {p2}"

    def _check_win(self):
        red_exists = any("Red_" in p for row in self.board for p in row)
        black_exists = any("Black_" in p for row in self.board for p in row)
        # Also check covered
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                if self.board[r][c] == "Covered":
                    p = self.hidden_board[r][c]
                    if "Red_" in p: red_exists = True
                    if "Black_" in p: black_exists = True
        
        if not red_exists:
            self.winner = "Black"
        elif not black_exists:
            self.winner = "Red"

    def _check_draw(self):
        if self.no_action_steps >= 50:
            self.winner = "Draw"
