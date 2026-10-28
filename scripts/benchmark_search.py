import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.board import ChessBoard
from engine.fen import load_fen
from engine.hybrid import select_move
from engine.search import find_best_move


STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def new_board():
    board = ChessBoard()
    load_fen(board, STARTING_FEN)
    return board


def run():
    parser = argparse.ArgumentParser(description="Benchmark engine and hybrid search.")
    parser.add_argument("--depth", type=int, default=2)
    args = parser.parse_args()

    engine_stats = {"nodes": 0, "cutoffs": 0}
    board = new_board()
    start = time.perf_counter()
    move, score = find_best_move(board, args.depth, engine_stats)
    elapsed = time.perf_counter() - start
    print({
        "mode": "engine",
        "depth": args.depth,
        "move": move,
        "score": score,
        "nodes": engine_stats.get("nodes", 0),
        "cutoffs": engine_stats.get("cutoffs", 0),
        "seconds": elapsed,
        "nodes_per_second": engine_stats.get("nodes", 0) / elapsed if elapsed else 0,
    })

    board = new_board()
    start = time.perf_counter()
    move, score, stats = select_move(board, depth=args.depth)
    elapsed = time.perf_counter() - start
    print({
        "mode": "hybrid",
        "depth": args.depth,
        "move": move,
        "score": score,
        "nodes": stats.get("nodes", 0),
        "cutoffs": stats.get("cutoffs", 0),
        "seconds": elapsed,
        "nodes_per_second": stats.get("nodes", 0) / elapsed if elapsed else 0,
        "hybrid_mode": stats.get("mode"),
    })


if __name__ == "__main__":
    run()
