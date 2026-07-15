import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rules.rule_engine import RuleEngine
from rules.rules_registry import RULES_BY_KIND
from realtime.real_time_arbiter import RealTimeArbiter
from engine.game_engine import GameEngine
from engine.arrival_resolver import ArrivalResolver
from engine.score_keeper import ScoreKeeper
from input.controller import Controller
from text_io.board_parser import parse
from view.sprite_loader import SpriteLoader
from view.renderer import Renderer
from view.game_window import GameWindow

STARTING_POSITION = """Board:
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR
Commands:
"""


def main() -> None:
    board, _pieces = parse(STARTING_POSITION)

    rule_engine = RuleEngine()
    arbiter     = RealTimeArbiter()
    resolver    = ArrivalResolver(board, RULES_BY_KIND, arbiter, ScoreKeeper())
    engine      = GameEngine(board, rule_engine, arbiter, resolver, ScoreKeeper())
    controller  = Controller(engine, board.rows, board.cols)

    sprite_loader = SpriteLoader()
    renderer      = Renderer(sprite_loader)

    GameWindow(engine, controller, renderer).run()


if __name__ == "__main__":
    main()
