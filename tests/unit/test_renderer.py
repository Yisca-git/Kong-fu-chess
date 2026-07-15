from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from engine.game_snapshot import GameSnapshot
from view.renderer import Renderer
from view.sprite_loader import SpriteLoader, CELL_SIZE


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id=f"{color.value}{kind.value}", color=color, kind=kind, cell=Position(row, col))


def test_render_returns_canvas_sized_to_board():
    board = Board(8, 8)
    snapshot = GameSnapshot.from_pieces([], False, board.rows, board.cols)
    renderer = Renderer(SpriteLoader())

    canvas = renderer.render(snapshot, now_ms=0)

    from view.renderer import PANEL_W
    h, w = canvas.img.shape[:2]
    assert (w, h) == (8 * CELL_SIZE + 2 * PANEL_W, 8 * CELL_SIZE)


def test_render_does_not_mutate_cached_board_image():
    board = Board(8, 8)
    rook = make_piece(0, 0)
    snapshot = GameSnapshot.from_pieces([rook], False, board.rows, board.cols)
    sprite_loader = SpriteLoader()
    renderer = Renderer(sprite_loader)

    cached_before = sprite_loader.board_image(8, 8).img.copy()
    renderer.render(snapshot, now_ms=0)
    cached_after = sprite_loader.board_image(8, 8).img

    assert (cached_before == cached_after).all()


def test_render_twice_produces_independent_canvases():
    board = Board(8, 8)
    rook = make_piece(0, 0)
    snapshot = GameSnapshot.from_pieces([rook], False, board.rows, board.cols)
    renderer = Renderer(SpriteLoader())

    canvas1 = renderer.render(snapshot, now_ms=0)
    canvas2 = renderer.render(snapshot, now_ms=0)

    assert canvas1.img is not canvas2.img


def test_render_uses_moving_sprite_for_moving_piece():
    board = Board(8, 8)
    rook = make_piece(0, 0)
    rook.state = PieceState.MOVING
    snapshot = GameSnapshot.from_pieces([rook], False, board.rows, board.cols)
    renderer = Renderer(SpriteLoader())

    # Should not raise even though the piece is in a non-idle state — confirms the
    # "moving" -> "move" folder mapping resolves to an existing sprite set.
    canvas = renderer.render(snapshot, now_ms=0)
    assert canvas.img is not None

