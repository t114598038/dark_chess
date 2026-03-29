<script setup lang="ts">
import ChessBoard from './components/chessBoard.vue'
import RoomJoin from './components/roomJoin.vue'
import { useBoard } from './composables/useBoard'

const { boardState, isConnected, joinRoom } = useBoard()
</script>

<template>
  <div class="flex min-h-screen flex-col items-center bg-gray-100 p-8">
    <h1 class="mb-4 text-3xl font-bold text-gray-800">暗棋</h1>
    <RoomJoin :isConnected="isConnected" @join="joinRoom" />
    <ChessBoard v-if="boardState.length" :boardState="boardState" />
    <p v-else class="mt-6 text-gray-400">加入房間後等待棋盤更新...</p>
  </div>
</template>
