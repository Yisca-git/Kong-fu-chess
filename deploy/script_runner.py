import io as _io
from game_engine import GameEngine
from game_snapshot import GameSnapshot
from controller import Controller
from board_parser import parse, validate
from board_printer import print_board
from real_time_arbiter import RealTimeArbiter
from rule_engine import RuleEngine
from rules_registry import RULES_BY_KIND
from script_parser import (
    parse_script, ClickCommand, JumpCommand, WaitCommand, PrintBoardCommand
)


def run_script(text):
    """Runs a DSL script and returns a list of (actual, expected) pairs for each print board."""
    board_text, commands = parse_script(text)

    if not validate(board_text):
        return []

    board, pieces = parse(board_text)
    rule_engine   = RuleEngine()
    arbiter       = RealTimeArbiter(board, RULES_BY_KIND)
    engine        = GameEngine(board, rule_engine, arbiter)
    controller    = Controller(engine, board.rows, board.cols)

    results = []

    for command in commands:
        if isinstance(command, ClickCommand):
            controller.handle_click(command.x, command.y)

        elif isinstance(command, JumpCommand):
            controller.handle_jump(command.x, command.y)

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
