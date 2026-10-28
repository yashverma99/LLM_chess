class ChessBoard:

    def __init__(self):
        self.board = ["."] * 64

        self.board[0:8] = list("rnbqkbnr")
        self.board[8:16] = list("pppppppp")
        self.board[48:56] = list("PPPPPPPP")
        self.board[56:64] = list("RNBQKBNR")

        self.turn = "w"
        self.castling = "KQkq"
        self.en_passant = "-"
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.position_history = []  # Track FEN positions for threefold repetition
        
        # Add initial position to history
        from engine.fen import to_fen
        self.position_history.append(to_fen(self))

    def square_to_index(self, square):
        if len(square) != 2:
            raise ValueError("Invalid square")

        file = ord(square[0]) - ord("a")
        rank = int(square[1])

        if not (0 <= file < 8 and 1 <= rank <= 8):
            raise ValueError("Invalid square")

        return (8 - rank) * 8 + file

    def index_to_square(self, index):
        if not 0 <= index < 64:
            raise ValueError("Invalid index")

        file = index % 8
        rank = 8 - (index // 8)

        return chr(ord("a") + file) + str(rank)

    def piece_at(self, square):
        index = self.square_to_index(square)
        return self.board[index]

    def display(self):
        print("  a b c d e f g h")

        for row in range(8):
            line = str(8 - row) + " "
            for col in range(8):
                index = row * 8 + col
                line += self.board[index] + " "
            print(line + str(8 - row))

        print("  a b c d e f g h")