<script setup lang="ts">
const props = defineProps<{
  boardState: string[][]
  selectedPiece: { x: number; y: number } | null
  interactive: boolean
}>()

const emit = defineEmits<{
  cellClick: [rowIndex: number, colIndex: number]
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

function isSelected(rowIndex: number, colIndex: number): boolean {
  return props.selectedPiece?.x === rowIndex && props.selectedPiece?.y === colIndex
}

function handleClick(rowIndex: number, colIndex: number) {
  if (props.interactive) {
    emit('cellClick', rowIndex, colIndex)
  }
}
</script>

<template>
  <div class="inline-block rounded-lg border-4 border-amber-800 bg-amber-700 p-3 shadow-xl">
    <div v-for="(row, rowIndex) in boardState" :key="rowIndex" class="flex">
      <div
        v-for="(cell, colIndex) in row"
        :key="colIndex"
        class="m-0.5 flex h-18 w-18 items-center justify-center rounded-sm bg-amber-600"
        :class="{ 'cursor-pointer hover:bg-amber-500': interactive }"
        @click="handleClick(rowIndex, colIndex)"
      >
        <!-- Covered piece -->
        <div
          v-if="isCovered(cell)"
          class="flex h-14 w-14 items-center justify-center rounded-full bg-amber-900 shadow-md ring-2 ring-amber-950"
          :class="{ 'ring-4 ring-yellow-400': isSelected(rowIndex, colIndex) }"
        />

        <!-- Red piece -->
        <div
          v-else-if="isRed(cell)"
          class="flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 shadow-md ring-2 ring-red-700"
          :class="{ 'ring-4 ring-yellow-400': isSelected(rowIndex, colIndex) }"
        >
          <span class="text-2xl font-bold text-red-700">{{ getPieceLabel(cell) }}</span>
        </div>

        <!-- Black piece -->
        <div
          v-else-if="isBlack(cell)"
          class="flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 shadow-md ring-2 ring-gray-800"
          :class="{ 'ring-4 ring-yellow-400': isSelected(rowIndex, colIndex) }"
        >
          <span class="text-2xl font-bold text-gray-900">{{ getPieceLabel(cell) }}</span>
        </div>

        <!-- Empty cell -->
        <div
          v-else
          class="flex h-14 w-14 items-center justify-center"
          :class="{ 'rounded-full ring-2 ring-yellow-400 ring-dashed': isSelected(rowIndex, colIndex) }"
        />
      </div>
    </div>
  </div>
</template>
