
import { useEffect, useMemo, useState } from 'react'
import { Chess, type Square } from 'chess.js'
import { Chessboard, type PieceDropHandlerArgs } from 'react-chessboard'
import './App.css'

const API = 'http://127.0.0.1:8001'
const TOKEN_KEY = 'chess_access_token'

const GAME_OVER = [
  'checkmate',
  'stalemate',
  'threefold_repetition_draw',
  'fifty_move_draw',
  'insufficient_material_draw',
  'threefold_repetition',
  'fifty_move_rule',
  'insufficient_material',
]

type Quality =
  | 'BEST'
  | 'GOOD'
  | 'INACCURACY'
  | 'MISTAKE'
  | 'BLUNDER'
  | 'GREAT'
  | 'BRILLIANT'

interface MoveAnnotation {
  ply: number
  move_number: number
  color: 'w' | 'b'
  san: string
  uci?: string
  fen_before: string
  fen_after: string
  eval_before?: number
  eval_after?: number
  best_move?: string
  best_eval?: number
  played_eval?: number
  centipawn_loss?: number
  quality: Quality
}

interface ReviewData {
  game_id?: number
  engine?: string
  review_depth?: number
  annotations: MoveAnnotation[]
  white_accuracy?: number
  black_accuracy?: number
  opening_name?: string
}

interface ReviewApiResponse {
  game_id?: number
  status?: string
  white_accuracy?: number
  black_accuracy?: number
  opening_name?: string
  error?: string | null
  review?: ReviewData | string | null
  review_json?: ReviewData | string | null
}

interface ApiResponse {
  game_id?: number
  fen: string
  history: string[]
  turn: 'w' | 'b'
  status: string
  moves_played: number
  evaluation?: number
  last_move?: string
  last_move_uci?: string
  winner?: string | null
  ai_score?: number
  ai_stats?: {
    depth?: number
    nodes?: number
    mode?: string
    thinking_time_seconds?: number
  }
}

interface User {
  id?: number
  username?: string
  email?: string
  elo?: number
  rating?: number
  peak_rating?: number
}

interface GameItem {
  id: number
  result?: string
  status?: string
  created_at?: string
  opponent_type?: string
}

const QUALITY_STYLE: Record<Quality, { symbol: string; color: string }> = {
  BRILLIANT: { symbol: '!!', color: '#20c997' },
  GREAT: { symbol: '!', color: '#45a8ff' },
  BEST: { symbol: '★', color: '#a78bfa' },
  GOOD: { symbol: '✓', color: '#69b77b' },
  INACCURACY: { symbol: '?!', color: '#e8bd48' },
  MISTAKE: { symbol: '?', color: '#ef9148' },
  BLUNDER: { symbol: '??', color: '#f05252' },
}

