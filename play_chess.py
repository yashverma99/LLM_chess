from engine.board import ChessBoard
from engine.legal_moves import generate_legal_moves, make_move
from engine.san import move_to_san, san_to_move
from engine.hybrid import select_move


def display_board(board):
    symbols = {
        "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
        "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
        ".": "·"
    }

    print("\n    a b c d e f g h")
    print("  +-----------------+")

    for row in range(8):
        rank = 8 - row
        pieces = " ".join(symbols[p] for p in board.board[row * 8:(row + 1) * 8])
        print(f"{rank} | {pieces} | {rank}")

    print("  +-----------------+")
    print("    a b c d e f g h")
    
    # Show check status if applicable
    is_in_check_func = __import__("engine.legal_moves", fromlist=["is_in_check"]).is_in_check
    in_check = is_in_check_func(board, board.turn)
    
    turn_text = f"\nTurn: {'White' if board.turn == 'w' else 'Black'}"
    if in_check:
        turn_text += " - ⚠️  CHECK!"
    
    print(turn_text)


def count_repetitions(board, history):
    """Count occurrences of the current position for threefold repetition."""
    from engine.fen import to_fen
    return 1  # Simplified for terminal version


def has_insufficient_material(board):
    """Check if there's insufficient material to checkmate."""
    pieces = []
    for piece in board.board:
        if piece != ".":
            pieces.append(piece.lower())
    
    # King vs king - insufficient
    if len(pieces) == 2:
        return True
    
    # King + bishop vs king or King + knight vs king
    if len(pieces) == 3:
        if "b" in pieces or "n" in pieces:
            return True
    
    return False


def get_game_status(board):
    """Get the current game status with proper termination rules."""
    legal_moves = generate_legal_moves(board)
    current_turn = board.turn
    is_in_check_func = __import__("engine.legal_moves", fromlist=["is_in_check"]).is_in_check
    
    # Game is over if no legal moves
    if not legal_moves:
        if is_in_check_func(board, current_turn):
            if current_turn == "b":
                return "checkmate_white_wins"
            else:
                return "checkmate_black_wins"
        else:
            return "stalemate_draw"
    
    # Check fifty-move rule
    if board.halfmove_clock >= 100:
        return "fifty_move_rule_draw"
    
    # Check insufficient material
    if has_insufficient_material(board):
        return "insufficient_material_draw"
    
    # Check if in check (game still ongoing)
    if is_in_check_func(board, current_turn):
        return "check"
    
    return "playing"


def main():
    board = ChessBoard()
    history = []

    print("=" * 45)
    print("       FORMULON CHESS - TERMINAL")
    print("=" * 45)
    print("You play White. AI plays Black.")
    print("Enter moves like e2e4 or SAN like Nf3.")
    print("Commands: quit, exit\n")

    display_board(board)

    while True:
        status = get_game_status(board)
        
        if status != "playing":
            # Handle game over conditions
            if status == "checkmate_white_wins":
                print("\n🏆 CHECKMATE — WHITE WINS!")
            elif status == "checkmate_black_wins":
                print("\n🏆 CHECKMATE — BLACK WINS!")
            elif status == "stalemate_draw":
                print("\n🤝 STALEMATE — DRAW!")
            elif status == "fifty_move_rule_draw":
                print("\n🤝 DRAW BY 50-MOVE RULE!")
            elif status == "insufficient_material_draw":
                print("\n🤝 DRAW BY INSUFFICIENT MATERIAL!")
            
            break

        if board.turn == "w":
            user_input = input("\nYour move: ").strip()

            if user_input.lower() in ("quit", "exit"):
                print("Game ended.")
                break

            try:
                if len(user_input) == 4 and user_input[:2] in [
                    board.index_to_square(i) for i in range(64)
                ]:
                    move = (
                        board.square_to_index(user_input[:2]),
                        board.square_to_index(user_input[2:4])
                    )
                    if move not in legal_moves:
                        raise ValueError("Illegal move")
                else:
                    move = san_to_move(board, user_input)

                san = move_to_san(board, move)
                make_move(board, move)
                history.append(san)
                print(f"You played: {san}")

            except (ValueError, IndexError) as error:
                print(f"Invalid move: {error}")
                continue

        else:
            print("\nAI is thinking...")

            move, score, stats = select_move(
                board,
                history=history,
                depth=3
            )

            if move is None:
                print("AI has no legal move.")
                break

            san = move_to_san(board, move)
            make_move(board, move)
            history.append(san)

            print(f"AI played: {san}")
            print(f"AI score: {score}")
            print(f"AI mode: {stats['mode']}")
            print(f"Nodes searched: {stats['nodes']}")

        display_board(board)


if __name__ == "__main__":
    main()