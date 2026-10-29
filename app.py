
import time
from datetime import datetime
from contextlib import asynccontextmanager

import jwt

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from mangum import Mangum

from engine.board import ChessBoard
from engine.fen import to_fen
from engine.hybrid import select_move
from engine.evaluation import evaluate_position
from engine.legal_moves import (
    generate_legal_moves,
    make_move,
    undo_move,
    is_in_check,
)
from engine.san import move_to_san

from database.connection import get_db
from database.models import User, RevokedToken, Game, RatingHistory

from game_sessions import (
    create_session,
    get_session,
    get_active_session,
    delete_user_sessions,
    update_clock,
    switch_clock_turn,
    award_capture,
    get_clock_state,
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


# =====================================================
# STARTUP
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FORMULON CHESS STARTING")

    try:
        yield
    finally:
        print("FORMULON CHESS SHUTTING DOWN")
    


app = FastAPI(
    title="Formulon Chess API",
    lifespan=lifespan,
)

handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "https://llm-chess-tau.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# AUTHENTICATION
# =====================================================

bearer_scheme = HTTPBearer()

DIFFICULTY_DEPTHS = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
    "expert": 4,
}

AI_RATINGS = {
    "easy": 800,
    "medium": 1200,
    "hard": 1600,
    "expert": 2000,
}

