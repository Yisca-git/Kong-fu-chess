from __future__ import annotations
from model.position import Position
from engine.game_engine import GameEngine
from input.board_mapper import pixel_to_position


class Controller:
    def __init__(self, engine: GameEngine, board_rows: int, board_cols: int):
        self._engine     = engine
        self._board_rows = board_rows
        self._board_cols = board_cols
        self._selected:  Position | None = None

    def _in_bounds(self, pos: Position) -> bool:
        """Returns True if the position is within the board boundaries."""
        return 0 <= pos.row < self._board_rows and 0 <= pos.col < self._board_cols

    def handle_jump(self, x: int, y: int) -> None:
        """Handles a pixel-space right-click: issues a jump command for the piece at the given position."""
        pos = pixel_to_position(x, y)
        if self._in_bounds(pos):
            self._engine.request_jump(pos)

    def handle_click(self, x: int, y: int) -> None:
        """Handles a pixel-space click: selects a piece or issues a move command."""
        pos = pixel_to_position(x, y)

        if not self._in_bounds(pos):
            self._selected = None
            return

        if self._selected is None:
            if self._engine.piece_at(pos):
                self._selected = pos
            return

        self._engine.request_move(self._selected, pos)
        self._selected = None
