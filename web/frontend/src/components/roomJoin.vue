<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  create: [roomId: string, mode: 'ai' | 'pvp']
  spectate: [roomId: string]
}>()

defineProps<{
  isConnected: boolean
}>()

const createRoomId = ref('')
const createMode = ref<'ai' | 'pvp'>('ai')
const spectateRoomId = ref('')

function handleCreate() {
  const id = createRoomId.value.trim()
  if (id) emit('create', id, createMode.value)
}

function handleSpectate() {
  const id = spectateRoomId.value.trim()
  if (id) emit('spectate', id)
}
</script>

<template>
  <div class="w-full max-w-md space-y-4">
    <!-- Connection status -->
    <div class="flex items-center justify-end">
      <span class="text-xs" :class="isConnected ? 'text-green-600' : 'text-gray-400'">
        {{ isConnected ? '• 已連線' : '• 未連線' }}
      </span>
    </div>

    <!-- Create Room -->
    <div class="rounded-lg border border-amber-200 bg-white p-4 shadow-sm">
      <h3 class="mb-3 text-sm font-semibold text-gray-700">建立房間</h3>
      <div class="flex flex-col gap-3">
        <input
          v-model="createRoomId"
          type="text"
          placeholder="房間號碼"
          class="rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-amber-500 focus:ring-1 focus:ring-amber-500 focus:outline-none"
          @keyup.enter="handleCreate"
        />
        <div class="flex items-center gap-4">
          <label class="flex items-center gap-1.5 text-sm text-gray-600">
            <input v-model="createMode" type="radio" value="ai" class="accent-amber-600" />
            對戰電腦
          </label>
          <label class="flex items-center gap-1.5 text-sm text-gray-600">
            <input v-model="createMode" type="radio" value="pvp" class="accent-amber-600" />
            玩家對戰
          </label>
        </div>
        <button
          @click="handleCreate"
          :disabled="!createRoomId.trim()"
          class="rounded bg-amber-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:bg-gray-300"
        >
          建立房間
        </button>
      </div>
    </div>

    <!-- Spectate Room -->
    <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h3 class="mb-3 text-sm font-semibold text-gray-700">觀戰模式</h3>
      <div class="flex gap-2">
        <input
          v-model="spectateRoomId"
          type="text"
          placeholder="房間號碼"
          class="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-gray-400 focus:ring-1 focus:ring-gray-400 focus:outline-none"
          @keyup.enter="handleSpectate"
        />
        <button
          @click="handleSpectate"
          :disabled="!spectateRoomId.trim()"
          class="rounded bg-gray-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-gray-700 disabled:cursor-not-allowed disabled:bg-gray-300"
        >
          觀戰
        </button>
      </div>
    </div>
  </div>
</template>