PIECE_POINTS = {
    "p": 1,
    "n": 3,
    "b": 3,
    "r": 5,
    "q": 9,
}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    error = HTTPException(
        status_code=401,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = decode_access_token(credentials.credentials)
    except (ValueError, jwt.InvalidTokenError, KeyError):
        raise error

    revoked = db.query(RevokedToken).filter(
        RevokedToken.jti == token_data["jti"]
    ).first()

    if revoked:
        raise error

    user = db.query(User).filter(
        User.id == token_data["user_id"]
    ).first()

    if not user:
        raise error

    return user


# =====================================================
# REQUEST MODELS
# =====================================================

class MoveRequest(BaseModel):
    from_square: str
    to_square: str


class DifficultyRequest(BaseModel):
    difficulty: str = Field(min_length=1)


class NewGameRequest(BaseModel):
    opponent_type: str = "ai"
    difficulty: str = "hard"
    player_color: str = "white"
    time_control: str = "10+0"  # format: minutes+increment, supported: 1+0, 3+0, 5+0, 10+0, 15+0


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


# =====================================================
# GAME HELPERS
# =====================================================

def get_user_game(current_user: User):
    session = get_active_session(current_user.id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="No active game. Start a new game first.",
        )

    return session


def get_game_record(game_id: int, current_user: User, db: Session):
    game = db.query(Game).filter(
        Game.id == game_id,
        Game.user_id == current_user.id,
    ).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return game


def opposite_color(color: str) -> str:
    return "black" if color == "white" else "white"


def board_color(color: str) -> str:
    return "w" if color == "white" else "b"


def get_player_color(session):
    return session.player_color


def get_ai_color(session):
    return opposite_color(session.player_color)


def count_repetitions(session):
    positions = session.board.position_history

    if not positions:
        return 0

    current = " ".join(positions[-1].split()[:4])

    return sum(
        1 for fen in positions
        if " ".join(fen.split()[:4]) == current
    )


def has_insufficient_material(session):
    pieces = [
        (index, piece)
        for index, piece in enumerate(session.board.board)
        if piece != "."
    ]

    non_kings = [
        (index, piece)
        for index, piece in pieces
        if piece.lower() != "k"
    ]

    if len(non_kings) == 0:
        return True

    if len(non_kings) == 1:
        return non_kings[0][1].lower() in ("b", "n")

    if (
        len(non_kings) == 2
        and all(piece.lower() == "b" for _, piece in non_kings)
    ):
        colors = [
            (index // 8 + index % 8) % 2
            for index, _ in non_kings
        ]
        return colors[0] == colors[1]

    return False


DRAW_STATUSES = {
    "stalemate",
    "fifty_move_rule",
    "threefold_repetition",
    "insufficient_material",
}


def get_status(session):
    board = session.board
    legal_moves = generate_legal_moves(board)

    if not legal_moves:
        if is_in_check(board, board.turn):
            return "checkmate"
        return "stalemate"

    if board.halfmove_clock >= 100:
        return "fifty_move_rule"

    if count_repetitions(session) >= 3:
        return "threefold_repetition"

    if has_insufficient_material(session):
        return "insufficient_material"

    if is_in_check(board, board.turn):
        return "check"

    return "playing"


def sync_session_to_game(session, game, db):
    game.white_time_ms = session.white_time_ms
    game.black_time_ms = session.black_time_ms
    game.white_material_points = session.white_material_points
    game.black_material_points = session.black_material_points

    if session.timed_out:
        game.termination_reason = "timeout"
        game.timeout_winner = session.timeout_winner

    db.commit()


def finish_game(session, db, game_status):
    game = db.query(Game).filter(
        Game.id == session.game_id,
        Game.user_id == session.user_id,
    ).first()

    if not game or game.status == "completed":
        return

    if game_status == "checkmate":
        winner = "white" if session.board.turn == "b" else "black"
        result = "win" if winner == session.player_color else "loss"
    else:
        result = "draw"

    game.result = result
    game.status = "completed"
    game.completed_at = datetime.utcnow()
    game.termination_reason = game_status

    update_elo(session, game, db, result)
    db.commit()


def update_elo(session, game, db, result):
    if game.opponent_type != "ai" or game.rated:
        return

    user = db.query(User).filter(
        User.id == session.user_id
    ).with_for_update().first()

    if not user:
        return

    old_rating = user.elo
    ai_rating = AI_RATINGS.get(session.difficulty, 1200)

    score = {
        "win": 1.0,
        "draw": 0.5,
        "loss": 0.0,
    }[result]

    expected = 1 / (
        1 + 10 ** ((ai_rating - old_rating) / 400)
    )

    new_rating = round(old_rating + 32 * (score - expected))

    user.elo = new_rating
    user.peak_elo = max(user.peak_elo, new_rating)

    game.rated = True
    game.elo_before = old_rating
    game.elo_after = new_rating

    db.add(
        RatingHistory(
            user_id=user.id,
            game_id=game.id,
            old_rating=old_rating,
            new_rating=new_rating,
            rating_change=new_rating - old_rating,
        )
    )


def check_game_timeout(session, game, db):
    if session.timed_out or game.status == "completed":
        return session.timed_out

    update_clock(session)
    sync_session_to_game(session, game, db)

    if not session.timed_out:
        return False

    winner = session.timeout_winner

    if winner == "draw":
        result = "draw"
    elif winner == session.player_color:
        result = "win"
    else:
        result = "loss"

    game.result = result
    game.status = "completed"
    game.completed_at = datetime.utcnow()
    game.termination_reason = "timeout"
    game.timeout_winner = winner

    update_elo(session, game, db, result)
    db.commit()

    return True


def get_captured_piece(board, move):
    from_index, to_index = move
    moving_piece = board.board[from_index]
    target_piece = board.board[to_index]

    if target_piece != ".":
        return target_piece

    # En passant
    if (
        moving_piece.lower() == "p"
        and from_index % 8 != to_index % 8
    ):
        if moving_piece.isupper():
            return board.board[to_index + 8]
        return board.board[to_index - 8]

    return "."


def award_capture_points(session, capturing_color, captured_piece):
    if captured_piece == ".":
        return

    award_capture(session, capturing_color, captured_piece)


def complete_if_finished(session, db):
    game_status = get_status(session)

    if game_status in DRAW_STATUSES or game_status == "checkmate":
        finish_game(session, db, game_status)

    return game_status


def get_game_state(session):
    board = session.board
    game_status = get_status(session)
    clock_state = get_clock_state(session)

    winner = None

    if session.timed_out:
        game_status = "timeout"
        winner = session.timeout_winner
    elif game_status == "checkmate":
        winner = "white" if board.turn == "b" else "black"
    elif game_status in DRAW_STATUSES:
        winner = "draw"

    return {
        "game_id": session.game_id,
        "fen": to_fen(board),
        "history": session.history.copy(),
        "turn": board.turn,
        "status": game_status,
        "winner": winner,
        "termination_reason": (
            "timeout" if session.timed_out
            else game_status if game_status != "playing"
            else None
        ),
        "moves_played": len(session.history),
        "difficulty": session.difficulty,
        "opponent_type": session.opponent_type,
        "player_color": session.player_color,
        "evaluation": evaluate_position(board),
        "clock": clock_state,
        "white_time_ms": clock_state["white_time_ms"],
        "black_time_ms": clock_state["black_time_ms"],
        "timed_out": clock_state["timed_out"],
        "timeout_winner": clock_state["timeout_winner"],
        "material": {
            "white": session.white_material_points,
            "black": session.black_material_points,
        },
    }


# =====================================================
# GENERAL API
# =====================================================

@app.get("/")
def root():
    return {
        "message": "Formulon Chess API is running",
        "version": "3.0",
    }


@app.get("/api/status")
def api_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_game(current_user)
    game = get_game_record(session.game_id, current_user, db)

    check_game_timeout(session, game, db)

    return {
        **get_game_state(session),
        "ai_stats": session.last_ai_stats.copy(),
    }


@app.post("/api/new-game")
def new_game(
    request: NewGameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opponent = request.opponent_type.strip().lower()
    difficulty = request.difficulty.strip().lower()
    player_color = request.player_color.strip().lower()
    time_control = request.time_control.strip().lower()

    # Validate inputs
    if opponent not in ("ai", "human"):
        raise HTTPException(400, "Opponent must be ai or human")

    if difficulty not in DIFFICULTY_DEPTHS:
        raise HTTPException(400, "Invalid difficulty")

    if player_color not in ("white", "black"):
        raise HTTPException(400, "Player color must be white or black")

    # Validate and parse time control
    valid_time_controls = ["1+0", "3+0", "5+0", "10+0", "15+0"]
    if time_control not in valid_time_controls:
        raise HTTPException(400, f"Invalid time control. Must be one of: {', '.join(valid_time_controls)}")
    
    # Parse minutes from time control (all have 0 increment)
    minutes = int(time_control.split("+")[0])
    initial_time_ms = minutes * 60 * 1000

    game = Game(
        user_id=current_user.id,
        opponent_type=opponent,
        difficulty=difficulty if opponent == "ai" else None,
        player_color=player_color,
        time_control=time_control,
        status="in_progress",
        rated=False,
        white_time_ms=initial_time_ms,
        black_time_ms=initial_time_ms,
        white_material_points=0,
        black_material_points=0,
    )

    db.add(game)
    db.commit()
    db.refresh(game)

    session = create_session(
        user_id=current_user.id,
        game_id=game.id,
        difficulty=difficulty,
        opponent_type=opponent,
        player_color=player_color,
        initial_time_ms=initial_time_ms,
    )

    return get_game_state(session)


@app.get("/api/evaluation")
def evaluation(current_user: User = Depends(get_current_user)):
    session = get_user_game(current_user)

    return {
        "score": evaluate_position(session.board),
        "perspective": "white",
        "fen": to_fen(session.board),
    }


# =====================================================
# DIFFICULTY
# =====================================================

@app.get("/api/difficulty")
def get_difficulty(current_user: User = Depends(get_current_user)):
    session = get_user_game(current_user)

    return {
        "difficulty": session.difficulty,
        "depth": DIFFICULTY_DEPTHS[session.difficulty],
        "available_levels": DIFFICULTY_DEPTHS,
    }


@app.post("/api/difficulty")
def set_difficulty(
    request: DifficultyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_game(current_user)
    level = request.difficulty.strip().lower()

    if level not in DIFFICULTY_DEPTHS:
        raise HTTPException(400, "Invalid difficulty")

    game = get_game_record(session.game_id, current_user, db)

    if game.status == "completed":
        raise HTTPException(400, "Game is already completed")

    session.difficulty = level
    game.difficulty = level
    db.commit()

    return {
        "difficulty": level,
        "depth": DIFFICULTY_DEPTHS[level],
    }


# =====================================================
# PLAYER MOVE
# =====================================================

@app.post("/api/move")
def player_move(
    request: MoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_game(current_user)
    game = get_game_record(session.game_id, current_user, db)

    if game.status == "completed":
        raise HTTPException(400, "Game is already completed")

    if check_game_timeout(session, game, db):
        return get_game_state(session)

    board = session.board
    user_turn = board_color(session.player_color)

    if board.turn != user_turn:
        raise HTTPException(400, "It is not your turn")

    if get_status(session) not in ("playing", "check"):
        raise HTTPException(400, "Game is over")

    try:
        from_index = board.square_to_index(request.from_square)
        to_index = board.square_to_index(request.to_square)
        move = (from_index, to_index)

        if move not in generate_legal_moves(board):
            raise HTTPException(400, "Illegal move")

        captured_piece = get_captured_piece(board, move)
        san = move_to_san(board, move)

        old_state = make_move(board, move)

        session.undo_stack.append((move, old_state))
        session.history.append(san)

        award_capture_points(session, session.player_color, captured_piece)
        switch_clock_turn(session)
        sync_session_to_game(session, game, db)

        complete_if_finished(session, db)

        return {
            **get_game_state(session),
            "last_move": san,
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(400, str(error))


# =====================================================
# AI MOVE
# =====================================================

@app.post("/api/ai-move")
def ai_move(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_game(current_user)
    game = get_game_record(session.game_id, current_user, db)

    if game.status == "completed":
        raise HTTPException(400, "Game is already completed")

    if check_game_timeout(session, game, db):
        return get_game_state(session)

    if session.opponent_type != "ai":
        raise HTTPException(400, "This game does not have an AI opponent")

    board = session.board
    ai_turn = board_color(get_ai_color(session))

    if board.turn != ai_turn:
        raise HTTPException(400, "It is not AI's turn")

    if get_status(session) not in ("playing", "check"):
        raise HTTPException(400, "Game is over")

    try:
        depth = DIFFICULTY_DEPTHS[session.difficulty]
        start = time.perf_counter()

        move, score, stats = select_move(
            board,
            history=session.history,
            depth=depth,
        )

        thinking_time = time.perf_counter() - start

        # AI thinking time bhi uske clock se deduct hoga.
        if check_game_timeout(session, game, db):
            return get_game_state(session)

        if move is None:
            complete_if_finished(session, db)
            return get_game_state(session)

        captured_piece = get_captured_piece(board, move)
        san = move_to_san(board, move)

        old_state = make_move(board, move)

        session.undo_stack.append((move, old_state))
        session.history.append(san)

        award_capture_points(session, get_ai_color(session), captured_piece)

        session.last_ai_stats = {
            **stats,
            "score": score,
            "difficulty": session.difficulty,
            "requested_depth": depth,
            "thinking_time_seconds": round(thinking_time, 3),
        }

        switch_clock_turn(session)
        sync_session_to_game(session, game, db)

        complete_if_finished(session, db)

        return {
            **get_game_state(session),
            "last_move": san,
            "ai_score": score,
            "ai_stats": session.last_ai_stats.copy(),
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(500, f"AI move failed: {error}")


# =====================================================
# UNDO
# =====================================================

@app.post("/api/undo")
def undo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_game(current_user)
    game = get_game_record(session.game_id, current_user, db)

    if game.status == "completed":
        raise HTTPException(400, "Cannot undo a completed game")

    if not session.undo_stack:
        raise HTTPException(400, "No moves to undo")

    undo_count = 1

    if session.opponent_type == "ai" and len(session.undo_stack) >= 2:
        undo_count = 2

    for _ in range(undo_count):
        move, old_state = session.undo_stack.pop()
        undo_move(session.board, move, old_state)

        if session.history:
            session.history.pop()

    # Clock aur material score ko undo karne ke liye
    # snapshots ki zarurat hai; is version mein board undo hota hai.
    session.last_ai_stats = {}

    return get_game_state(session)


# =====================================================
# GAME HISTORY
# =====================================================

@app.get("/api/games")
def game_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    games = db.query(Game).filter(
        Game.user_id == current_user.id
    ).order_by(Game.created_at.desc()).limit(100).all()

    return [
        {
            "id": game.id,
            "opponent_type": game.opponent_type,
            "difficulty": game.difficulty,
            "result": game.result,
            "status": game.status,
            "rated": game.rated,
            "elo_before": game.elo_before,
            "elo_after": game.elo_after,
            "created_at": game.created_at,
            "completed_at": game.completed_at,
            "termination_reason": game.termination_reason,
            "timeout_winner": game.timeout_winner,
            "white_material_points": game.white_material_points,
            "black_material_points": game.black_material_points,
        }
        for game in games
    ]


@app.get("/api/rating-history")
def rating_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = db.query(RatingHistory).filter(
        RatingHistory.user_id == current_user.id
    ).order_by(RatingHistory.created_at.desc()).limit(100).all()

    return [
        {
            "game_id": record.game_id,
            "old_rating": record.old_rating,
            "new_rating": record.new_rating,
            "rating_change": record.rating_change,
            "created_at": record.created_at,
        }
        for record in records
    ]


# =====================================================
# SIGNUP
# =====================================================

@app.post("/api/signup", status_code=201)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
):
    username = request.username.strip()
    email = request.email.strip().lower()

    if not username or not email:
        raise HTTPException(400, "Username and email are required")

    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing:
        raise HTTPException(409, "Username or email already registered")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(request.password),
        elo=1000,
        peak_elo=1000,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Username or email already registered")

    token = create_access_token(user.id)

    return {
        "message": "Account created successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "elo": user.elo,
            "peak_elo": user.peak_elo,
        },
    }


# =====================================================
# LOGIN
# =====================================================

@app.post("/api/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    email = request.email.strip().lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(401, "Incorrect email or password")

    token = create_access_token(user.id)

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "elo": user.elo,
            "peak_elo": user.peak_elo,
        },
    }


# =====================================================
# PROFILE
# =====================================================

@app.get("/api/profile")
def profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "elo": current_user.elo,
        "peak_elo": current_user.peak_elo,
        "created_at": current_user.created_at,
    }


# =====================================================
# LOGOUT
# =====================================================

@app.post("/api/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token_data = decode_access_token(credentials.credentials)

    existing = db.query(RevokedToken).filter(
        RevokedToken.jti == token_data["jti"]
    ).first()

    if not existing:
        db.add(
            RevokedToken(
                jti=token_data["jti"],
                expires_at=token_data["expires_at"],
            )
        )
        db.commit()

    delete_user_sessions(current_user.id)

    return {"message": "Logout successful"}