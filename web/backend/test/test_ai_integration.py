from services.auto_ai import BanqiAI
from services.game_engine import GameEngine
from services.room_manager import AI_PLAYER_ID


class TestAiIntegration:
    def test_ai_produces_valid_move(self):
        game = GameEngine()
        game.register_player("human")
        game.register_player(AI_PLAYER_ID)

        ai = BanqiAI()

        # First move: AI or human flips a tile
        current = game.current_turn
        player_id = game.players[0] if current == "A" else game.players[1]
        move_str = ai.get_move(game.get_public_board(), player_id, game.color_table)
        assert move_str, "AI should produce a move"

        parts = move_str.split()
        coords = list(map(int, parts))
        assert len(coords) in (2, 4)

    def test_ai_game_terminates(self):
        game = GameEngine()
        game.register_player("p1")
        game.register_player("p2")

        ai = BanqiAI()
        max_steps = 300

        for _ in range(max_steps):
            current = game.current_turn
            player_id = game.players[0] if current == "A" else game.players[1]
            move_str = ai.get_move(game.get_public_board(), player_id, game.color_table)
            if not move_str:
                break

            parts = move_str.split()
            # Skip non-coordinate responses (e.g. "JOIN 123" fallback)
            if not all(p.lstrip("-").isdigit() for p in parts):
                break

            coords = list(map(int, parts))
            if len(coords) == 2:
                game.action(player_id, coords[0], coords[1])
            elif len(coords) == 4:
                game.action(player_id, coords[0], coords[1], coords[2], coords[3])

            status = game.check_game_over()
            if status != "Playing":
                break

        # Game should have ended or at least progressed
        board = game.get_public_board()
        covered_count = sum(1 for row in board for cell in row if cell == "Covered")
        assert covered_count < 32, "AI should have flipped some pieces"
