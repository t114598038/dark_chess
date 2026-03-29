import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

export function connectSocket(): Socket {
    if (!socket) {
        socket = io('http://localhost:8000')
    }
    if (!socket.connected) {
        socket.connect()
    }
    return socket
}

export function disconnectSocket(): void {
    if (socket) {
        socket.disconnect()
        socket = null
    }
}

export function getSocket(): Socket | null {
    return socket
}

export function subscribeBoard(
    roomNumber: string,
    onBoardUpdate: (boardState: string[][]) => void
): void {
    const s = connectSocket()
    s.on('board_update', onBoardUpdate)

    const emitSubscribe = () => {
        s.emit('subscribe_board', { room_number: roomNumber })
    }

    if (s.connected) {
        emitSubscribe()
    } else {
        s.once('connect', emitSubscribe)
    }
}

export function unsubscribeBoard(): void {
    if (socket) {
        socket.off('board_update')
    }
}
