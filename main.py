from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from text_io.board_parser import parse, validate as validate_board
from text_io.command_parser import parse_commands
from text_io.board_printer import print_board
from engine.game_engine import GameEngine
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from model.position import Position


def main():
    text = sys.stdin.read().strip()
    if not text:
        return

    if not validate_board(text):
        return

    board, _ = parse(text)
    engine   = GameEngine(board, RuleEngine(), RealTimeArbiter(board))
    commands = parse_commands(text)
    selected: Position | None = None

    for cmd in commands:
        if cmd[0] == "click":
            pos = Position(row=cmd[2] // 100, col=cmd[1] // 100)
            if selected is None:
                if engine.piece_at(pos):
                    selected = pos
            else:
                result = engine.request_move(selected, pos)
                selected = None
                if not result.is_accepted and engine.piece_at(pos):
                    selected = pos
        elif cmd[0] == "jump":
            pos = Position(row=cmd[2] // 100, col=cmd[1] // 100)
            engine.request_jump(pos)
        elif cmd[0] == "wait":
            engine.advance_time(cmd[1])
        elif cmd[0] == "print":
            print_board(engine.snapshot())


if __name__ == "__main__":
    main()
