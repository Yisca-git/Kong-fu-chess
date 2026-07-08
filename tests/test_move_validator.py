import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from board import Board
from move_validator import is_legal_move


def make_board(rows):
    return Board(rows)


class TestPawnMoves(unittest.TestCase):

    def test_single_step(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        self.assertTrue(is_legal_move('P', 6, 4, 5, 4, b))

    def test_double_step_from_start(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        self.assertTrue(is_legal_move('P', 6, 4, 4, 4, b))

    def test_double_step_blocked_not_start(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
            '. . . . . . . .',
        ])
        self.assertFalse(is_legal_move('P', 5, 4, 3, 4, b))

    def test_capture_diagonal(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . bP . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
            '. . . . . . . .',
        ])
        self.assertTrue(is_legal_move('P', 5, 4, 4, 3, b))

    def test_cannot_capture_empty_diagonal(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
            '. . . . . . . .',
        ])
        self.assertFalse(is_legal_move('P', 5, 4, 4, 3, b))

    def test_cannot_move_backward(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
            '. . . . . . . .',
        ])
        self.assertFalse(is_legal_move('P', 5, 4, 6, 4, b))


class TestKnightMoves(unittest.TestCase):

    def setUp(self):
        self.board = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . wN . . . .',
        ])

    def test_valid_l_shapes(self):
        self.assertTrue(is_legal_move('N', 7, 3, 5, 4, self.board))
        self.assertTrue(is_legal_move('N', 7, 3, 5, 2, self.board))
        self.assertTrue(is_legal_move('N', 7, 3, 6, 5, self.board))
        self.assertTrue(is_legal_move('N', 7, 3, 6, 1, self.board))

    def test_invalid_move(self):
        self.assertFalse(is_legal_move('N', 7, 3, 5, 5, self.board))

    def test_jumps_over_pieces(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . wN . . . .',
        ])
        self.assertTrue(is_legal_move('N', 7, 3, 5, 4, b))


class TestRookMoves(unittest.TestCase):

    def setUp(self):
        self.board = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . wR . . . .',
        ])

    def test_horizontal(self):
        self.assertTrue(is_legal_move('R', 7, 3, 7, 0, self.board))
        self.assertTrue(is_legal_move('R', 7, 3, 7, 7, self.board))

    def test_vertical(self):
        self.assertTrue(is_legal_move('R', 7, 3, 0, 3, self.board))

    def test_blocked(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. wP . wR . . . .',
        ])
        self.assertFalse(is_legal_move('R', 7, 3, 7, 0, b))

    def test_cannot_move_diagonal(self):
        self.assertFalse(is_legal_move('R', 7, 3, 5, 5, self.board))


class TestBishopMoves(unittest.TestCase):

    def setUp(self):
        self.board = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . wB . . . .',
        ])

    def test_diagonal_up_right(self):
        self.assertTrue(is_legal_move('B', 7, 3, 4, 6, self.board))

    def test_diagonal_up_left(self):
        self.assertTrue(is_legal_move('B', 7, 3, 4, 0, self.board))

    def test_cannot_move_straight(self):
        self.assertFalse(is_legal_move('B', 7, 3, 7, 6, self.board))
        self.assertFalse(is_legal_move('B', 7, 3, 4, 3, self.board))

    def test_blocked(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . wP . .',
            '. . . . . . . .',
            '. . . wB . . . .',
        ])
        self.assertFalse(is_legal_move('B', 7, 3, 4, 6, b))


class TestGeneralRules(unittest.TestCase):

    def test_cannot_capture_own_piece(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . wR . . wP .',
        ])
        self.assertFalse(is_legal_move('R', 7, 3, 7, 6, b))

    def test_cannot_move_to_same_square(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . wR . . . .',
        ])
        self.assertFalse(is_legal_move('R', 7, 3, 7, 3, b))

    def test_unknown_piece_type(self):
        b = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . wR . . . .',
        ])
        self.assertFalse(is_legal_move('X', 7, 3, 5, 3, b))


if __name__ == '__main__':
    unittest.main(verbosity=2)
