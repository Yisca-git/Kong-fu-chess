import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from board import Board
from move_validator import is_legal_move


def make_board(rows):
    return Board(rows)


class TestQueenMoves(unittest.TestCase):

    def setUp(self):
        self.board = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . wQ . . . .',
        ])

    def test_horizontal(self):
        self.assertTrue(is_legal_move('Q', 7, 3, 7, 7, self.board))
        self.assertTrue(is_legal_move('Q', 7, 3, 7, 0, self.board))

    def test_vertical(self):
        self.assertTrue(is_legal_move('Q', 7, 3, 0, 3, self.board))

    def test_diagonal(self):
        self.assertTrue(is_legal_move('Q', 7, 3, 4, 6, self.board))
        self.assertTrue(is_legal_move('Q', 7, 3, 4, 0, self.board))

    def test_blocked_horizontal(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . wQ wP . . .',
        ])
        self.assertFalse(is_legal_move('Q', 7, 3, 7, 6, b))

    def test_blocked_diagonal(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . wP . .',
            '. . . . . . . .',
            '. . . wQ . . . .',
        ])
        self.assertFalse(is_legal_move('Q', 7, 3, 4, 6, b))

    def test_invalid_move(self):
        # L-shape is not valid for queen — validator returns False before path check
        self.assertFalse(is_legal_move('Q', 7, 3, 6, 5, self.board))
        self.assertFalse(is_legal_move('Q', 7, 3, 5, 4, self.board))


class TestKingMoves(unittest.TestCase):

    def setUp(self):
        self.board = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . wK . . . .',
        ])

    def test_one_step_horizontal(self):
        self.assertTrue(is_legal_move('K', 7, 3, 7, 4, self.board))
        self.assertTrue(is_legal_move('K', 7, 3, 7, 2, self.board))

    def test_one_step_vertical(self):
        self.assertTrue(is_legal_move('K', 7, 3, 6, 3, self.board))

    def test_one_step_diagonal(self):
        self.assertTrue(is_legal_move('K', 7, 3, 6, 4, self.board))
        self.assertTrue(is_legal_move('K', 7, 3, 6, 2, self.board))

    def test_cannot_move_two_squares(self):
        self.assertFalse(is_legal_move('K', 7, 3, 7, 5, self.board))
        self.assertFalse(is_legal_move('K', 7, 3, 5, 3, self.board))

    def test_cannot_capture_own_piece(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . wK . . . .',
        ])
        self.assertFalse(is_legal_move('K', 7, 3, 6, 4, b))


if __name__ == '__main__':
    unittest.main(verbosity=2)
