from __future__ import annotations
from view.img import Img
from view.sprites.sprite_library import SpriteLibrary


class BoardRenderer:
    """Owns the pristine board background template and hands out a fresh copy each frame."""

    def __init__(self, library: SpriteLibrary) -> None:
        self._library = library

    def set_cell_size(self, cell_size: int) -> None:
        self._library.set_cell_size(cell_size)

    def fresh_frame(self, rows: int, cols: int) -> Img:
        board  = self._library.board_image(rows, cols)
        return board.copy()
