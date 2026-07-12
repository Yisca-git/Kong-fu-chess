from position import Position
from game_engine import GameEngine
from board_mapper import pixel_to_position


class Controller:
    def __init__(self, engine, board_rows, board_cols):
        self._engine     = engine
        self._board_rows = board_rows
        self._board_cols = board_cols
        self._selected   = None

    def _in_bounds(self, pos):
        return 0 <= pos.row < self._board_rows and 0 <= pos.col < self._board_cols

    def handle_jump(self, x, y):
        pos = pixel_to_position(x, y)
        if self._in_bounds(pos):
            self._engine.request_jump(pos)

    def handle_click(self, x, y):
        pos = pixel_to_position(x, y)
        if not self._in_bounds(pos):
            self._selected = None
            return
        if self._selected is None:
            if self._engine.piece_at(pos):
                self._selected = pos
            return
        result = self._engine.request_move(self._selected, pos)
        if result.reason == 'friendly_destination':
            self._selected = pos
        else:
            self._selected = None
