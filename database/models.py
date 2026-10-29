
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    Text,
    Float,
)
from sqlalchemy.orm import relationship

from database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    elo = Column(Integer, default=1000, nullable=False)
    peak_elo = Column(Integer, default=1000, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    games = relationship("Game", back_populates="user")
    rating_history = relationship("RatingHistory", back_populates="user")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    opponent_type = Column(String(20), nullable=False)
    difficulty = Column(String(30), nullable=True)
    player_color = Column(String(10), nullable=True)
    time_control = Column(String(20), default="10+0", nullable=False)

    result = Column(String(10), nullable=True)
    status = Column(String(20), default="in_progress")

    rated = Column(Boolean, default=False, nullable=False)
    elo_before = Column(Integer, nullable=True)
    elo_after = Column(Integer, nullable=True)

    # Game clock: milliseconds remaining
    white_time_ms = Column(
        Integer,
        default=600000,
        nullable=False,
    )
    black_time_ms = Column(
        Integer,
        default=600000,
        nullable=False,
    )

    # Captured material points
    white_material_points = Column(
        Integer,
        default=0,
        nullable=False,
    )
    black_material_points = Column(
        Integer,
        default=0,
        nullable=False,
    )

    # Timeout information
    termination_reason = Column(String(30), nullable=True)
    timeout_winner = Column(String(10), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="games")
    rating_history = relationship(
        "RatingHistory",
        back_populates="game",
        uselist=False,
    )


class RatingHistory(Base):
    __tablename__ = "rating_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), unique=True, nullable=False)

    old_rating = Column(Integer, nullable=False)
    new_rating = Column(Integer, nullable=False)
    rating_change = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="rating_history")
    game = relationship("Game", back_populates="rating_history")


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, default=datetime.utcnow)


class MoveRecord(Base):
    __tablename__ = "move_records"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)

    ply = Column(Integer, nullable=False)
    move_number = Column(Integer, nullable=False)
    color = Column(String(10), nullable=False)

    san = Column(String(20), nullable=False)
    uci = Column(String(10), nullable=False)

    fen_before = Column(Text, nullable=False)
    fen_after = Column(Text, nullable=False)

    eval_before = Column(Float, nullable=True)
    eval_after = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("game_id", "ply", name="uq_game_move_ply"),
    )


class GameReview(Base):
    __tablename__ = "game_reviews"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(
        Integer,
        ForeignKey("games.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    # pending, analyzing, completed, failed
    status = Column(String(20), default="pending", nullable=False)

    review_json = Column(Text, nullable=True)

    white_accuracy = Column(Float, nullable=True)
    black_accuracy = Column(Float, nullable=True)
    opening_name = Column(String(150), nullable=True)

    error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
