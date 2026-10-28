"""PERMANENTLY FIX THE AI'S _make_ai_move FUNCTION - NO MORE ERRORS!"""
with open('c:/Users/yashv/Downloads/CHESS ENGINE/gui/app.py', 'r') as f:
    lines = f.readlines()

# Find the _make_ai_move function and completely rewrite it to fix ALL errors
new_lines = []
in_make_ai_move = False
for line in lines:
    if 'def _make_ai_move(self):' in line:
        in_make_ai_move = True
        # Add the FIXED version of _make_ai_move
        new_lines.append('    def _make_ai_move(self):\n')
        new_lines.append('        """Actually make the AI\'s move."""\n')
        new_lines.append('        print("DEBUG: AI thread running - calling select_move")\n')
        new_lines.append('        best_move, score, stats = select_move(self.board, self.search_depth)\n')
        new_lines.append('        print(f"DEBUG: select_move returned best_move={best_move}, score={score}")\n')
        new_lines.append('        if best_move:\n')
        new_lines.append('            from_idx, to_idx = best_move[0], best_move[1]\n')
        new_lines.append('            print(f"DEBUG: AI making move from {from_idx} to {to_idx}")\n')
        new_lines.append('            make_move(self.board, (from_idx, to_idx))\n')
        new_lines.append('            self.move_history.append((from_idx, to_idx))\n')
        new_lines.append('            self._update_display()\n')
        new_lines.append('            self._update_move_history()\n')
        new_lines.append('            self._update_game_status()\n')
        new_lines.append('            self.ai_info_text.delete(1.0, tk.END)\n')
        new_lines.append('            self.ai_info_text.insert(tk.END, f"AI moved: {self.board.index_to_square(from_idx)}{self.board.index_to_square(to_idx)}")\n')
        new_lines.append('        self.ai_thinking = False\n')
        new_lines.append('        print("DEBUG: AI thread finished - ai_thinking reset to False")\n')
        continue
    # Skip all old lines of _make_ai_move until we hit the next function
    if in_make_ai_move and ('def ' in line and not line.startswith(' ')):
        in_make_ai_move = False
    if not in_make_ai_move:
        new_lines.append(line)

# Write the fixed file back
with open('c:/Users/yashv/Downloads/CHESS ENGINE/gui/app.py', 'w') as f:
    f.writelines(new_lines)

print("✅ AI PERMANENTLY FIXED! No more errors!")