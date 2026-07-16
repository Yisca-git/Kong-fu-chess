from __future__ import annotations
from typing import Protocol, TYPE_CHECKING
from view.img import Img

if TYPE_CHECKING:
    from engine.game_snapshot import GameSnapshot


class IBoardRenderer(Protocol):
    def fresh_frame(self, rows: int, cols: int) -> Img: ...


class IPieceRenderer(Protocol):
    def draw(self, frame: Img, snapshot: GameSnapshot, dt_ms: int) -> None: ...


class IOverlayRenderer(Protocol):
    def draw_selection(self, frame: Img, snapshot: GameSnapshot) -> None: ...
    def compose_panels(self, board_canvas: Img, snapshot: GameSnapshot) -> Img: ...
    def draw_game_over(self, canvas: Img, snapshot: GameSnapshot) -> None: ...
    def draw_rejection(self, canvas: Img, snapshot: GameSnapshot) -> None: ...
