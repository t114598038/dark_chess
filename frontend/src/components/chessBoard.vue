<script setup lang="ts">
defineProps<{
  boardState: string[][]
}>()

const redPieceMap: Record<string, string> = {
  Red_King: '帥',
  Red_Guard: '仕',
  Red_Elephant: '相',
  Red_Car: '俥',
  Red_Horse: '傌',
  Red_Cannon: '炮',
  Red_Soldier: '兵'
}

const blackPieceMap: Record<string, string> = {
  Black_King: '將',
  Black_Guard: '士',
  Black_Elephant: '象',
  Black_Car: '車',
  Black_Horse: '馬',
  Black_Cannon: '砲',
  Black_Soldier: '卒'
}

function getPieceLabel(cell: string): string {
  if (cell === 'Covered') return ''
  if (cell === 'Null') return ''
  return redPieceMap[cell] ?? blackPieceMap[cell] ?? cell
}

function isRed(cell: string): boolean {
  return cell.startsWith('Red_')
}

function isBlack(cell: string): boolean {
  return cell.startsWith('Black_')
}

function isCovered(cell: string): boolean {
  return cell === 'Covered'
}

function isEmpty(cell: string): boolean {
  return cell === 'Null'
}
</script>

<template>
  <div class="inline-block rounded-lg border-4 border-amber-800 bg-amber-700 p-3 shadow-xl">
    <div v-for="(row, rowIndex) in boardState" :key="rowIndex" class="flex">
      <div
        v-for="(cell, colIndex) in row"
        :key="colIndex"
        class="m-0.5 flex h-18 w-18 items-center justify-center rounded-sm bg-amber-600"
      >
        <!-- Covered piece: solid dark circle -->
        <div
          v-if="isCovered(cell)"
          class="flex h-14 w-14 items-center justify-center rounded-full bg-amber-900 shadow-md ring-2 ring-amber-950"
        />

        <!-- Red piece -->
        <div
          v-else-if="isRed(cell)"
          class="flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 shadow-md ring-2 ring-red-700"
        >
          <span class="text-2xl font-bold text-red-700">{{ getPieceLabel(cell) }}</span>
        </div>

        <!-- Black piece -->
        <div
          v-else-if="isBlack(cell)"
          class="flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 shadow-md ring-2 ring-gray-800"
        >
          <span class="text-2xl font-bold text-gray-900">{{ getPieceLabel(cell) }}</span>
        </div>

        <!-- Empty cell: no piece -->
      </div>
    </div>
  </div>
</template>
