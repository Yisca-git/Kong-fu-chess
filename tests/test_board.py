import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from board import Board


def make_board(rows):
    return Board(rows)


class TestBoard(unittest.TestCase):

    def setUp(self):
        self.board = make_board([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
        ])

    def test_get_set(self):
        self.board.set(3, 3, 'wQ')
        self.assertEqual(self.board.get(3, 3), 'wQ')

    def test_is_empty(self):
        self.assertTrue(self.board.is_empty(0, 0))
        self.board.set(0, 0, 'wK')
        self.assertFalse(self.board.is_empty(0, 0))

    def test_in_bounds(self):
        self.assertTrue(self.board.in_bounds(0, 0))
        self.assertTrue(self.board.in_bounds(7, 7))
        self.assertFalse(self.board.in_bounds(-1, 0))
        self.assertFalse(self.board.in_bounds(8, 0))
        self.assertFalse(self.board.in_bounds(0, 8))

    def test_path_clear_horizontal(self):
        self.assertTrue(self.board.is_path_clear(4, 0, 4, 7))
        self.board.set(4, 3, 'wP')
        self.assertFalse(self.board.is_path_clear(4, 0, 4, 7))

    def test_path_clear_vertical(self):
        self.assertTrue(self.board.is_path_clear(0, 4, 7, 4))
        self.board.set(3, 4, 'bP')
        self.assertFalse(self.board.is_path_clear(0, 4, 7, 4))

    def test_path_clear_diagonal(self):
        self.assertTrue(self.board.is_path_clear(0, 0, 7, 7))
        self.board.set(3, 3, 'wB')
        self.assertFalse(self.board.is_path_clear(0, 0, 7, 7))

    def test_snapshot_is_independent(self):
        snap = self.board.snapshot()
        snap[0][0] = 'wK'
        self.assertEqual(self.board.get(0, 0), '.')


if __name__ == '__main__':
    unittest.main(verbosity=2)
