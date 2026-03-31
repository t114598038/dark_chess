import asyncio
from dataclasses import dataclass, field
from typing import Literal

from services.game_engine import GameEngine

AI_PLAYER_ID = "AI_PLAYER"


@dataclass
class Room:
    room_id: str
    mode: Literal["ai", "pvp"]
    state: Literal["waiting", "playing", "finished"] = "waiting"
    creator_sid: str = ""
    player_sids: list[str] = field(default_factory=list)
    spectator_sids: set[str] = field(default_factory=set)
    game: GameEngine | None = None
    winner_message: str = ""
    disconnect_tasks: dict[str, asyncio.Task] = field(default_factory=dict)


class RoomManager:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}

    def create_room(self, room_id: str, mode: str, creator_sid: str) -> Room:
        if room_id in self._rooms:
            raise ValueError(f"Room {room_id} already exists")
        if mode not in ("ai", "pvp"):
            raise ValueError("Mode must be 'ai' or 'pvp'")

        room = Room(room_id=room_id, mode=mode, creator_sid=creator_sid)
        self._rooms[room_id] = room
        return room

    def join_room(self, room_id: str, player_sid: str) -> Room:
        room = self._get_existing_room(room_id)

        if room.state != "waiting":
            raise ValueError(
                f"Room {room_id} is not accepting players (state: {room.state})"
            )

        max_players = 1 if room.mode == "ai" else 2
        if len(room.player_sids) >= max_players:
            raise ValueError(f"Room {room_id} is full")

        if player_sid in room.player_sids:
            raise ValueError("Already joined this room")

        room.player_sids.append(player_sid)
        return room

    def spectate_room(self, room_id: str, sid: str) -> Room:
        room = self._get_existing_room(room_id)
        room.spectator_sids.add(sid)
        return room

    def start_game(self, room_id: str, requester_sid: str) -> Room:
        room = self._get_existing_room(room_id)

        if requester_sid != room.creator_sid:
            raise ValueError("Only the room creator can start the game")

        if room.state != "waiting":
            raise ValueError(f"Cannot start game in state: {room.state}")

        if room.mode == "ai" and len(room.player_sids) < 1:
            raise ValueError("Need 1 player to start an AI game")

        if room.mode == "pvp" and len(room.player_sids) < 2:
            raise ValueError("Need 2 players to start a PvP game")

        game = GameEngine()

        for sid in room.player_sids:
            game.register_player(sid)

        if room.mode == "ai":
            game.register_player(AI_PLAYER_ID)

        room.game = game
        room.state = "playing"
        return room

    def terminate_match(self, room_id: str, requester_sid: str) -> Room:
        room = self._get_existing_room(room_id)

        if requester_sid != room.creator_sid:
            raise ValueError("Only the room creator can terminate the match")

        room.state = "finished"
        room.winner_message = "Match terminated by creator"
        self._cancel_disconnect_tasks(room)
        return room

    def end_match(self, room_id: str) -> None:
        room = self._get_existing_room(room_id)

        if room.state != "finished":
            raise ValueError("Can only end a finished match")

        self._cancel_disconnect_tasks(room)
        del self._rooms[room_id]

    def set_disconnect_winner(self, room_id: str, winner_sid: str) -> Room | None:
        room = self._rooms.get(room_id)
        if not room or room.state != "playing":
            return None

        player_name = room.game.get_player_name(winner_sid)
        room.state = "finished"
        room.winner_message = f"Player {player_name} wins (opponent disconnected)"
        return room

    def remove_spectator(self, room_id: str, sid: str) -> None:
        room = self._rooms.get(room_id)
        if room:
            room.spectator_sids.discard(sid)

    def get_room(self, room_id: str) -> Room | None:
        return self._rooms.get(room_id)

    def find_room_by_sid(self, sid: str) -> Room | None:
        for room in self._rooms.values():
            if (
                sid == room.creator_sid
                or sid in room.player_sids
                or sid in room.spectator_sids
            ):
                return room
        return None

    def is_player_in_room(self, room_id: str, sid: str) -> bool:
        room = self._rooms.get(room_id)
        return room is not None and sid in room.player_sids

    def _get_existing_room(self, room_id: str) -> Room:
        room = self._rooms.get(room_id)
        if not room:
            raise ValueError(f"Room {room_id} does not exist")
        return room

    @staticmethod
    def _cancel_disconnect_tasks(room: Room) -> None:
        for task in room.disconnect_tasks.values():
            task.cancel()
        room.disconnect_tasks.clear()
