from model.piece import Kind
from rules.piece_rules import PieceRules
from rules.rook_rules import RookRules
from rules.bishop_rules import BishopRules
from rules.queen_rules import QueenRules
from rules.knight_rules import KnightRules
from rules.king_rules import KingRules
from rules.pawn_rules import PawnRules


RULES_BY_KIND: dict[Kind, PieceRules] = {
    Kind.ROOK:   RookRules(),
    Kind.BISHOP: BishopRules(),
    Kind.QUEEN:  QueenRules(),
    Kind.KNIGHT: KnightRules(),
    Kind.KING:   KingRules(),
    Kind.PAWN:   PawnRules(),
}
