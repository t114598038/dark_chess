import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

export function connectSocket(): Socket {
    if (!socket) {
        // 動態取得目前的 Host 位址，若在開發模式下則連線到 8000 埠
        const protocol = window.location.protocol
        const hostname = window.location.hostname
        const port = '8000'
        const socketUrl = `${protocol}//${hostname}:${port}`
        
        socket = io(socketUrl)
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

// ── Room lifecycle emitters ─────────────────────────────

export function emitCreateRoom(roomId: string, mode: 'ai' | 'pvp'): void {
    connectSocket().emit('create_room', { room_id: roomId, mode })
}

export function emitJoinRoom(roomId: string): void {
    connectSocket().emit('join_room', { room_id: roomId })
}

export function emitSpectateRoom(roomId: string): void {
    connectSocket().emit('spectate_room', { room_id: roomId })
}

export function emitStartGame(roomId: string): void {
    connectSocket().emit('start_game', { room_id: roomId })
}

export function emitMakeMove(
    roomId: string,
    x1: number,
    y1: number,
    x2?: number,
    y2?: number
): void {
    connectSocket().emit('make_move', {
        room_id: roomId,
        x1,
        y1,
        x2: x2 ?? -1,
        y2: y2 ?? -1,
    })
}

export function emitTerminateMatch(roomId: string): void {
    connectSocket().emit('terminate_match', { room_id: roomId })
}

export function emitEndMatch(roomId: string): void {
    connectSocket().emit('end_match', { room_id: roomId })
}

// ── Event listener types ────────────────────────────────

export interface RoomStatePayload {
    roomId: string
    state: 'waiting' | 'playing' | 'finished'
    mode: 'ai' | 'pvp'
    playerCount: number
    currentTurn: string | null
    currentTurnRole: string | null
    board: string[][]
}

export interface MoveResultPayload {
    success: boolean
    message: string
    currentTurn: string
    gameStatus: string
}

export interface GameOverPayload {
    roomId: string
    result: string
}

// ── Listener helpers ────────────────────────────────────

function mapRoomState(data: Record<string, unknown>): RoomStatePayload {
    return {
        roomId: data.room_id as string,
        state: data.state as RoomStatePayload['state'],
        mode: data.mode as RoomStatePayload['mode'],
        playerCount: data.player_count as number,
        currentTurn: (data.current_turn as string) ?? null,
        currentTurnRole: (data.current_turn_role as string) ?? null,
        board: data.board as string[][],
    }
}

function mapMoveResult(data: Record<string, unknown>): MoveResultPayload {
    return {
        success: data.success as boolean,
        message: data.message as string,
        currentTurn: data.current_turn as string,
        gameStatus: data.game_status as string,
    }
}

function mapGameOver(data: Record<string, unknown>): GameOverPayload {
    return {
        roomId: data.room_id as string,
        result: data.result as string,
    }
}

export function onRoomCreated(cb: (data: { roomId: string; mode: string }) => void): void {
    connectSocket().on('room_created', (raw: Record<string, unknown>) => {
        cb({ roomId: raw.room_id as string, mode: raw.mode as string })
    })
}

export function onRoomState(cb: (data: RoomStatePayload) => void): void {
    connectSocket().on('room_state', (raw: Record<string, unknown>) => {
        cb(mapRoomState(raw))
    })
}

export function onPlayerJoined(cb: (data: { roomId: string; playerCount: number }) => void): void {
    connectSocket().on('player_joined', (raw: Record<string, unknown>) => {
        cb({ roomId: raw.room_id as string, playerCount: raw.player_count as number })
    })
}

export function onPlayerRole(cb: (data: { role: string }) => void): void {
    connectSocket().on('player_role', (raw: Record<string, unknown>) => {
        cb({ role: raw.role as string })
    })
}

export function onGameStarted(cb: (data: { roomId: string; board: string[][] }) => void): void {
    connectSocket().on('game_started', (raw: Record<string, unknown>) => {
        cb({ roomId: raw.room_id as string, board: raw.board as string[][] })
    })
}

export function onBoardUpdate(cb: (board: string[][]) => void): void {
    connectSocket().on('board_update', cb)
}

export function onMoveResult(cb: (data: MoveResultPayload) => void): void {
    connectSocket().on('move_result', (raw: Record<string, unknown>) => {
        cb(mapMoveResult(raw))
    })
}

export function onGameOver(cb: (data: GameOverPayload) => void): void {
    connectSocket().on('game_over', (raw: Record<string, unknown>) => {
        cb(mapGameOver(raw))
    })
}

export function onPlayerDisconnected(cb: (data: { roomId: string }) => void): void {
    connectSocket().on('player_disconnected', (raw: Record<string, unknown>) => {
        cb({ roomId: raw.room_id as string })
    })
}

export function onRoomEnded(cb: (data: { roomId: string }) => void): void {
    connectSocket().on('room_ended', (raw: Record<string, unknown>) => {
        cb({ roomId: raw.role as string })
    })
}

export function onError(cb: (data: { message: string }) => void): void {
    connectSocket().on('error', cb)
}

export function offAllGameEvents(): void {
    if (!socket) return
    const events = [
        'room_created', 'room_state', 'player_joined', 'player_role', 'game_started',
        'board_update', 'move_result', 'game_over', 'player_disconnected',
        'room_ended', 'error',
    ]
    for (const e of events) {
        socket.off(e)
    }
}
