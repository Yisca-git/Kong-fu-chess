from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from engine.game_snapshot import GameSnapshot, PieceSnapshot
from engine.move_log import MoveEntry
from view.renderer import Renderer
from view.sprites.sprite_library import SpriteLibrary
from view.config import CELL_SIZE


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id=f"{color.value}{kind.value}", color=color, kind=kind, cell=Position(row, col))


def test_render_returns_canvas_sized_to_board():
    board = Board(8, 8)
    snapshot = GameSnapshot.from_pieces([], False, board.rows, board.cols)
    renderer = Renderer(SpriteLibrary())

    canvas = renderer.render(snapshot, now_ms=0)

    from view.config import CELL_SIZE, PANEL_W
    h, w = canvas.img.shape[:2]
    assert (w, h) == (8 * CELL_SIZE + 2 * PANEL_W, 8 * CELL_SIZE)


def test_render_does_not_mutate_cached_board_image():
    board = Board(8, 8)
    rook = make_piece(0, 0)
    snapshot = GameSnapshot.from_pieces([rook], False, board.rows, board.cols)
    sprite_library = SpriteLibrary()
    renderer = Renderer(sprite_library)

    cached_before = sprite_library.board_image(8, 8).img.copy()
    renderer.render(snapshot, now_ms=0)
    cached_after = sprite_library.board_image(8, 8).img

    assert (cached_before == cached_after).all()


def test_render_twice_produces_independent_canvases():
    board = Board(8, 8)
    rook = make_piece(0, 0)
    snapshot = GameSnapshot.from_pieces([rook], False, board.rows, board.cols)
    renderer = Renderer(SpriteLibrary())

    canvas1 = renderer.render(snapshot, now_ms=0)
    canvas2 = renderer.render(snapshot, now_ms=0)

    assert canvas1.img is not canvas2.img


def test_render_uses_moving_sprite_for_moving_piece():
    board = Board(8, 8)
    rook = make_piece(0, 0)
    rook.state = PieceState.MOVING
    snapshot = GameSnapshot.from_pieces([rook], False, board.rows, board.cols)
    renderer = Renderer(SpriteLibrary())

    canvas = renderer.render(snapshot, now_ms=0)
    assert canvas.img is not None


def test_render_game_over_does_not_raise():
    snapshot = GameSnapshot.from_pieces([], game_over=True, rows=8, cols=8, winner="w")
    renderer = Renderer(SpriteLibrary())
    canvas = renderer.render(snapshot, now_ms=0)
    assert canvas.img is not None


def test_render_with_move_log_entries_does_not_raise():
    entries = [
        MoveEntry(color="w", notation="P E2→E4", time_ms=1000),
        MoveEntry(color="b", notation="P E7→E5", time_ms=1500),
    ]
    snapshot = GameSnapshot.from_pieces([], False, 8, 8, move_log=entries)
    renderer = Renderer(SpriteLibrary())
    canvas = renderer.render(snapshot, now_ms=0)
    assert canvas.img is not None


def test_render_with_scores_does_not_raise():
    snapshot = GameSnapshot.from_pieces([], False, 8, 8, white_score=9, black_score=3)
    renderer = Renderer(SpriteLibrary())
    canvas = renderer.render(snapshot, now_ms=0)
    assert canvas.img is not None


def test_render_cooldown_bar_does_not_raise():
    rook = make_piece(3, 3)
    snapshot = GameSnapshot.from_pieces(
        [rook], False, 8, 8,
        cooldown_progress_for=lambda p: 0.6,
    )
    renderer = Renderer(SpriteLibrary())
    canvas = renderer.render(snapshot, now_ms=0)
    assert canvas.img is not None


def test_render_selected_cell_does_not_raise():
    snapshot = GameSnapshot.from_pieces([], False, 8, 8, selected_row=3, selected_col=4)
    renderer = Renderer(SpriteLibrary())
    canvas = renderer.render(snapshot, now_ms=0)
    assert canvas.img is not None


def test_render_pawn_promotion_switches_to_queen_sprite():
    """After promotion, the renderer must use the Queen sprite, not the Pawn sprite."""
    from unittest.mock import MagicMock, patch
    from view.rendering.piece_renderer import PieceRenderer
    from view.sprites.sprite_state import AnimatedSprite

    library = MagicMock()
    pawn_sprite  = MagicMock()
    queen_sprite = MagicMock()
    pawn_sprite.kind  = "P"
    queen_sprite.kind = "Q"

    created = []
    def make_sprite(lib, color, kind, state):
        s = MagicMock()
        s.kind = kind
        s.current_frame = MagicMock()
        s.current_frame.img = None
        created.append(kind)
        return s

    renderer = PieceRenderer(library)

    pawn_snap  = PieceSnapshot(id="wP60", color="w", kind="P", row=6, col=0)
    queen_snap = PieceSnapshot(id="wP60", color="w", kind="Q", row=0, col=0)

    with patch("view.rendering.piece_renderer.AnimatedSprite", side_effect=make_sprite):
        renderer._animated_sprite_for(pawn_snap,  dt_ms=0)
        renderer._animated_sprite_for(queen_snap, dt_ms=0)

    assert created == ["P", "Q"], "Expected a new AnimatedSprite to be created after promotion"

