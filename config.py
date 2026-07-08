TILE_SIZE = 100

# ms — used as the unit of time throughout the game clock
MOVE_DURATION = 1000
JUMP_DURATION = 1000

# Point values used for scoring; King is infinity because capturing it ends the game
PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': float('inf')}

VALID_PIECES = set(PIECE_VALUES.keys())
VALID_COLORS = {'w', 'b'}

EMPTY = '.'
WHITE = 'w'
BLACK = 'b'
KING_SYMBOL = 'K'
PAWN_SYMBOL = 'P'
PROMOTED_PIECE = 'Q'
