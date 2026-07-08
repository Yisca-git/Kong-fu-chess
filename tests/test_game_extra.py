import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import io
from game import KungFuChess


def make_game(rows):
    return KungFuChess(rows)

def cell(game, row, col):
    return game._board.get(row, col)


class TestPrintBoard(unittest.TestCase):

    def test_print_board_shows_pieces(self):
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
        out = io.StringIO()
        sys.stdout = out
        g.print_board()
        sys.stdout = sys.__stdout__
        self.assertIn('wP', out.getvalue())

    def test_print_board_shows_airborne_piece(self):
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
        out = io.StringIO()
        sys.stdout = out
        g.print_board()
        sys.stdout = sys.__stdout__
        self.assertIn('wP', out.getvalue())


class TestOpponentMoving(unittest.TestCase):

    def test_blocked_when_opponent_moving(self):
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . bR . . .',
            '. . . . . . . .',
            '. . . . wP . . .',
            '. . . . . . . .',
        ])
        # queue opponent move
        g.select_or_move(4, 4)
        g.select_or_move(5, 4)
        # white should be blocked while black is moving
        g.select_or_move(6, 4)
        g.select_or_move(5, 4)
        self.assertEqual(len(g.pending_moves), 1)
        self.assertEqual(g.pending_moves[0]['piece'], 'bR')

    def test_allowed_when_opponent_not_moving(self):
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
        self.assertEqual(len(g.pending_moves), 1)
        self.assertEqual(g.pending_moves[0]['piece'], 'wP')


class TestAirborneProxy(unittest.TestCase):

    def test_airborne_piece_can_still_move(self):
        # A piece that is airborne should be visible to move validation via the proxy
        g = make_game([
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . . . . .',
            '. . . . wR . . .',
            '. . . . . . . .',
        ])
        g.jump(6, 4)
        # piece is airborne — board square is empty, but select should still find it via _piece_at
        g.select_or_move(6, 4)
        self.assertEqual(g.selected, (6, 4))

    def test_cannot_jump_already_airborne_piece(self):
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
        g.jump(6, 4)
        self.assertEqual(len(g.airborne), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
