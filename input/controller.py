from __future__ import annotations
from model.position import Position
from engine.move_result import MoveResult
from engine.game_engine import GameEngine
from input.board_mapper import pixel_to_position


class Controller:
    def __init__(self, engine: GameEngine, board_rows: int, board_cols: int,
                 cell_size: int):
        self._engine    = engine
        self._cell_size = cell_size
        self._selected: Position | None = None

    def set_cell_size(self, cell_size: int) -> None:
        self._cell_size = cell_size

    def _in_bounds(self, pos: Position) -> bool:
        return self._engine.in_bounds(pos)

    def handle_jump(self, x: int, y: int) -> None:
        pos = pixel_to_position(x, y, self._cell_size)
        if self._in_bounds(pos):
            result = self._engine.request_jump(pos)
            if not result.is_accepted:
                self._engine.set_rejection(result.reason)
        self._selected = None
        self._engine.set_selected(None)

    def handle_click(self, x: int, y: int) -> None:
        pos = pixel_to_position(x, y, self._cell_size)

        if not self._in_bounds(pos):
            self._selected = None
            self._engine.set_selected(None)
            return

        if self._selected is None:
            if self._engine.piece_at(pos):
                self._selected = pos
                self._engine.set_selected(pos)
            return

        result = self._engine.request_move(self._selected, pos)
        if not result.is_accepted:
            self._engine.set_rejection(result.reason)
        if result.reason == MoveResult.FRIENDLY_DESTINATION:
            self._selected = pos
            self._engine.set_selected(pos)
        else:
            self._selected = None
            self._engine.set_selected(None)
