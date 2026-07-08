import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from game import KungFuChess


def make_game(rows):
    return KungFuChess(rows)

def cell(game, row, col):
    return game._board.get(row, col)


class TestSelection(unittest.TestCase):

    def test_select_piece(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.select_or_move(6, 4)
        self.assertEqual(g.selected, (6, 4))

    def test_select_empty_square_does_nothing(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.select_or_move(4, 4)
        self.assertIsNone(g.selected)

    def test_reselect_same_color(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP wR . .',
            '. . . . . . . .',
        ])
        g.select_or_move(6, 4)
        g.select_or_move(6, 5)
        self.assertEqual(g.selected, (6, 5))

    def test_deselect_after_move_attempt(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.select_or_move(6, 4)
        g.select_or_move(4, 4)
        self.assertIsNone(g.selected)


class TestMovement(unittest.TestCase):

    def test_move_queued(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.select_or_move(6, 4)
        g.select_or_move(4, 4)
        self.assertEqual(len(g.pending_moves), 1)
        self.assertEqual(g.pending_moves[0]['to'], (4, 4))

    def test_piece_arrives_at_destination(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.select_or_move(6, 4)
        g.select_or_move(4, 4)
        g.handle_wait(1000)
        self.assertEqual(cell(g, 4, 4), 'wP')
        self.assertEqual(cell(g, 6, 4), '.')

    def test_cannot_move_piece_in_flight(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.select_or_move(6, 4)
        g.select_or_move(5, 4)
        g.select_or_move(5, 4)
        g.select_or_move(4, 4)
        self.assertEqual(len(g.pending_moves), 1)

    def test_pawn_promotion(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
        ])
        g.select_or_move(1, 4)
        g.select_or_move(0, 4)
        g.handle_wait(1000)
        self.assertEqual(cell(g, 0, 4), 'wQ')


class TestCapture(unittest.TestCase):

    def test_capture_king_ends_game(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . bK . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wR . . .',
        ])
        g.select_or_move(7, 4)
        g.select_or_move(4, 4)
        g.handle_wait(1000)
        self.assertTrue(g.game_over)

    def test_capture_non_king_does_not_end_game(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . bP . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wR . . .',
        ])
        g.select_or_move(7, 4)
        g.select_or_move(4, 4)
        g.handle_wait(1000)
        self.assertFalse(g.game_over)
        self.assertEqual(cell(g, 4, 4), 'wR')

    def test_no_moves_after_game_over(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . bK . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wR . . .',
        ])
        g.select_or_move(7, 4)
        g.select_or_move(4, 4)
        g.handle_wait(1000)
        g.select_or_move(4, 4)
        g.select_or_move(0, 4)
        self.assertEqual(len(g.pending_moves), 0)

    def test_friendly_fire_blocked(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
            '. . . . wR . . .',
            '. . . . . . . .',
        ])
        g.select_or_move(6, 4)
        g.select_or_move(4, 4)
        g.handle_wait(1000)
        self.assertEqual(cell(g, 6, 4), 'wR')
        self.assertEqual(cell(g, 4, 4), 'wP')


class TestJump(unittest.TestCase):

    def test_jump_makes_piece_airborne(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.jump(6, 4)
        self.assertEqual(cell(g, 6, 4), '.')
        self.assertEqual(len(g.airborne), 1)

    def test_jump_lands_back(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.jump(6, 4)
        g.handle_wait(1000)
        self.assertEqual(cell(g, 6, 4), 'wP')
        self.assertEqual(len(g.airborne), 0)

    def test_attacker_captured_by_jump(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . bR . . .',
        ])
        g.select_or_move(7, 4)
        g.select_or_move(6, 4)
        g.jump(6, 4)
        g.handle_wait(1000)
        self.assertEqual(cell(g, 6, 4), 'wP')
        self.assertEqual(cell(g, 7, 4), '.')

    def test_cannot_jump_moving_piece(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.select_or_move(6, 4)
        g.select_or_move(4, 4)
        g.jump(6, 4)
        self.assertEqual(len(g.airborne), 0)

    def test_cannot_jump_empty_square(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.jump(4, 4)
        self.assertEqual(len(g.airborne), 0)


class TestUILayer(unittest.TestCase):

    def test_handle_click_delegates_correctly(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.handle_click(400, 600)
        self.assertEqual(g.selected, (6, 4))

    def test_handle_jump_delegates_correctly(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.handle_jump(400, 600)
        self.assertEqual(len(g.airborne), 1)

    def test_handle_click_out_of_bounds(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        g.handle_click(9999, 9999)
        self.assertIsNone(g.selected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
