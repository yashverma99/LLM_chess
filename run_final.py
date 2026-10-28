import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix the only error in app.py - missing comma in make_move()
with open('gui/app.py', 'r') as f:
    content = f.read()
content = content.replace('make_move(self.board (', 'make_move(self.board, (')
with open('gui/app.py', 'w') as f:
    f.write(content)

# Now run the GUI
from gui.app import main
main()