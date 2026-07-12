from model.board import Board
from model.piece import Piece, Color, Kind
from model.position import Position
from rules.piece_rules import PieceRules


class PawnRules(PieceRules):
    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Returns forward step if empty, plus diagonal captures if occupied by an enemy."""
        forward = -1 if piece.color == Color.WHITE else 1
        destinations = set()

        step = Position(piece.cell.row + forward, piece.cell.col)
        if board.in_bounds(step) and board.is_empty(step):
            destinations.add(step)

        for dc in (-1, 1):
            capture = Position(piece.cell.row + forward, piece.cell.col + dc)
            if not board.in_bounds(capture):
                continue
            occupant = board.piece_at(capture)
            if occupant is not None and occupant.color != piece.color:
                destinations.add(capture)

        return destinations

    def on_arrival(self, piece: Piece, board_rows: int) -> None:
        """Promotes pawn to Queen if it reached the last row."""
        promotion_row = 0 if piece.color == Color.WHITE else board_rows - 1
        if piece.cell.row == promotion_row:
            piece.kind = Kind.QUEEN
