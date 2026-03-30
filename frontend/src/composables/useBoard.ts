import { ref, onUnmounted } from 'vue'
import {
    connectSocket,
    subscribeBoard,
    unsubscribeBoard,
    disconnectSocket
} from '../services/socketService'

export function useBoard() {
    const boardState = ref<string[][]>([])
    const roomNumber = ref('')
    const isConnected = ref(false)

    function joinRoom(room: string) {
        leaveRoom()
        roomNumber.value = room

        const socket = connectSocket()

        socket.on('connect', () => {
            isConnected.value = true
        })
        socket.on('disconnect', () => {
            isConnected.value = false
        })

        isConnected.value = socket.connected

        subscribeBoard(room, (data: string[][]) => {
            boardState.value = data
        })
    }

    function leaveRoom() {
        unsubscribeBoard()
        boardState.value = []
        roomNumber.value = ''
    }

    onUnmounted(() => {
        leaveRoom()
        disconnectSocket()
    })

    return {
        boardState,
        roomNumber,
        isConnected,
        joinRoom,
        leaveRoom
    }
}