async function request<T>(
  endpoint: string,
  token?: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (!response.ok) {
    const body = await response.text()
    let message = body || `HTTP ${response.status}`

    try {
      const parsed = JSON.parse(body)
      message = parsed.detail || message
    } catch {
      // Keep original error.
    }

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return response.json() as Promise<T>
}

function gameFromResponse(data: ApiResponse): Chess {
  const next = new Chess()

  try {
    for (const san of data.history || []) next.move(san)
    if (next.fen() !== data.fen) next.load(data.fen)
  } catch {
    next.load(data.fen)
  }

  return next
}

function normalizeQuality(value: string): Quality {
  const normalized = value.toUpperCase()

  if (
    normalized === 'BEST' ||
    normalized === 'GOOD' ||
    normalized === 'GREAT' ||
    normalized === 'BRILLIANT' ||
    normalized === 'INACCURACY' ||
    normalized === 'MISTAKE' ||
    normalized === 'BLUNDER'
  ) {
    return normalized
  }

  return 'GOOD'
}

function formatTime(ms: number): string {
  const totalSeconds = Math.ceil(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

function parseReview(value: unknown): ReviewData | null {
  if (!value) return null

  let parsed = value

  if (typeof parsed === 'string') {
    try {
      parsed = JSON.parse(parsed)
    } catch {
      return null
    }
  }

  if (!parsed || typeof parsed !== 'object') return null

  const raw = parsed as Record<string, unknown>
  const rawAnnotations = Array.isArray(raw.annotations)
    ? raw.annotations
    : []

  const annotations: MoveAnnotation[] = rawAnnotations.map(
    (item: any, index: number) => ({
      ply: Number(item.ply ?? index + 1),
      move_number: Number(item.move_number ?? Math.ceil((index + 1) / 2)),
      color: item.color === 'b' ? 'b' : 'w',
      san: String(item.san ?? ''),
      uci: item.uci ? String(item.uci) : undefined,
      fen_before: String(item.fen_before ?? ''),
      fen_after: String(item.fen_after ?? ''),
      eval_before: Number.isFinite(Number(item.eval_before))
        ? Number(item.eval_before)
        : undefined,
      eval_after: Number.isFinite(Number(item.eval_after))
        ? Number(item.eval_after)
        : undefined,
      best_move: item.best_move ? String(item.best_move) : undefined,
      best_eval: Number.isFinite(Number(item.best_eval))
        ? Number(item.best_eval)
        : undefined,
      played_eval: Number.isFinite(Number(item.played_eval))
        ? Number(item.played_eval)
        : undefined,
      centipawn_loss: Number.isFinite(Number(item.centipawn_loss))
        ? Number(item.centipawn_loss)
        : undefined,
      quality: normalizeQuality(String(item.quality ?? 'GOOD')),
    })
  )

  return {
    game_id: Number(raw.game_id) || undefined,
    engine: String(raw.engine ?? 'FORMULON custom engine'),
    review_depth: Number(raw.review_depth) || undefined,
    annotations,
    white_accuracy: Number.isFinite(Number(raw.white_accuracy))
      ? Number(raw.white_accuracy)
      : undefined,
    black_accuracy: Number.isFinite(Number(raw.black_accuracy))
      ? Number(raw.black_accuracy)
      : undefined,
    opening_name: raw.opening_name
      ? String(raw.opening_name)
      : undefined,
  }
}

function getDestination(uci?: string): string | null {
  if (!uci || !/^[a-h][1-8][a-h][1-8][qrbn]?$/i.test(uci)) {
    return null
  }

  return uci.slice(2, 4).toLowerCase()
}

function App() {
  const [token, setToken] = useState(
    () => localStorage.getItem(TOKEN_KEY) || ''
  )

  const [user, setUser] = useState<User | null>(null)
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const [game, setGame] = useState(() => new Chess())
  const [history, setHistory] = useState<string[]>([])
  const [status, setStatus] = useState('Start a new game')
  const [gameStatus, setGameStatus] = useState('playing')
  const [orientation, setOrientation] = useState<'white' | 'black'>('white')
  const [difficulty, setDifficulty] = useState('hard')
  // New states for time control and color selection
  const [timeControl, setTimeControl] = useState('10+0')
  const [colorSelection, setColorSelection] = useState<'white' | 'black' | 'random'>('white')
  // Timer states
  const [whiteTimeMs, setWhiteTimeMs] = useState(600000)
  const [blackTimeMs, setBlackTimeMs] = useState(600000)
  const [lastUpdateTime, setLastUpdateTime] = useState<number>(Date.now())
  const [gameStarted, setGameStarted] = useState(false)

  const [thinking, setThinking] = useState(false)
  const [error, setError] = useState('')
  const [aiScore, setAiScore] = useState<number | null>(null)
  const [aiStats, setAiStats] = useState<ApiResponse['ai_stats'] | null>(null)

  const [annotations, setAnnotations] = useState<MoveAnnotation[]>([])
  const [games, setGames] = useState<GameItem[]>([])
  const [ratingHistory, setRatingHistory] = useState<any[]>([])
  const [showHistory, setShowHistory] = useState(false)

  const [review, setReview] = useState<ReviewData | null>(null)
  const [reviewStatus, setReviewStatus] = useState('')
  const [reviewError, setReviewError] = useState('')
  const [reviewGameId, setReviewGameId] = useState<number | null>(null)
  const [selectedPly, setSelectedPly] = useState(-1)
  const [reviewLoading, setReviewLoading] = useState(false)
  const [showReview, setShowReview] = useState(false)

  const isGameOver = GAME_OVER.includes(gameStatus)

  function updateGame(data: any) {
    setGame(gameFromResponse(data))
    setHistory(data.history || [])
    setGameStatus(data.status)

    // Update clock times from server
    if (data.white_time_ms !== undefined) setWhiteTimeMs(data.white_time_ms)
    if (data.black_time_ms !== undefined) setBlackTimeMs(data.black_time_ms)
    setLastUpdateTime(Date.now())

    // Set board orientation based on player color
    if (data.player_color) {
      setOrientation(data.player_color as 'white' | 'black')
    }

    if (data.ai_score !== undefined) setAiScore(data.ai_score)
    if (data.ai_stats) setAiStats(data.ai_stats)

    // Handle timeout
    if (data.timed_out && data.timeout_winner) {
      if (data.timeout_winner === 'draw') {
        setStatus('DRAW - TIMEOUT (INSUFFICIENT MATERIAL)')
      } else {
        setStatus(`${data.timeout_winner.toUpperCase()} WINS ON TIME!`)
      }
      setGameStarted(false)
    } else if (data.status === 'checkmate') {
      setStatus(data.turn === 'b' ? 'WHITE WINS!' : 'BLACK WINS!')
      setGameStarted(false)
    } else if (data.status === 'stalemate') {
      setStatus('DRAW - STALEMATE')
      setGameStarted(false)
    } else if (data.status.includes('repetition')) {
      setStatus('DRAW - REPETITION')
      setGameStarted(false)
    } else if (data.status.includes('fifty')) {
      setStatus('DRAW - 50 MOVE RULE')
      setGameStarted(false)
    } else if (data.status.includes('insufficient')) {
      setStatus('DRAW - INSUFFICIENT MATERIAL')
      setGameStarted(false)
    } else if (data.status === 'check') {
      setStatus('CHECK!')
    } else {
      // Start the game clock once first move is made
      if (data.moves_played > 0 && !gameStarted) {
        setGameStarted(true)
      }
      setStatus(data.turn === 'w' ? 'Your move' : 'AI to move')
    }

    if (data.game_id) setReviewGameId(data.game_id)
  }

  async function loadProfile(activeToken: string) {
    const profile = await request<User>('/api/profile', activeToken)
    setUser(profile)
  }

  async function loadHistory(activeToken: string) {
    try {
      const [gameData, ratingData] = await Promise.all([
        request<any>('/api/games', activeToken),
        request<any>('/api/rating-history', activeToken),
      ])

      setGames(Array.isArray(gameData) ? gameData : gameData.games || [])
      setRatingHistory(
        Array.isArray(ratingData) ? ratingData : ratingData.history || []
      )
    } catch (err) {
      console.error('History loading failed:', err)
    }
  }

  async function authenticate() {
    setThinking(true)
    setError('')

    try {
      const endpoint = authMode === 'login' ? '/api/login' : '/api/signup'
      const payload = authMode === 'login'
        ? { email, password }
        : { username, email, password }

      const data = await request<any>(endpoint, undefined, {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      const receivedToken = data.access_token || data.token
      if (!receivedToken) throw new Error('Token missing from authentication response')

      localStorage.setItem(TOKEN_KEY, receivedToken)
      setToken(receivedToken)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setThinking(false)
    }
  }

  async function logout() {
    try {
      await request('/api/logout', token, { method: 'POST' })
    } catch (err) {
      console.error(err)
    }

    localStorage.removeItem(TOKEN_KEY)
    setToken('')
    setUser(null)
    setHistory([])
    setGame(new Chess())
    setAnnotations([])
    setReview(null)
  }

  async function newGame() {
    if (!token || thinking) return

    setThinking(true)
    setError('')
    setAiScore(null)
    setAiStats(null)
    setAnnotations([])
    setReview(null)
    setReviewStatus('')
    setReviewError('')
    setReviewGameId(null)
    setSelectedPly(-1)
    setShowReview(false)
    setGameStarted(false)

    // Handle random color selection
    let selectedColor = colorSelection
    if (colorSelection === 'random') {
      selectedColor = Math.random() < 0.5 ? 'white' : 'black'
    }

    try {
      const data = await request<any>('/api/new-game', token, {
        method: 'POST',
        body: JSON.stringify({
          opponent_type: 'ai',
          difficulty,
          player_color: selectedColor,
          time_control: timeControl,
        }),
      })

      updateGame(data)

      // If player is black, AI makes the first move
      if (data.player_color === 'black' && !GAME_OVER.includes(data.status)) {
        setStatus('AI is thinking...')
        const aiResponse = await request<any>('/api/ai-move', token, { method: 'POST' })
        updateGame(aiResponse)
        
        if (GAME_OVER.includes(aiResponse.status)) {
          await loadProfile(token)
          await loadHistory(token)
          if (aiResponse.game_id) {
            await loadReview(aiResponse.game_id)
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start game')
    } finally {
      setThinking(false)
    }
  }

  async function loadReview(gameId: number, activeToken = token) {
    setReviewLoading(true)
    setReviewError('')
    setReviewGameId(gameId)

    try {
      const response = await request<ReviewApiResponse>(
        `/api/games/${gameId}/review`,
        activeToken
      )

      setReviewStatus(String(response.status ?? 'unknown'))

      const parsed = parseReview(response.review ?? response.review_json)

      if (parsed) {
        setReview({
          ...parsed,
          game_id: gameId,
          white_accuracy: response.white_accuracy ?? parsed.white_accuracy,
          black_accuracy: response.black_accuracy ?? parsed.black_accuracy,
          opening_name: response.opening_name ?? parsed.opening_name,
        })
        setAnnotations(parsed.annotations)
      } else {
        setReview(null)
      }

      if (response.error) setReviewError(response.error)
      setShowReview(true)
      setSelectedPly(-1)
    } catch (err) {
      setReviewError(err instanceof Error ? err.message : 'Review loading failed')
      setShowReview(true)
    } finally {
      setReviewLoading(false)
    }
  }

  async function retryReview() {
    if (!reviewGameId) return

    setReviewLoading(true)
    setReviewError('')
    setReviewStatus('pending')

    try {
      await request(
        `/api/games/${reviewGameId}/review/retry`,
        token,
        { method: 'POST' }
      )

      await loadReview(reviewGameId)
    } catch (err) {
      setReviewError(err instanceof Error ? err.message : 'Review retry failed')
    } finally {
      setReviewLoading(false)
    }
  }

  async function processMove(from: Square, to: Square) {
    if (!token || thinking) return

    setThinking(true)
    setError('')

    try {
      const playerResponse = await request<ApiResponse>(
        '/api/move',
        token,
        {
          method: 'POST',
          body: JSON.stringify({
            from_square: from,
            to_square: to,
          }),
        }
      )

      updateGame(playerResponse)

      if (
        playerResponse.turn === 'b' &&
        !GAME_OVER.includes(playerResponse.status)
      ) {
        setStatus('AI is thinking...')

        const aiResponse = await request<ApiResponse>(
          '/api/ai-move',
          token,
          { method: 'POST' }
        )

        updateGame(aiResponse)

        if (GAME_OVER.includes(aiResponse.status)) {
          await loadProfile(token)
          await loadHistory(token)
          if (aiResponse.game_id) {
            await loadReview(aiResponse.game_id)
          }
        }
      } else if (GAME_OVER.includes(playerResponse.status)) {
        await loadProfile(token)
        await loadHistory(token)
        if (playerResponse.game_id) {
          await loadReview(playerResponse.game_id)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Move failed')
    } finally {
      setThinking(false)
    }
  }

  function onDrop({
    sourceSquare,
    targetSquare,
  }: PieceDropHandlerArgs): boolean {
    // Only allow moves if it's the player's turn
    const playerTurn = orientation === 'white' ? 'w' : 'b'
    if (
      !targetSquare ||
      !token ||
      thinking ||
      isGameOver ||
      game.turn() !== playerTurn
    ) return false

    const from = sourceSquare as Square
    const to = targetSquare as Square

    try {
      const test = new Chess(game.fen())
      test.move({ from, to, promotion: 'q' })
    } catch {
      return false
    }

    void processMove(from, to)
    return true
  }

  async function undoMove() {
    if (!token || thinking || history.length === 0) return

    setThinking(true)
    setError('')

    try {
      const data = await request<ApiResponse>('/api/undo', token, {
        method: 'POST',
      })

      updateGame(data)
      setReview(null)
      setReviewStatus('')
      setAnnotations([])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Undo failed')
    } finally {
      setThinking(false)
    }
  }

  // Timer effect to update clocks
  useEffect(() => {
    if (!gameStarted || isGameOver) return

    const interval = setInterval(() => {
      const now = Date.now()
      const elapsed = now - lastUpdateTime
      
      if (elapsed > 0) {
        const currentTurn = game.turn()
        if (currentTurn === 'w') {
          setWhiteTimeMs(prev => Math.max(0, prev - elapsed))
        } else {
          setBlackTimeMs(prev => Math.max(0, prev - elapsed))
        }
        setLastUpdateTime(now)
      }
    }, 100)

    return () => clearInterval(interval)
  }, [gameStarted, isGameOver, game.turn(), lastUpdateTime])

  // Backend clock sync to ensure accuracy - don't rely only on frontend
  useEffect(() => {
    if (!token || !gameStarted || isGameOver) return

    const syncInterval = setInterval(async () => {
      try {
        const data = await request<any>('/api/status', token)
        if (data.white_time_ms !== undefined) setWhiteTimeMs(data.white_time_ms)
        if (data.black_time_ms !== undefined) setBlackTimeMs(data.black_time_ms)
        setLastUpdateTime(Date.now())
        
        // Check for timeout from backend
        if (data.timed_out && data.timeout_winner) {
          updateGame(data)
        }
      } catch (err) {
        console.error('Clock sync failed:', err)
      }
    }, 2000) // Sync every 2 seconds to maintain accuracy

    return () => clearInterval(syncInterval)
  }, [token, gameStarted, isGameOver])

  useEffect(() => {
    if (!token) return

    let cancelled = false

    async function initialize() {
      try {
        await loadProfile(token)
        if (cancelled) return

        await loadHistory(token)
        if (cancelled) return

        await newGame()
      } catch (err) {
        if (cancelled) return

        localStorage.removeItem(TOKEN_KEY)
        setToken('')
        setUser(null)
        setError(err instanceof Error ? err.message : 'Please login again')
      }
    }

    void initialize()

    return () => {
      cancelled = true
    }
  }, [token])

  // Poll while the backend is still generating the review.
  useEffect(() => {
    if (!token || !isGameOver || !reviewGameId) return
    if (reviewStatus === 'completed' || reviewStatus === 'failed') return

    let cancelled = false

    const timer = window.setInterval(async () => {
      try {
        const response = await request<ReviewApiResponse>(
          `/api/games/${reviewGameId}/review`,
          token
        )

        if (cancelled) return

        setReviewStatus(String(response.status ?? 'unknown'))

        const parsed = parseReview(response.review ?? response.review_json)

        if (parsed) {
          setReview({
            ...parsed,
            game_id: reviewGameId,
            white_accuracy: response.white_accuracy ?? parsed.white_accuracy,
            black_accuracy: response.black_accuracy ?? parsed.black_accuracy,
          })
          setAnnotations(parsed.annotations)
        }

        if (response.error) setReviewError(response.error)
      } catch (err) {
        if (!cancelled) {
          setReviewError(err instanceof Error ? err.message : 'Review polling failed')
        }
      }
    }, 2500)

    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [token, isGameOver, reviewGameId, reviewStatus])

  const movePairs: string[][] = []

  for (let i = 0; i < history.length; i += 2) {
    movePairs.push(history.slice(i, i + 2))
  }

  const replayFen = useMemo(() => {
    if (!review || selectedPly < 0) return new Chess().fen()

    return review.annotations[selectedPly]?.fen_after || new Chess().fen()
  }, [review, selectedPly])

  const selectedMove = review && selectedPly >= 0
    ? review.annotations[selectedPly]
    : null

  const graphValues = useMemo(() => {
    if (!review) return []

    return review.annotations.map((move, index) => ({
      x: index,
      value: move.eval_after ?? 0,
    }))
  }, [review])

  function downloadPGN() {
    if (!review) return

    const chess = new Chess()

    for (const move of review.annotations) {
      try {
        chess.move(move.san)
      } catch {
        // Stop using invalid/incomplete SAN entries.
        break
      }
    }

    const pgn = chess.pgn()
    const blob = new Blob([pgn], { type: 'application/x-chess-pgn' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')

    anchor.href = url
    anchor.download = `formulon-game-${review.game_id ?? 'review'}.pgn`
    anchor.click()

    URL.revokeObjectURL(url)
  }

  function annotationPosition(square: string) {
    const file = square.charCodeAt(0) - 97
    const rank = Number(square[1])

    const col = orientation === 'white' ? file : 7 - file
    const row = orientation === 'white' ? 8 - rank : rank - 1

    return {
      left: `${(col + 0.70) * 12.5}%`,
      top: `${(row + 0.04) * 12.5}%`,
    }
  }

  if (!token) {
    return (
      <div className="app auth-screen">
        <div className="auth-card">
          <div className="brand">
            <span className="brand-icon">♟</span>
            <span>FORMULON CHESS</span>
          </div>

          <h1>{authMode === 'login' ? 'Welcome Back' : 'Create Account'}</h1>
          <p>Challenge the intelligence of LSTM + Minimax.</p>

          <form onSubmit={event => {
            event.preventDefault()
            void authenticate()
          }}>
            {authMode === 'signup' && (
              <input
                placeholder="Username"
                value={username}
                onChange={event => setUsername(event.target.value)}
                required
              />
            )}

            <input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={event => setEmail(event.target.value)}
              required
            />

            <input
              type="password"
              placeholder="Password (minimum 8 characters)"
              value={password}
              onChange={event => setPassword(event.target.value)}
              minLength={8}
              required
            />

            {error && <div className="error-message">{error}</div>}

            <button type="submit" disabled={thinking}>
              {thinking ? 'Please wait...' :
                authMode === 'login' ? 'Login' : 'Create Account'}
            </button>
          </form>

          <p>
            {authMode === 'login'
              ? "Don't have an account?"
              : 'Already have an account?'}
            {' '}
            <button
              className="text-button"
              onClick={() => {
                setAuthMode(authMode === 'login' ? 'signup' : 'login')
                setError('')
              }}
            >
              {authMode === 'login' ? 'Sign up' : 'Login'}
            </button>
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">♟</span>
          <span>FORMULON CHESS</span>
        </div>

        <nav>
          <span className={!showHistory && !showReview ? 'active' : ''}>
            Play
          </span>
          <button onClick={() => {
            setShowHistory(!showHistory)
            setShowReview(false)
          }}>
            History
          </button>
        </nav>

        <div className="online-status">
          <span className="green-dot" />
          Engine ready
          <button onClick={() => void logout()}>Logout</button>
        </div>
      </header>

      <main className="main-layout">
        <section className="game-area">
          {/* Top player card - always shows the player that's physically on top of the board */}
          <div className={`player-card ${(game.turn() === 'b' && gameStarted) ? 'active-clock' : ''}`}>
            <div className="avatar">{orientation === 'white' ? '♟' : '♙'}</div>
            <div>
              <strong>{orientation === 'white' ? 'Hybrid AI' : (user?.username || user?.email || 'You')}</strong>
              <small>{orientation === 'white' ? 'Computer · LSTM + Minimax' : 'Black · Human player'}</small>
            </div>
            <span className="rating">
              <strong className="clock">{formatTime(orientation === 'white' ? blackTimeMs : whiteTimeMs)}</strong>
            </span>
          </div>

          <div className="board-wrapper">
            <div className="board-container">
              <Chessboard
                options={{
                  position: showReview ? replayFen : game.fen(),
                  onPieceDrop: showReview ? () => false : onDrop,
                  boardOrientation: orientation,
                  allowDragging:
                    !showReview &&
                    !isGameOver &&
                    !thinking &&
                    game.turn() === (orientation === 'white' ? 'w' : 'b'),
                  animationDurationInMs: 180,
                  squareStyles: Object.fromEntries(
                    annotations
                      .filter(() => !showReview)
                      .map(item => {
                        const square = getDestination(item.uci)
                        return square
                          ? [square, {
                              background: `linear-gradient(135deg, ${QUALITY_STYLE[item.quality].color}35, transparent)`,
                            }]
                          : ['', {}]
                      })
                      .filter(([key]) => key)
                  ),
                  boardStyle: {
                    borderRadius: '4px',
                    boxShadow: '0 12px 35px rgba(0,0,0,0.35)',
                  },
                }}
              />
              <div className="annotation-overlay">
                {!showReview && annotations.map((item, index) => {
                  const square = getDestination(item.uci)
                  if (!square) return null

                  const style = QUALITY_STYLE[item.quality]

                  return (
                    <div
                      key={`${index}-${square}`}
                      className="square-annotation"
                      style={{
                        ...annotationPosition(square),
                        color: style.color,
                      }}
                      title={`${item.san}: ${item.quality}`}
                    >
                      {style.symbol}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Bottom player card - always shows the player that's physically at the bottom of the board */}
          <div className={`player-card bottom-player ${(game.turn() === 'w' && gameStarted) ? 'active-clock' : ''}`}>
            <div className="avatar user-avatar">{orientation === 'white' ? '♙' : '♟'}</div>
            <div>
              <strong>{orientation === 'white' ? (user?.username || user?.email || 'You') : 'Hybrid AI'}</strong>
              <small>{orientation === 'white' ? 'White · Human player' : 'Computer · LSTM + Minimax'}</small>
            </div>
            <span className="rating">
              <strong className="clock">{formatTime(orientation === 'white' ? whiteTimeMs : blackTimeMs)}</strong>
            </span>
          </div>

          <div className="game-controls">
            <select
              value={difficulty}
              disabled={thinking}
              onChange={event => setDifficulty(event.target.value)}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
              <option value="expert">Expert</option>
            </select>

            <select
              value={timeControl}
              disabled={thinking}
              onChange={event => setTimeControl(event.target.value)}
            >
              <option value="1+0">1 min</option>
              <option value="3+0">3 min</option>
              <option value="5+0">5 min</option>
              <option value="10+0">10 min</option>
              <option value="15+0">15 min</option>
            </select>

            <select
              value={colorSelection}
              disabled={thinking}
              onChange={event => setColorSelection(event.target.value as 'white' | 'black' | 'random')}
            >
              <option value="white">Play as White</option>
              <option value="black">Play as Black</option>
              <option value="random">Random Color</option>
            </select>

            <button onClick={() => void newGame()} disabled={thinking}>
              + New Game
            </button>

            <button
              onClick={() => void undoMove()}
              disabled={thinking || history.length === 0 || showReview}
            >
              ↶ Undo
            </button>

            <button onClick={() =>
              setOrientation(current => current === 'white' ? 'black' : 'white')
            }>
              ⇅ Flip
            </button>
          </div>

          {showReview && review && (
            <section className="review-panel">
              <div className="review-heading">
                <div>
                  <h2>Game Review</h2>
                  <p>{review.opening_name || 'FORMULON Chess Analysis'}</p>
                </div>
                <button onClick={() => setShowReview(false)}>Back to game</button>
              </div>

              <div className="accuracy-grid">
                <div>
                  <span>White accuracy</span>
                  <strong>
                    {review.white_accuracy !== undefined
                      ? `${review.white_accuracy.toFixed(1)}%`
                      : '—'}
                  </strong>
                </div>
                <div>
                  <span>Black accuracy</span>
                  <strong>
                    {review.black_accuracy !== undefined
                      ? `${review.black_accuracy.toFixed(1)}%`
                      : '—'}
                  </strong>
                </div>
              </div>

              <h3>Evaluation graph</h3>
              <div className="evaluation-graph">
                {graphValues.length > 1 ? (
                  <svg viewBox="0 0 600 180" preserveAspectRatio="none">
                    <line x1="0" y1="90" x2="600" y2="90" />
                    <polyline
                      points={graphValues.map((point, index) => {
                        const x = graphValues.length <= 1
                          ? 0
                          : index * 600 / (graphValues.length - 1)
                        const y = 90 - Math.max(-80, Math.min(80, point.value)) * 0.9
                        return `${x},${y}`
                      }).join(' ')}
                    />
                  </svg>
                ) : (
                  <p>Not enough moves for an evaluation graph.</p>
                )}
              </div>

              <div className="review-navigation">
                <button
                  disabled={selectedPly < 0}
                  onClick={() => setSelectedPly(-1)}
                >
                  Start
                </button>
                <button
                  disabled={selectedPly < 0}
                  onClick={() => setSelectedPly(value => Math.max(-1, value - 1))}
                >
                  Previous
                </button>
                <span>
                  {selectedPly + 1} / {review.annotations.length}
                </span>
                <button
                  disabled={selectedPly >= review.annotations.length - 1}
                  onClick={() => setSelectedPly(value =>
                    Math.min(review.annotations.length - 1, value + 1)
                  )}
                >
                  Next
                </button>
              </div>

              {selectedMove && (
                <div className="selected-move">
                  <h3>
                    {selectedMove.move_number}. {selectedMove.san}
                  </h3>
                  <span className={`quality-label ${selectedMove.quality.toLowerCase()}`}>
                    {selectedMove.quality}
                  </span>
                  <p>Best move: <strong>{selectedMove.best_move || 'Not available'}</strong></p>
                  <p>Centipawn loss: <strong>{selectedMove.centipawn_loss ?? '—'}</strong></p>
                  <p>Played evaluation: <strong>{selectedMove.played_eval ?? '—'}</strong></p>
                </div>
              )}

              <h3>Move-by-move analysis</h3>
              <div className="review-moves">
                {review.annotations.map((move, index) => (
                  <button
                    key={move.ply}
                    className={selectedPly === index ? 'selected' : ''}
                    onClick={() => setSelectedPly(index)}
                  >
                    <span>{move.move_number}{move.color === 'b' ? '...' : '.'}</span>
                    <strong>{move.san}</strong>
                    <span className={`quality-label ${move.quality.toLowerCase()}`}>
                      {move.quality}
                    </span>
                  </button>
                ))}
              </div>

              <button className="export-button" onClick={downloadPGN}>
                Download PGN
              </button>
              <p className="review-disclaimer">
                Analysis is generated by the FORMULON custom Minimax evaluator.
                It is an approximate review, not a Stockfish-certified evaluation.
              </p>
            </section>
          )}
        </section>

        <aside className="side-panel">
          <div className="panel-heading">
            <h2>{showHistory ? 'Game History' : showReview ? 'Review' : 'Game'}</h2>
            <span className="live-tag">{isGameOver ? 'FINISHED' : 'LIVE'}</span>
          </div>

          <div className="status-card">
            <div className="status-indicator" />
            <div>
              <strong>{thinking ? 'AI is calculating...' : status}</strong>
              <small>{isGameOver ? 'Game finished' : 'Human vs AI'}</small>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          {!showHistory && !showReview && (
            <>
              <div className="moves-section">
                <h3>Move History</h3>
                <div className="moves-list">
                  {movePairs.length === 0 ? (
                    <div className="empty-moves">Make your first move.</div>
                  ) : (
                    movePairs.map((pair, index) => (
                      <div className="move-row" key={index}>
                        <span>{index + 1}.</span>
                        <span>{pair[0]}</span>
                        <span>{pair[1] || '...'}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="ai-panel">
                <div className="ai-title">
                  <span>♟</span>
                  <h3>AI Analysis</h3>
                </div>
                <p>{thinking ? 'AI is calculating...' : 'Hybrid engine connected.'}</p>
                <div className="ai-details">
                  <div><span>Engine</span><strong>LSTM + Minimax</strong></div>
                  <div><span>Search</span><strong>Alpha-Beta</strong></div>
                  <div><span>Depth</span><strong>{aiStats?.depth ?? '-'}</strong></div>
                  <div><span>Mode</span><strong>{aiStats?.mode ?? 'Ready'}</strong></div>
                  <div><span>Nodes</span><strong>{aiStats?.nodes ?? '-'}</strong></div>
                  <div><span>AI Score</span><strong>{aiScore ?? '-'}</strong></div>
                </div>
              </div>

              <div className="game-info">
                <h3>Profile</h3>
                <div><span>Username</span><strong>{user?.username || '-'}</strong></div>
                <div><span>Email</span><strong>{user?.email || '-'}</strong></div>
                <div><span>Current ELO</span><strong>{user?.elo ?? user?.rating ?? '-'}</strong></div>
                <div><span>Peak ELO</span><strong>{user?.peak_rating ?? '-'}</strong></div>
                <div><span>Moves played</span><strong>{history.length}</strong></div>
              </div>
            </>
          )}

          {showHistory && (
            <div className="game-info">
              <h3>Previous Games</h3>
              {games.length === 0 ? <p>No games found.</p> :
                games.map((item, index) => (
                  <div className="history-game" key={item.id ?? index}>
                    <span>
                      Game #{item.id ?? index + 1}
                      <small>{item.created_at ?? ''}</small>
                    </span>
                    <button
                      onClick={() => void loadReview(item.id)}
                      disabled={!item.id || reviewLoading}
                    >
                      Review
                    </button>
                  </div>
                ))}

              <h3>Rating History</h3>
              {ratingHistory.length === 0 ? <p>No rating changes yet.</p> :
                ratingHistory.map((item, index) => (
                  <div key={item.id ?? index}>
                    <span>{item.created_at ?? `Match ${index + 1}`}</span>
                    <strong>{item.new_rating ?? item.rating ?? '-'}</strong>
                  </div>
                ))}
            </div>
          )}

          {showReview && (
            <div className="game-info">
              <h3>Review status</h3>
              <div><span>Status</span><strong>{reviewStatus || 'Not loaded'}</strong></div>
              <div><span>Game ID</span><strong>{reviewGameId ?? '—'}</strong></div>

              {reviewLoading && <p>Loading review...</p>}
              {reviewError && <p className="error-message">{reviewError}</p>}

              {reviewStatus !== 'completed' && (
                <button onClick={() => void retryReview()} disabled={reviewLoading}>
                  Retry review
                </button>
              )}

              {review && (
                <button onClick={() => setShowReview(false)}>
                  Return to game
                </button>
              )}
            </div>
          )}
        </aside>
      </main>

      <footer>
        <span>FORMULON CHESS ENGINE</span>
        <span>Powered by LSTM + Minimax</span>
      </footer>
    </div>
  )
}

export default App