from model.piece import Kind, Color
from view.sprite_loader import SpriteLoader, CELL_SIZE


def test_frames_for_returns_five_frames():
    loader = SpriteLoader()
    frames = loader.frames_for(Kind.QUEEN, Color.WHITE, "idle")
    assert len(frames) == 5


def test_frames_for_returns_frames_resized_to_fit_a_cell():
    loader = SpriteLoader()
    frames = loader.frames_for(Kind.QUEEN, Color.WHITE, "move")
    for f in frames:
        assert f.img is not None
        h, w = f.img.shape[:2]
        assert h <= CELL_SIZE and w <= CELL_SIZE


def test_frames_for_caches_same_list_instance():
    loader = SpriteLoader()
    first  = loader.frames_for(Kind.ROOK, Color.BLACK, "idle")
    second = loader.frames_for(Kind.ROOK, Color.BLACK, "idle")
    assert first is second


def test_frames_for_different_states_are_not_conflated():
    loader = SpriteLoader()
    idle = loader.frames_for(Kind.KNIGHT, Color.WHITE, "idle")
    move = loader.frames_for(Kind.KNIGHT, Color.WHITE, "move")
    assert idle is not move


def test_board_image_loads_successfully():
    loader = SpriteLoader()
    board = loader.board_image(rows=8, cols=8)
    assert board.img is not None


def test_board_image_matches_cell_grid_exactly():
    loader = SpriteLoader()
    board = loader.board_image(rows=8, cols=8)
    h, w = board.img.shape[:2]
    assert (w, h) == (8 * CELL_SIZE, 8 * CELL_SIZE)


def test_board_image_returns_cached_instance_for_same_size():
    loader = SpriteLoader()
    first  = loader.board_image(rows=8, cols=8)
    second = loader.board_image(rows=8, cols=8)
    assert first is second


def test_all_piece_kinds_and_colors_have_idle_sprites():
    loader = SpriteLoader()
    for kind in Kind:
        for color in Color:
            frames = loader.frames_for(kind, color, "idle")
            assert len(frames) == 5, f"expected 5 idle frames for {kind}/{color}"

