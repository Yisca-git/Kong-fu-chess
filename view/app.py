"""Composition root for the graphical UI.

Builds every collaborator, wires DI, and runs the game loop.

Usage:
    py view/app.py
"""
from __future__ import annotations

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
from view.setup import build_starting_board
from view.sprites.sprite_library import SpriteLibrary
from view.renderer import Renderer
from view.game_window import GameWindow
from view.events.event_bus import EventBus
from view.events.events import MoveResolvedEvent, JumpResolvedEvent
from view.events.observers.score_observer import ScoreObserver
from view.events.observers.moves_log_observer import MovesLogObserver


def main() -> None:
    # --- engine stack ---
    board, _pieces = build_starting_board()
    score_keeper   = ScoreKeeper()
    arbiter        = RealTimeArbiter()
    rule_engine    = RuleEngine()
    resolver       = ArrivalResolver(board, RULES_BY_KIND, arbiter, score_keeper)
    engine         = GameEngine(board, rule_engine, arbiter, resolver, score_keeper,
                                white_name="Player 1", black_name="Player 2")
    controller     = Controller(engine, board.rows, board.cols)

    # --- observer wiring (S4A hook) ---
    bus            = EventBus()
    score_obs      = ScoreObserver()
    log_obs        = MovesLogObserver()
    bus.subscribe(MoveResolvedEvent, score_obs.on_move_resolved)
    bus.subscribe(JumpResolvedEvent, score_obs.on_jump_resolved)
    bus.subscribe(MoveResolvedEvent, log_obs.on_move_resolved)
    bus.subscribe(JumpResolvedEvent, log_obs.on_jump_resolved)
    resolver.add_settlement_listener(bus.publish)

    # --- rendering ---
    library  = SpriteLibrary()
    renderer = Renderer(library)

    GameWindow(engine, controller, renderer).run()


if __name__ == "__main__":
    main()
