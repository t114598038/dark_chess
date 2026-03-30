<script setup lang="ts">
defineProps<{
  roomId: string
  roomState: 'waiting' | 'playing' | 'finished' | null
  roomMode: 'ai' | 'pvp' | null
  isCreator: boolean
  playerRole: 'player' | 'spectator' | null
  playerCount: number
  currentTurn: string | null
  gameResult: string | null
  opponentDisconnected: boolean
  errorMessage: string | null
}>()

const emit = defineEmits<{
  startGame: []
  terminateMatch: []
  endMatch: []
  leaveRoom: []
}>()

function canStart(
  roomState: string | null,
  isCreator: boolean,
  roomMode: string | null,
  playerCount: number
): boolean {
  if (roomState !== 'waiting' || !isCreator) return false
  if (roomMode === 'pvp') return playerCount >= 2
  return true // ai mode: creator is the only player needed
}

function modeLabel(mode: string | null): string {
  if (mode === 'ai') return '對戰電腦'
  if (mode === 'pvp') return '玩家對戰'
  return ''
}

function roleLabel(role: string | null): string {
  if (role === 'player') return '玩家'
  if (role === 'spectator') return '觀戰者'
  return ''
}
</script>

<template>
  <div class="w-full max-w-md space-y-3">
    <!-- Room info bar -->
    <div class="flex items-center justify-between rounded-lg bg-white px-4 py-2 shadow-sm">
      <div class="flex items-center gap-3 text-sm text-gray-600">
        <span>房間：<strong class="text-gray-800">{{ roomId }}</strong></span>
        <span class="rounded bg-gray-100 px-2 py-0.5 text-xs">{{ modeLabel(roomMode) }}</span>
        <span class="rounded bg-gray-100 px-2 py-0.5 text-xs">{{ roleLabel(playerRole) }}</span>
      </div>
      <span class="text-xs text-gray-500">玩家 {{ playerCount }} / {{ roomMode === 'ai' ? 1 : 2 }}</span>
    </div>

    <!-- Turn indicator -->
    <div
      v-if="roomState === 'playing' && currentTurn"
      class="rounded-lg bg-blue-50 px-4 py-2 text-center text-sm text-blue-700"
    >
      當前回合：Player {{ currentTurn }}
    </div>

    <!-- Waiting message -->
    <div
      v-if="roomState === 'waiting' && roomMode === 'pvp' && playerCount < 2"
      class="rounded-lg bg-yellow-50 px-4 py-2 text-center text-sm text-yellow-700"
    >
      等待其他玩家加入...（{{ playerCount }} / 2）
    </div>

    <!-- Opponent disconnected warning -->
    <div
      v-if="opponentDisconnected"
      class="rounded-lg bg-red-50 px-4 py-2 text-center text-sm text-red-700"
    >
      對手已斷線，10 秒內未重連將判定您獲勝
    </div>

    <!-- Game result -->
    <div
      v-if="roomState === 'finished' && gameResult"
      class="rounded-lg bg-green-50 px-4 py-2 text-center text-sm font-semibold text-green-800"
    >
      {{ gameResult }}
    </div>

    <!-- Error message -->
    <div
      v-if="errorMessage"
      class="rounded-lg bg-red-50 px-4 py-2 text-center text-sm text-red-600"
    >
      {{ errorMessage }}
    </div>

    <!-- Action buttons -->
    <div class="flex flex-wrap gap-2">
      <!-- Start game -->
      <button
        v-if="canStart(roomState, isCreator, roomMode, playerCount)"
        @click="emit('startGame')"
        class="rounded bg-green-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-green-700"
      >
        開始比賽
      </button>

      <!-- Terminate match (creator only, during playing) -->
      <button
        v-if="roomState === 'playing' && isCreator"
        @click="emit('terminateMatch')"
        class="rounded bg-red-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-red-700"
      >
        終止比賽
      </button>

      <!-- End match (after finished) -->
      <button
        v-if="roomState === 'finished'"
        @click="emit('endMatch')"
        class="rounded bg-gray-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
      >
        結束比賽
      </button>

      <!-- Leave room -->
      <button
        @click="emit('leaveRoom')"
        class="rounded border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100"
      >
        離開房間
      </button>
    </div>
  </div>
</template>
