import pytest
from model.piece import Kind, Color
from view.sprites.sprite_library import SpriteLibrary
from view.config import CELL_SIZE


@pytest.fixture
def lib():
    return SpriteLibrary()


def test_get_state_returns_sprite_state(lib):
    state = lib.get_state("W", "Q", "idle")
    assert state is not None


def test_get_state_returns_independent_instances(lib):
    """Two calls must return separate objects so each piece has its own playback clock."""
    a = lib.get_state("W", "Q", "idle")
    b = lib.get_state("W", "Q", "idle")
    assert a is not b


def test_different_states_are_not_conflated(lib):
    idle = lib.get_state("W", "N", "idle")
    move = lib.get_state("W", "N", "moving")
    assert idle is not move


def test_engine_state_maps_to_folder(lib):
    # "moving" should resolve to the "move" folder — no FileNotFoundError
    state = lib.get_state("B", "R", "moving")
    assert state.name == "move"


def test_airborne_maps_to_jump_folder(lib):
    state = lib.get_state("W", "P", "airborne")
    assert state.name == "jump"


def test_get_state_by_kind_color_enum(lib):
    state = lib.get_state_by_kind_color(Kind.KING, Color.WHITE, "idle")
    assert state is not None


def test_board_image_loads(lib):
    img = lib.board_image(8, 8)
    assert img.img is not None


def test_board_image_exact_size(lib):
    img = lib.board_image(8, 8)
    h, w = img.img.shape[:2]
    assert (w, h) == (8 * CELL_SIZE, 8 * CELL_SIZE)


def test_board_image_cached(lib):
    a = lib.board_image(8, 8)
    b = lib.board_image(8, 8)
    assert a is b


def test_all_kinds_and_colors_load_idle(lib):
    for kind in Kind:
        for color in Color:
            state = lib.get_state_by_kind_color(kind, color, "idle")
            assert state is not None
