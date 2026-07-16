from __future__ import annotations
from model.board import Board
from model.piece import Piece, Color, Kind
from model.position import Position

# Standard 8x8 starting layout — row 0 is Black's back rank, row 7 is White's back rank.
# Each entry: (color, kind, row, col)
_BACK_RANK = [Kind.ROOK, Kind.KNIGHT, Kind.BISHOP, Kind.QUEEN,
              Kind.KING, Kind.BISHOP, Kind.KNIGHT, Kind.ROOK]

BOARD_ROWS = 8
BOARD_COLS = 8


def build_starting_board() -> tuple[Board, list[Piece]]:
    """Returns a fresh Board and the 32 pieces in the standard chess starting position."""
    board  = Board(BOARD_ROWS, BOARD_COLS)
    pieces: list[Piece] = []

    for col, kind in enumerate(_BACK_RANK):
        _place(board, pieces, Color.BLACK, kind, row=0, col=col)
        _place(board, pieces, Color.BLACK, Kind.PAWN, row=1, col=col)
        _place(board, pieces, Color.WHITE, Kind.PAWN, row=6, col=col)
        _place(board, pieces, Color.WHITE, kind, row=7, col=col)

    return board, pieces


def _place(board: Board, pieces: list[Piece], color: Color, kind: Kind,
           row: int, col: int) -> None:
    piece = Piece(
        id=f"{color.value}{kind.value}{row}{col}",
        color=color,
        kind=kind,
        cell=Position(row, col),
    )
    board.add_piece(piece)
    pieces.append(piece)
