from __future__ import annotations
from pathlib import Path
from model.piece import Kind, Color
from view.img import Img
from view.sprites.sprite_state import SpriteState, StateConfig
from input.board_mapper import CELL_SIZE

ASSETS_ROOT  = Path(__file__).resolve().parent.parent.parent / "assets2"
PIECES_ROOT  = ASSETS_ROOT / "pieces_mine"
BOARD_PATH   = ASSETS_ROOT / "board.png"

_COLOR_LETTER: dict[Color, str] = {Color.WHITE: "w", Color.BLACK: "b"}

# engine state -> asset folder name
_FOLDER: dict[str, str] = {
    "idle":       "idle",
    "moving":     "move",
    "airborne":   "jump",
    "short_rest": "short_rest",
    "long_rest":  "long_rest",
}


_AssetKey = tuple[str, str, str]  # (color, kind, folder)


class SpriteLibrary:
    """Strategy: the single place that knows the on-disk asset layout.
    Swap pieces_root to retarget the entire UI to a different art set — one arg.

    The asset cache stores only immutable data (config + frames list).
    Every call to get_state() returns a *fresh* SpriteState with its own
    playback clock — so two pieces of the same type never share animation state.
    """

    def __init__(self, pieces_root: Path = PIECES_ROOT,
                 board_path: Path = BOARD_PATH,
                 cell_size: int = CELL_SIZE) -> None:
        self._root       = Path(pieces_root)
        self._board_path = Path(board_path)
        self._cell_size  = cell_size
        self._asset_cache: dict[_AssetKey, tuple[StateConfig, list[Img]]] = {}
        self._board_cache: dict[tuple[int, int], Img] = {}

    def get_state(self, color: str, kind: str, engine_state: str) -> SpriteState:
        """Returns a new SpriteState (fresh clock) backed by cached frames."""
        folder = _FOLDER.get(engine_state, "idle")
        key    = (color, kind, folder)
        if key not in self._asset_cache:
            self._asset_cache[key] = self._load_assets(color, kind, folder)
        config, frames = self._asset_cache[key]
        return SpriteState(config, frames)

    def get_state_by_kind_color(self, kind: Kind, color: Color,
                                engine_state: str) -> SpriteState:
        """Convenience overload accepting Kind/Color enums."""
        return self.get_state(color.value, kind.value, engine_state)

    def board_image(self, rows: int, cols: int) -> Img:
        """Returns the cached board background resized to the exact cell grid."""
        key = (rows, cols)
        if key not in self._board_cache:
            size = (cols * self._cell_size, rows * self._cell_size)
            self._board_cache[key] = Img().read(str(self._board_path), size=size)
        return self._board_cache[key]

    def _load_assets(self, color: str, kind: str, folder: str) -> tuple[StateConfig, list[Img]]:
        state_dir   = self._root / f"{color}{kind}" / "states" / folder
        config      = StateConfig.from_json(state_dir / "config.json", folder)
        frame_paths = sorted((state_dir / "sprites").glob("*.png"),
                             key=lambda p: int(p.stem))
        if not frame_paths:
            raise FileNotFoundError(f"No frames in {state_dir / 'sprites'}")
        size   = (self._cell_size, self._cell_size)
        frames = [Img().read(str(p), size=size, keep_aspect=True) for p in frame_paths]
        return config, frames
