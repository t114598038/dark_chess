import { ref, onUnmounted } from 'vue'
import {
    connectSocket,
    disconnectSocket,
    offAllGameEvents,
    emitCreateRoom,
    emitJoinRoom,
    emitSpectateRoom,
    emitStartGame,
    emitMakeMove,
    emitTerminateMatch,
    emitEndMatch,
    onRoomCreated,
    onRoomState,
    onPlayerJoined,
    onPlayerRole,
    onGameStarted,
    onBoardUpdate,
    onMoveResult,
    onGameOver,
    onPlayerDisconnected,
    onRoomEnded,
    onError,
} from '../services/socketService'

export function useBoard() {
    const boardState = ref<string[][]>([])
    const roomId = ref('')
    const isConnected = ref(false)
    const roomMode = ref<'ai' | 'pvp' | null>(null)
    const roomState = ref<'waiting' | 'playing' | 'finished' | null>(null)
    const playerRole = ref<'player' | 'spectator' | null>(null)
    const playerRoleName = ref<string | null>(null) // 'first' or 'second'
    const isCreator = ref(false)
    const playerCount = ref(0)
    const currentTurn = ref<string | null>(null)
    const currentTurnRole = ref<string | null>(null)
    const gameResult = ref<string | null>(null)
    const opponentDisconnected = ref(false)
    const errorMessage = ref<string | null>(null)
    const selectedPiece = ref<{ x: number; y: number } | null>(null)
    const lastMoveMessage = ref<string | null>(null)

    function setupListeners() {
        const socket = connectSocket()

        socket.on('connect', () => { isConnected.value = true })
        socket.on('disconnect', () => { isConnected.value = false })
        isConnected.value = socket.connected

        onRoomCreated((data) => {
            roomId.value = data.roomId
            roomMode.value = data.mode as 'ai' | 'pvp'
            roomState.value = 'waiting'
            playerRole.value = 'spectator'
            isCreator.value = true
            errorMessage.value = null
        })

        onRoomState((data) => {
            roomState.value = data.state
            roomMode.value = data.mode
            playerCount.value = data.playerCount
            currentTurn.value = data.currentTurn
            currentTurnRole.value = data.currentTurnRole
            if (data.board && data.board.length) {
                boardState.value = data.board
            }
        })

        onPlayerJoined((data) => {
            playerCount.value = data.playerCount
        })

        onPlayerRole((data) => {
            playerRoleName.value = data.role
        })

        onGameStarted((data) => {
            roomState.value = 'playing'
            boardState.value = data.board
            gameResult.value = null
            selectedPiece.value = null
        })

        onBoardUpdate((board) => {
            boardState.value = board
        })

        onMoveResult((data) => {
            lastMoveMessage.value = data.message
            currentTurn.value = data.currentTurn
            // Note: we might want currentTurnRole here too if move_result included it
            if (!data.success) {
                errorMessage.value = data.message
            } else {
                errorMessage.value = null
            }
            selectedPiece.value = null
        })

        onGameOver((data) => {
            roomState.value = 'finished'
            gameResult.value = data.result
            opponentDisconnected.value = false
        })

        onPlayerDisconnected(() => {
            opponentDisconnected.value = true
        })

        onRoomEnded(() => {
            resetState()
        })

        onError((data) => {
            errorMessage.value = data.message
        })
    }

    function createRoom(id: string, mode: 'ai' | 'pvp') {
        setupListeners()
        emitCreateRoom(id, mode)
    }

    function joinRoomAsPlayer(id: string) {
        setupListeners()
        roomId.value = id
        playerRole.value = 'player'
        isCreator.value = false
        emitJoinRoom(id)
    }

    function spectateRoom(id: string) {
        setupListeners()
        roomId.value = id
        playerRole.value = 'spectator'
        isCreator.value = false
        emitSpectateRoom(id)
    }

    function startGame() {
        if (roomId.value) {
            emitStartGame(roomId.value)
        }
    }

    function handleCellClick(rowIndex: number, colIndex: number) {
        if (playerRole.value !== 'player' || roomState.value !== 'playing') return

        const cell = boardState.value[rowIndex]?.[colIndex]
        if (!cell) return

        // clicking a covered piece → flip directly
        if (cell === 'Covered') {
            emitMakeMove(roomId.value, rowIndex, colIndex)
            selectedPiece.value = null
            return
        }

        // if we have a selected piece already
        if (selectedPiece.value) {
            const { x, y } = selectedPiece.value
            // clicking the same piece → deselect
            if (x === rowIndex && y === colIndex) {
                selectedPiece.value = null
                return
            }
            // clicking another target → send move
            emitMakeMove(roomId.value, x, y, rowIndex, colIndex)
            return
        }

        // clicking a piece (not empty and not covered) → select
        if (cell !== 'Null') {
            selectedPiece.value = { x: rowIndex, y: colIndex }
        }
    }

    function terminateMatch() {
        if (roomId.value) {
            emitTerminateMatch(roomId.value)
        }
    }

    function endMatch() {
        if (roomId.value) {
            emitEndMatch(roomId.value)
        }
    }

    function resetState() {
        offAllGameEvents()
        boardState.value = []
        roomId.value = ''
        roomMode.value = null
        roomState.value = null
        playerRole.value = null
        playerRoleName.value = null
        isCreator.value = false
        playerCount.value = 0
        currentTurn.value = null
        currentTurnRole.value = null
        gameResult.value = null
        opponentDisconnected.value = false
        errorMessage.value = null
        selectedPiece.value = null
        lastMoveMessage.value = null
    }

    function leaveRoom() {
        resetState()
        disconnectSocket()
    }

    onUnmounted(() => {
        leaveRoom()
    })

    return {
        boardState,
        roomId,
        isConnected,
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
        lastMoveMessage,
        createRoom,
        joinRoomAsPlayer,
        spectateRoom,
        startGame,
        handleCellClick,
        terminateMatch,
        endMatch,
        leaveRoom,
    }
}
