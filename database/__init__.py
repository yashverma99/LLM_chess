
from sqlalchemy import inspect, text

from database.connection import Base, engine
from database import models

# Create any missing tables
Base.metadata.create_all(bind=engine)

# Safely add missing columns to existing tables
inspector = inspect(engine)
game_columns = {
    column["name"] for column in inspector.get_columns("games")
}

if "time_control" not in game_columns:
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE games "
                "ADD COLUMN time_control VARCHAR(20) "
                "NOT NULL DEFAULT '10+0'"
            )
        )
    print("Added time_control column to games table")

print("Database initialized successfully!")
print("Tables created:")
print(list(Base.metadata.tables.keys()))
