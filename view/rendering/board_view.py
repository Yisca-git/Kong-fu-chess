from __future__ import annotations
from typing import TYPE_CHECKING
from view.rendering.protocols import IBoardRenderer, IPieceRenderer, IOverlayRenderer
from view.img import Img

if TYPE_CHECKING:
    from engine.game_snapshot import GameSnapshot


class BoardView:
    """Thin coordinator — delegates to three focused collaborators, draws nothing itself.

    Per §7.2a of final_plan.md:
      IBoardRenderer   — background template only
      IPieceRenderer   — piece compositing + animation + interpolation
      IOverlayRenderer — selection, panels, game-over banner

    All dependencies are typed against Protocols so tests can inject fakes
    without opening a window or touching disk (per §7.7).
    """

    def __init__(self, board_renderer: IBoardRenderer,
                 piece_renderer: IPieceRenderer,
                 overlay_renderer: IOverlayRenderer) -> None:
        self._board   = board_renderer
        self._pieces  = piece_renderer
        self._overlay = overlay_renderer

    @property
    def board_renderer(self) -> IBoardRenderer:
        return self._board
    def render(self, snapshot: GameSnapshot, dt_ms: int) -> Img:
        frame = self._board.fresh_frame(snapshot.rows, snapshot.cols)
        self._overlay.draw_selection(frame, snapshot)
        self._pieces.draw(frame, snapshot, dt_ms)
        full = self._overlay.compose_panels(frame, snapshot)
        if snapshot.game_over:
            self._overlay.draw_game_over(full, snapshot)
        self._overlay.draw_rejection(full, snapshot)
        self._overlay.draw_countdown(full, snapshot)
        return full
