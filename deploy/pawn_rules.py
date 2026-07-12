from board import Board
from piece import Piece, Color, Kind
from position import Position
from piece_rules import PieceRules


class PawnRules(PieceRules):
    def legal_destinations(self, board, piece):
        """Returns forward step if empty, plus diagonal captures if occupied by an enemy."""
        forward = -1 if piece.color == Color.WHITE else 1
        destinations = set()

        r, c = piece.cell.row + forward, piece.cell.col
        step = Position(r, c) if r >= 0 else None
        if step and board.in_bounds(step) and board.is_empty(step):
            destinations.add(step)

            start_row = board.rows - 2 if piece.color == Color.WHITE else 1
            r2 = piece.cell.row + 2 * forward
            double = Position(r2, c) if r2 >= 0 else None
            if double and piece.cell.row == start_row and board.in_bounds(double) and board.is_empty(double):
                destinations.add(double)

        for dc in (-1, 1):
            cr, cc = piece.cell.row + forward, piece.cell.col + dc
            if cr < 0 or cc < 0:
                continue
            capture = Position(cr, cc)
            occupant = board.piece_at(capture)
            if occupant is not None and occupant.color != piece.color:
                destinations.add(capture)

        return destinations

    def on_arrival(self, piece, board_rows):
        """Promotes pawn to Queen if it reached the last row."""
        promotion_row = 0 if piece.color == Color.WHITE else board_rows - 1
        if piece.cell.row == promotion_row:
            piece.kind = Kind.QUEEN
