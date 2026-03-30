<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  join: [roomNumber: string]
}>()

defineProps<{
  isConnected: boolean
}>()

const inputRoom = ref('')

function handleJoin() {
  const room = inputRoom.value.trim()
  if (room) {
    emit('join', room)
  }
}
</script>

<template>
  <div class="mb-4 flex items-center gap-2">
    <label for="room-input" class="text-sm font-medium text-gray-700">房間號碼：</label>
    <input
      id="room-input"
      v-model="inputRoom"
      type="text"
      placeholder="輸入房間號碼"
      class="rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-amber-500 focus:ring-1 focus:ring-amber-500 focus:outline-none"
      @keyup.enter="handleJoin"
    />
    <button
      @click="handleJoin"
      :disabled="!inputRoom.trim()"
      class="rounded bg-amber-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:bg-gray-300"
    >
      加入
    </button>
    <span
      class="text-xs"
      :class="isConnected ? 'text-green-600' : 'text-gray-400'"
    >
      {{ isConnected ? '• 已連線' : '• 未連線' }}
    </span>
  </div>
</template>
