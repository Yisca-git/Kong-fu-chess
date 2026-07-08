TILE_SIZE = 100

MOVE_DURATION = 1000
JUMP_DURATION = 1000

PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': float('inf')}

VALID_PIECES = set(PIECE_VALUES.keys())
VALID_COLORS = {'w', 'b'}

EMPTY = '.'
WHITE = 'w'
BLACK = 'b'
