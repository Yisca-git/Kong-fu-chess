import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from board_parser import parse_and_validate_board


def make_input(board_rows, commands=''):
    lines = ['Board:'] + list(board_rows) + ['Commands:']
    if commands:
        lines.append(commands)
    return '\n'.join(lines)


EMPTY_BOARD = [
    '. . . . . . . .',
    '. . . . . . . .',
    '. . . . . . . .',
    '. . . . . . . .',
    '. . . . . . . .',
    '. . . . . . . .',
    '. . . . . . . .',
    '. . . . . . . .',
]


class TestValidInput(unittest.TestCase):

    def test_valid_empty_board(self):
        result = parse_and_validate_board(make_input(EMPTY_BOARD))
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 8)

    def test_valid_board_with_pieces(self):
        rows = list(EMPTY_BOARD)
        rows[6] = '. . . . wP . . .'
        rows[0] = 'bK . . . . . . .'
        result = parse_and_validate_board(make_input(rows))
        self.assertIsNotNone(result)

    def test_returns_correct_rows(self):
        rows = list(EMPTY_BOARD)
        rows[7] = '. . . wR . . . .'
        result = parse_and_validate_board(make_input(rows))
        self.assertIn('wR', result[7].split())


class TestInvalidInput(unittest.TestCase):

    def test_empty_string_returns_none(self):
        self.assertIsNone(parse_and_validate_board(''))

    def test_none_returns_none(self):
        self.assertIsNone(parse_and_validate_board(None))

    def test_missing_board_header_returns_none(self):
        text = '\n'.join(EMPTY_BOARD) + '\nCommands:'
        self.assertIsNone(parse_and_validate_board(text))

    def test_missing_commands_header_returns_none(self):
        text = 'Board:\n' + '\n'.join(EMPTY_BOARD)
        self.assertIsNone(parse_and_validate_board(text))

    def test_row_width_mismatch_returns_none(self):
        rows = list(EMPTY_BOARD)
        rows[3] = '. . . .'
        self.assertIsNone(parse_and_validate_board(make_input(rows)))

    def test_unknown_piece_token_returns_none(self):
        rows = list(EMPTY_BOARD)
        rows[4] = '. . . . xZ . . .'
        self.assertIsNone(parse_and_validate_board(make_input(rows)))

    def test_invalid_color_returns_none(self):
        rows = list(EMPTY_BOARD)
        rows[4] = '. . . . rP . . .'
        self.assertIsNone(parse_and_validate_board(make_input(rows)))

    def test_invalid_piece_letter_returns_none(self):
        rows = list(EMPTY_BOARD)
        rows[4] = '. . . . wX . . .'
        self.assertIsNone(parse_and_validate_board(make_input(rows)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
