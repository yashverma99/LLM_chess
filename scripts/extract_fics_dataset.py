import bz2
import chess.pgn
from pathlib import Path

source = Path(r"C:\Users\yashv\Downloads\ficsgamesdb_202601_chess_nomovetimes_4354651.pgn.bz2")
output = Path("dataset/raw/fics_10000.pgn")
output.parent.mkdir(parents=True, exist_ok=True)

target_games = 10000
valid_games = 0
checked_games = 0

with bz2.open(source, "rt", encoding="utf-8", errors="replace") as infile:
    with output.open("w", encoding="utf-8") as outfile:
        while valid_games < target_games:
            game = chess.pgn.read_game(infile)
            if game is None:
                break

            checked_games += 1

            if game.errors:
                continue

            if game.headers.get("Variant", "Standard").lower() != "standard":
                continue

            board = game.board()
            legal = True
            move_count = 0

            for move in game.mainline_moves():
                if move not in board.legal_moves:
                    legal = False
                    break
                board.push(move)
                move_count += 1

            if not legal or move_count < 10:
                continue

            outfile.write(str(game) + "\n\n")
            valid_games += 1

            if valid_games % 1000 == 0:
                print(f"Valid games: {valid_games}")

print(f"\nCompleted. Checked: {checked_games}")
print(f"Valid standard games: {valid_games}")
print(f"Output: {output}")
