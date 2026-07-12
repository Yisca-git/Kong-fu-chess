from piece import Kind
from piece_rules import PieceRules
from rook_rules import RookRules
from bishop_rules import BishopRules
from queen_rules import QueenRules
from knight_rules import KnightRules
from king_rules import KingRules
from pawn_rules import PawnRules


RULES_BY_KIND = {
    Kind.ROOK:   RookRules(),
    Kind.BISHOP: BishopRules(),
    Kind.QUEEN:  QueenRules(),
    Kind.KNIGHT: KnightRules(),
    Kind.KING:   KingRules(),
    Kind.PAWN:   PawnRules(),
}
