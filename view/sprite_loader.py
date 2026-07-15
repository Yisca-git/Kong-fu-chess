from __future__ import annotations
from pathlib import Path
from model.piece import Kind, Color
from view.img import Img
from input.board_mapper import CELL_SIZE

ASSETS_ROOT = Path(__file__).resolve().parent.parent / "assets"
PIECES_ROOT = ASSETS_ROOT / "pieces"
BOARD_IMAGE_PATH = ASSETS_ROOT / "board.png"

_COLOR_LETTERS: dict[Color, str] = {
    Color.WHITE: "W",
    Color.BLACK: "B",
}


class SpriteLoader:
    """Loads and caches Img sprites for pieces and the board background.

    Follows the CTD26 asset convention:
    assets/pieces/<KindLetter><ColorLetter>/states/<state>/sprites/<n>.png

    Piece sprites are resized to fit within one board cell (CELL_SIZE, keeping aspect
    ratio) at load time, since the raw source sprites are larger than a cell. The board
    background is resized to an exact multiple of CELL_SIZE (cols x rows) so it lines up
    with input.board_mapper's pixel-to-cell math — the raw board.png isn't a clean multiple
    of CELL_SIZE.
    """

    def __init__(self, pieces_root: Path = PIECES_ROOT, board_path: Path = BOARD_IMAGE_PATH,
                 cell_size: int = CELL_SIZE):
        self._pieces_root = pieces_root
        self._board_path  = board_path
        self._cell_size   = cell_size
        self._frame_cache: dict[tuple[Kind, Color, str], list[Img]] = {}
        self._board_cache: dict[tuple[int, int], Img] = {}

    def frames_for(self, kind: Kind, color: Color, state: str) -> list[Img]:
        """Returns the cached list of Img frames for the given piece kind/color/state,
        loading them from disk on first request."""
        key = (kind, color, state)
        if key not in self._frame_cache:
            self._frame_cache[key] = self._load_frames(kind, color, state)
        return self._frame_cache[key]

    def _load_frames(self, kind: Kind, color: Color, state: str) -> list[Img]:
        """Reads every sprite PNG for (kind, color, state) from disk, ordered by frame
        number, resized to fit within one cell."""
        folder = self._pieces_root / f"{kind.value}{_COLOR_LETTERS[color]}" / "states" / state / "sprites"
        paths  = sorted(folder.glob("*.png"), key=lambda p: int(p.stem))
        size   = (self._cell_size, self._cell_size)
        return [Img().read(str(p), size=size, keep_aspect=True) for p in paths]

    def board_image(self, rows: int, cols: int) -> Img:
        """Returns the cached board background image resized to rows*cols cells,
        loading it from disk on first request for that board size."""
        key = (rows, cols)
        if key not in self._board_cache:
            size = (cols * self._cell_size, rows * self._cell_size)
            self._board_cache[key] = Img().read(str(self._board_path), size=size)
        return self._board_cache[key]

