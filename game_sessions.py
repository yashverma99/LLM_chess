
from dataclasses import dataclass, field
from typing import Any
import time

from engine.board import ChessBoard


# Chess material values
PIECE_POINTS = {
    "p": 1,
    "n": 3,
    "b": 3,
    "r": 5,
    "q": 9,
}

@dataclass
class GameSession:
    user_id: int
    game_id: int
    opponent_type: str = "ai"
    player_color: str = "white"
    difficulty: str = "hard"
    initial_time_ms: int = 10 * 60 * 1000  # Default 10 minutes

    board: ChessBoard = field(default_factory=ChessBoard)
    history: list = field(default_factory=list)
    undo_stack: list = field(default_factory=list)
    last_ai_stats: dict[str, Any] = field(default_factory=dict)

    # Clock: remaining time for each side
    white_time_ms: int = None
    black_time_ms: int = None
    turn_started_at: float = field(default_factory=time.monotonic)
    
    def __post_init__(self):
        # Initialize remaining times if not provided
        if self.white_time_ms is None:
            self.white_time_ms = self.initial_time_ms
        if self.black_time_ms is None:
            self.black_time_ms = self.initial_time_ms

    # Points earned by capturing opponent pieces
    white_material_points: int = 0
    black_material_points: int = 0

    # Timeout state
    timed_out: bool = False
    timeout_winner: str | None = None

    # Game state
    is_finished: bool = False


# Active sessions indexed by database game_id
sessions: dict[int, GameSession] = {}

# Tracks each user's currently active game
active_games: dict[int, int] = {}


def get_side_to_move(session: GameSession) -> str:
    """Return 'white' or 'black' based on board.turn."""
    return "white" if session.board.turn == "w" else "black"


def get_remaining_time(session: GameSession, side: str) -> int:
    """Get remaining time in milliseconds."""
    return (
        session.white_time_ms
        if side == "white"
        else session.black_time_ms
    )


def set_remaining_time(
    session: GameSession,
    side: str,
    value: int,
) -> None:
    """Set remaining time in milliseconds."""
    value = max(0, int(value))

    if side == "white":
        session.white_time_ms = value
    else:
        session.black_time_ms = value


def update_clock(session: GameSession) -> dict[str, Any]:
    """
    Update the active player's clock.

    Call this before returning game state and before accepting a move.
    """
    if session.is_finished or session.timed_out:
        return get_clock_state(session)

    now = time.monotonic()
    elapsed_ms = int((now - session.turn_started_at) * 1000)

    side = get_side_to_move(session)
    remaining = get_remaining_time(session, side) - elapsed_ms

    set_remaining_time(session, side, remaining)

    # Reset timestamp after deducting elapsed time
    session.turn_started_at = now

    if remaining <= 0:
        session.timed_out = True
        session.is_finished = True

        if session.white_material_points > session.black_material_points:
            session.timeout_winner = "white"
        elif session.black_material_points > session.white_material_points:
            session.timeout_winner = "black"
        else:
            session.timeout_winner = "draw"

    return get_clock_state(session)


def switch_clock_turn(session: GameSession) -> None:
    """
    Call immediately after a successful board move.
    The next player's clock starts from this moment.
    """
    session.turn_started_at = time.monotonic()


def award_capture(
    session: GameSession,
    capturing_color: str,
    captured_piece: str,
) -> int:
    """
    Award material points for a captured piece.

    captured_piece can be 'p', 'n', 'b', 'r', 'q'
    or uppercase equivalents.
    """
    piece = captured_piece.lower()
    points = PIECE_POINTS.get(piece, 0)

    if capturing_color == "white":
        session.white_material_points += points
    elif capturing_color == "black":
        session.black_material_points += points

    return points


def get_material_state(session: GameSession) -> dict[str, int]:
    return {
        "white_material_points": session.white_material_points,
        "black_material_points": session.black_material_points,
    }


def get_clock_state(session: GameSession) -> dict[str, Any]:
    """Return clock and timeout information for the frontend."""
    return {
        "white_time_ms": max(0, session.white_time_ms),
        "black_time_ms": max(0, session.black_time_ms),
        "white_material_points": session.white_material_points,
        "black_material_points": session.black_material_points,
        "timed_out": session.timed_out,
        "timeout_winner": session.timeout_winner,
    }


def create_session(
    user_id: int,
    game_id: int,
    difficulty: str = "hard",
    opponent_type: str = "ai",
    player_color: str = "white",
    initial_time_ms: int = 10 * 60 * 1000,
) -> GameSession:

    if player_color not in ("white", "black"):
        raise ValueError("player_color must be 'white' or 'black'")

    session = GameSession(
        user_id=user_id,
        game_id=game_id,
        difficulty=difficulty,
        opponent_type=opponent_type,
        player_color=player_color,
        initial_time_ms=initial_time_ms,
    )

    sessions[game_id] = session
    active_games[user_id] = game_id

    return session


def get_session(game_id: int) -> GameSession | None:
    return sessions.get(game_id)


def get_active_session(user_id: int) -> GameSession | None:
    game_id = active_games.get(user_id)

    if game_id is None:
        return None

    session = sessions.get(game_id)

    if session is None or session.user_id != user_id:
        return None

    return session


def delete_session(game_id: int) -> None:
    session = sessions.pop(game_id, None)

    if session is not None:
        if active_games.get(session.user_id) == game_id:
            active_games.pop(session.user_id, None)


def delete_user_sessions(user_id: int) -> None:
    game_ids = [
        game_id
        for game_id, session in sessions.items()
        if session.user_id == user_id
    ]

    for game_id in game_ids:
        delete_session(game_id)