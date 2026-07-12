import io as _io
from engine.game_engine import GameEngine
from engine.game_snapshot import GameSnapshot
from input.controller import Controller
from text_io.board_parser import parse
from text_io.board_printer import print_board
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from rules.rules_registry import RULES_BY_KIND
from texttests.script_parser import (
    parse_script, ClickCommand, WaitCommand, PrintBoardCommand
)


def run_script(text: str) -> list[tuple[list[str], list[str]]]:
    """Runs a DSL script and returns a list of (actual, expected) pairs for each print board."""
    board_text, commands = parse_script(text)

    board, pieces = parse(board_text)
    rule_engine   = RuleEngine()
    arbiter       = RealTimeArbiter(board, RULES_BY_KIND)
    engine        = GameEngine(board, rule_engine, arbiter)
    controller    = Controller(engine, board.rows, board.cols)

    results: list[tuple[list[str], list[str]]] = []

    for command in commands:
        if isinstance(command, ClickCommand):
            controller.handle_click(command.x, command.y)

        elif isinstance(command, WaitCommand):
            engine.advance_time(command.ms)

        elif isinstance(command, PrintBoardCommand):
            buf = _io.StringIO()
            import sys
            old_stdout = sys.stdout
            sys.stdout = buf
            print_board(engine.snapshot())
            sys.stdout = old_stdout

            actual   = [l for l in buf.getvalue().splitlines() if l.strip()]
            expected = list(command.expected)
            results.append((actual, expected))

    return results
