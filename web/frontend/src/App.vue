<script setup lang="ts">
import ChessBoard from './components/chessBoard.vue'
import RoomJoin from './components/roomJoin.vue'
import GameControls from './components/gameControls.vue'
import { useBoard } from './composables/useBoard'

const {
  boardState,
  isConnected,
  roomId,
  roomMode,
  roomState,
  playerRole,
  playerRoleName,
  isCreator,
  playerCount,
  currentTurn,
  currentTurnRole,
  gameResult,
  opponentDisconnected,
  errorMessage,
  selectedPiece,
  createRoom,
  joinRoomAsPlayer,
  spectateRoom,
  startGame,
  handleCellClick,
  terminateMatch,
  endMatch,
  leaveRoom,
} = useBoard()

const isInRoom = () => !!roomState.value
const isInteractive = () => playerRole.value === 'player' && roomState.value === 'playing'
</script>

<template>
  <div class="flex min-h-screen flex-col items-center bg-gray-100 p-8">
    <h1 class="mb-4 text-3xl font-bold text-gray-800">暗棋</h1>

    <!-- Not in a room → show join/create UI -->
    <RoomJoin
      v-if="!isInRoom()"
      :isConnected="isConnected"
      @create="createRoom"
      @spectate="spectateRoom"
    />

    <!-- In a room → show controls + board -->
    <template v-else>
      <GameControls
        :roomId="roomId"
        :roomState="roomState"
        :roomMode="roomMode"
        :isCreator="isCreator"
        :playerRole="playerRole"
        :playerRoleName="playerRoleName"
        :playerCount="playerCount"
        :currentTurn="currentTurn"
        :currentTurnRole="currentTurnRole"
        :gameResult="gameResult"
        :opponentDisconnected="opponentDisconnected"
        :errorMessage="errorMessage"
        @startGame="startGame"
        @terminateMatch="terminateMatch"
        @endMatch="endMatch"
        @leaveRoom="leaveRoom"
        class="mb-4"
      />

      <ChessBoard
        v-if="boardState.length"
        :boardState="boardState"
        :selectedPiece="selectedPiece"
        :interactive="isInteractive()"
        @cellClick="handleCellClick"
      />
      <p v-else class="mt-6 text-gray-400">等待棋盤更新...</p>
    </template>
  </div>
</template>
