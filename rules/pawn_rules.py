from model.board import Board
from model.piece import Piece
from model.position import Position
from model.piece import Color
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
