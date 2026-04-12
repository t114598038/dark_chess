import os
import subprocess
import json
import logging
import random
import tempfile
from typing import List, Optional

logger = logging.getLogger(__name__)

class BanqiAI:
    def __init__(self):
        # Paths for the C source and compiled executable
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.c_source = os.path.join(self.current_dir, "move_generator.c")
        self.executable = os.path.join(self.current_dir, "move_generator.exe")
        
        self.rows = 4
        self.cols = 8
        
        # Track last move to prevent oscillation
        self.last_from_idx = -1
        self.last_to_idx = -1
        
        # Try to compile if executable doesn't exist
        self._ensure_compiled()

    def _ensure_compiled(self):
        try:
            logger.info(f"Compiling {self.c_source}...")
            # We always try to compile during initialization to ensure we use the latest code
            subprocess.run(["gcc", self.c_source, "-o", self.executable], check=True, capture_output=True)
            logger.info("Compilation successful.")
        except Exception as e:
            logger.error(f"Failed to compile C AI: {e}. If exe exists, we will still try to use it.")

    def _get_fallback_move(self, board: List[List[str]]) -> str:
        """Simple fallback: Flip a random covered piece."""
        covered = []
        for r in range(self.rows):
            for c in range(self.cols):
                if board[r][c] == "Covered":
                    covered.append((r, c))
        if covered:
            r, c = random.choice(covered)
            print(f"Fallback AI flipping: {r} {c}")
            return f"{r} {c}"
        return ""

    def get_move(self, board: List[List[str]], player_id: str, color_table: dict, room_id: str = "N/A") -> str:
        """
        Executes the compiled C move generator to get the best move.
        """
        role = "A" if player_id == "A" else "B"

        # Flatten board for easier C parsing
        flat_board = []
        for row in board:
            flat_board.extend(row)

        # Use a temporary file to pass state safely
        state_dict = {
            "board": flat_board,
            "color_table": color_table
        }
        
        # Save a permanent debug file so the user can "see" what AI receives
        debug_path = os.path.join(self.current_dir, "last_ai_state.json")
        try:
            with open(debug_path, 'w') as f:
                json.dump(state_dict, f, indent=2)
        except:
            pass

        temp_fd, temp_path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(state_dict, f)

            if not os.path.exists(self.executable):
                self._ensure_compiled()
                if not os.path.exists(self.executable):
                    return self._get_fallback_move(board)

            args = [
                self.executable, 
                temp_path, 
                role, 
                str(self.last_from_idx), 
                str(self.last_to_idx)
            ]
            
            result = subprocess.run(args, capture_output=True, text=True, check=True, encoding='utf-8')
            move_str = result.stdout.strip()
            
            if result.stderr:
                # Log C debug output to stdout so we can see it in backend logs
                print(f"C AI Debug output:\n{result.stderr.strip()}")
            
            if move_str:
                print(f"AI ({role}) decided move: {move_str}")
                # Update last move indices
                parts = move_str.split()
                if len(parts) == 4:
                    self.last_from_idx = int(parts[0]) * 8 + int(parts[1])
                    self.last_to_idx = int(parts[2]) * 8 + int(parts[3])
                else:
                    self.last_from_idx = -1
                    self.last_to_idx = -1
                return move_str
            else:
                print("C AI returned empty move, using fallback.")
                return self._get_fallback_move(board)
            
        except Exception as e:
            print(f"Error calling C AI: {e}. Using fallback.")
            return self._get_fallback_move(board)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
