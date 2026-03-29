import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services.board_sync import BoardSync


@pytest.fixture
def mock_sio():
    sio = AsyncMock()
    return sio


@pytest.fixture
def board_sync(mock_sio):
    return BoardSync(mock_sio)


def valid_board():
    return [
        ["Covered"] * 8,
        ["Covered"] * 8,
        ["Covered"] * 8,
        ["Covered"] * 8,
    ]


class TestBoardSyncDraw:
    def test_draw_success(self, board_sync, mock_sio):
        result = asyncio.get_event_loop().run_until_complete(
            board_sync.draw("room1", valid_board())
        )
        assert result.status == "success"
        assert result.message == "Board state sent"
        assert result.error == ""
        mock_sio.emit.assert_called_once_with(
            "board_update", valid_board(), room="room1-board"
        )

    def test_draw_invalid_row_count(self, board_sync):
        board = [["Covered"] * 8] * 3  # only 3 rows
        result = asyncio.get_event_loop().run_until_complete(
            board_sync.draw("room1", board)
        )
        assert result.status == "fail"
        assert "4 rows" in result.error

    def test_draw_invalid_col_count(self, board_sync):
        board = [
            ["Covered"] * 8,
            ["Covered"] * 5,  # only 5 columns
            ["Covered"] * 8,
            ["Covered"] * 8,
        ]
        result = asyncio.get_event_loop().run_until_complete(
            board_sync.draw("room1", board)
        )
        assert result.status == "fail"
        assert "8 columns" in result.error

    def test_draw_with_mixed_pieces(self, board_sync, mock_sio):
        board = [
            [
                "Covered",
                "Red_King",
                "Null",
                "Black_Soldier",
                "Covered",
                "Covered",
                "Covered",
                "Covered",
            ],
            ["Covered"] * 8,
            ["Covered"] * 8,
            ["Covered"] * 8,
        ]
        result = asyncio.get_event_loop().run_until_complete(
            board_sync.draw("room42", board)
        )
        assert result.status == "success"
        mock_sio.emit.assert_called_once_with(
            "board_update", board, room="room42-board"
        )

    def test_draw_emit_failure(self, board_sync, mock_sio):
        mock_sio.emit.side_effect = Exception("Connection lost")
        result = asyncio.get_event_loop().run_until_complete(
            board_sync.draw("room1", valid_board())
        )
        assert result.status == "fail"
        assert "Connection lost" in result.error
