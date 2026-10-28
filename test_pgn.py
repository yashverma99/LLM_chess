from pathlib import Path
import re

content = Path("dataset/raw/sample.pgn").read_text(encoding="utf-8")
game = re.split(r"\n(?=\[Event )", content.strip())[0]

moves_section = game.split("\n\n", 1)[1]

moves = re.findall(
    r"(?<!\S)(?:O-O-O|O-O|[a-h][1-8](?:=[QRBN])?|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?)[+#]?",
    moves_section
)

print("Extracted moves:")
print(moves)
print("Total moves:", len(moves))
