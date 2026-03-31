import pytest

from services.room_manager import RoomManager, AI_PLAYER_ID


@pytest.fixture
def manager() -> RoomManager:
    return RoomManager()


class TestCreateRoom:
    def test_create_ai_room(self, manager: RoomManager):
        room = manager.create_room("r1", "ai", "sid-a")
        assert room.room_id == "r1"
        assert room.mode == "ai"
        assert room.state == "waiting"
        assert room.creator_sid == "sid-a"
        assert room.player_sids == []

    def test_create_pvp_room(self, manager: RoomManager):
        room = manager.create_room("r2", "pvp", "sid-b")
        assert room.mode == "pvp"
        assert room.player_sids == []

    def test_duplicate_room_id_rejected(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        with pytest.raises(ValueError, match="already exists"):
            manager.create_room("r1", "pvp", "sid-b")

    def test_invalid_mode_rejected(self, manager: RoomManager):
        with pytest.raises(ValueError, match="Mode must be"):
            manager.create_room("r1", "invalid", "sid-a")


class TestJoinRoom:
    def test_join_pvp_room(self, manager: RoomManager):
        manager.create_room("r1", "pvp", "sid-a")
        manager.join_room("r1", "sid-b")
        room = manager.join_room("r1", "sid-c")
        assert len(room.player_sids) == 2
        assert "sid-b" in room.player_sids
        assert "sid-c" in room.player_sids

    def test_join_ai_room(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        room = manager.join_room("r1", "sid-b")
        assert len(room.player_sids) == 1
        assert "sid-b" in room.player_sids

    def test_join_nonexistent_room(self, manager: RoomManager):
        with pytest.raises(ValueError, match="does not exist"):
            manager.join_room("nope", "sid-a")

    def test_join_full_pvp_room(self, manager: RoomManager):
        manager.create_room("r1", "pvp", "sid-a")
        manager.join_room("r1", "sid-b")
        manager.join_room("r1", "sid-c")
        with pytest.raises(ValueError, match="full"):
            manager.join_room("r1", "sid-d")

    def test_join_full_ai_room(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        manager.join_room("r1", "sid-b")
        with pytest.raises(ValueError, match="full"):
            manager.join_room("r1", "sid-c")

    def test_join_playing_room_rejected(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        manager.join_room("r1", "sid-b")
        manager.start_game("r1", "sid-a")
        with pytest.raises(ValueError, match="not accepting"):
            manager.join_room("r1", "sid-c")

    def test_duplicate_join_rejected(self, manager: RoomManager):
        manager.create_room("r1", "pvp", "sid-a")
        manager.join_room("r1", "sid-b")
        with pytest.raises(ValueError, match="Already joined"):
            manager.join_room("r1", "sid-b")


class TestSpectateRoom:
    def test_spectate_existing_room(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        room = manager.spectate_room("r1", "spectator-1")
        assert "spectator-1" in room.spectator_sids

    def test_spectate_nonexistent_room(self, manager: RoomManager):
        with pytest.raises(ValueError, match="does not exist"):
            manager.spectate_room("nope", "spectator-1")


class TestStartGame:
    def test_start_ai_game(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        manager.join_room("r1", "sid-player")
        room = manager.start_game("r1", "sid-a")
        assert room.state == "playing"
        assert room.game is not None
        assert len(room.game.players) == 2
        assert AI_PLAYER_ID in room.game.players

    def test_start_pvp_game(self, manager: RoomManager):
        manager.create_room("r1", "pvp", "sid-a")
        manager.join_room("r1", "sid-b")
        manager.join_room("r1", "sid-c")
        room = manager.start_game("r1", "sid-a")
        assert room.state == "playing"
        assert len(room.game.players) == 2

    def test_non_creator_cannot_start(self, manager: RoomManager):
        manager.create_room("r1", "pvp", "sid-a")
        manager.join_room("r1", "sid-b")
        manager.join_room("r1", "sid-c")
        with pytest.raises(ValueError, match="creator"):
            manager.start_game("r1", "sid-b")

    def test_ai_cannot_start_without_player(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        with pytest.raises(ValueError, match="Need 1 player"):
            manager.start_game("r1", "sid-a")

    def test_pvp_cannot_start_without_two_players(self, manager: RoomManager):
        manager.create_room("r1", "pvp", "sid-a")
        manager.join_room("r1", "sid-b")
        with pytest.raises(ValueError, match="Need 2 players"):
            manager.start_game("r1", "sid-a")

    def test_cannot_start_already_playing(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        manager.join_room("r1", "sid-player")
        manager.start_game("r1", "sid-a")
        with pytest.raises(ValueError, match="Cannot start"):
            manager.start_game("r1", "sid-a")


class TestTerminateAndEnd:
    def test_terminate_match(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        manager.join_room("r1", "sid-player")
        manager.start_game("r1", "sid-a")
        room = manager.terminate_match("r1", "sid-a")
        assert room.state == "finished"
        assert "terminated" in room.winner_message.lower()

    def test_non_creator_cannot_terminate(self, manager: RoomManager):
        manager.create_room("r1", "pvp", "sid-a")
        manager.join_room("r1", "sid-b")
        manager.join_room("r1", "sid-c")
        manager.start_game("r1", "sid-a")
        with pytest.raises(ValueError, match="creator"):
            manager.terminate_match("r1", "sid-b")

    def test_end_match_deletes_room(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        manager.join_room("r1", "sid-player")
        manager.start_game("r1", "sid-a")
        manager.terminate_match("r1", "sid-a")
        manager.end_match("r1")
        assert manager.get_room("r1") is None

    def test_end_non_finished_match_rejected(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        manager.join_room("r1", "sid-player")
        manager.start_game("r1", "sid-a")
        with pytest.raises(ValueError, match="finished"):
            manager.end_match("r1")


class TestDisconnect:
    def test_set_disconnect_winner(self, manager: RoomManager):
        manager.create_room("r1", "pvp", "sid-a")
        manager.join_room("r1", "sid-b")
        manager.join_room("r1", "sid-c")
        manager.start_game("r1", "sid-a")
        room = manager.set_disconnect_winner("r1", "sid-b")
        assert room.state == "finished"
        assert "disconnected" in room.winner_message.lower()

    def test_set_disconnect_winner_nonexistent_room(self, manager: RoomManager):
        result = manager.set_disconnect_winner("nope", "sid-a")
        assert result is None


class TestFindRoom:
    def test_find_room_by_creator(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        room = manager.find_room_by_sid("sid-a")
        assert room is not None
        assert room.room_id == "r1"

    def test_find_room_by_player(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        manager.join_room("r1", "sid-player")
        room = manager.find_room_by_sid("sid-player")
        assert room is not None
        assert room.room_id == "r1"

    def test_find_room_by_spectator(self, manager: RoomManager):
        manager.create_room("r1", "ai", "sid-a")
        manager.spectate_room("r1", "spectator-1")
        room = manager.find_room_by_sid("spectator-1")
        assert room is not None
        assert room.room_id == "r1"

    def test_find_room_unknown_sid(self, manager: RoomManager):
        assert manager.find_room_by_sid("unknown") is None
