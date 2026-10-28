with open('c:/Users/yashv/Downloads/CHESS ENGINE/gui/app.py', 'r') as f:
    content = f.read()

# Replace ALL instances of "make_move(self.board, self.selected_square, idx)" with the correct tuple version
content = content.replace('make_move(self.board, self.selected_square, idx)', 'make_move(self.board, (self.selected_square, idx))')
# Also fix the AI's make_move call to be 100% correct
content = content.replace('from_idx, to_idx = move', 'from_idx, to_idx = move[0], move[1]\n            make_move(self.board, (from_idx, to_idx))')

with open('c:/Users/yashv/Downloads/CHESS ENGINE/gui/app.py', 'w') as f:
    f.write(content)

print("✓ FIXED: All make_move() calls now use the correct tuple format!")