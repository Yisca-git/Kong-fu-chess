from config import TILE_SIZE, JUMP_DURATION, EMPTY, WHITE
from pieces import PIECE_TYPES
from board import Board
from move_validator import is_legal_move


class KungFuChess:
    def __init__(self, raw_rows):
        self._board        = Board(raw_rows)
        self.game_clock    = 0
        self.selected      = None
        self.pending_moves = []
        self.airborne      = []
        self.game_over     = False

    # ── private helpers ───────────────────────────────────────────────────

    def _piece_at(self, row, col):
        piece = self._board.get(row, col)
        if piece != EMPTY:
            return piece
        for jump in self.airborne:
            if jump['row'] == row and jump['col'] == col:
                return jump['piece']
        return EMPTY

    def _is_piece_moving(self, row, col):
        return any(m['from'] == (row, col) for m in self.pending_moves)

    def _has_opponent_moving(self, color):
        return any(m['piece'][0] != color for m in self.pending_moves)

    def _board_view_for(self, row, col, piece):
        """Returns a board proxy that makes an airborne piece visible at its square."""
        class _AirborneProxy:
            def __init__(self, base, r, c, p):
                self._base = base
                self._r, self._c, self._p = r, c, p
                self.rows, self.cols = base.rows, base.cols

            def get(self, row, col):
                if row == self._r and col == self._c and self._base.is_empty(row, col):
                    return self._p
                return self._base.get(row, col)

            def is_empty(self, row, col):
                return self.get(row, col) == EMPTY

            def is_path_clear(self, fr, fc, tr, tc):
                return self._base.is_path_clear(fr, fc, tr, tc)

        return _AirborneProxy(self._board, row, col, piece)

    def _try_capture_by_jump(self, to_r, to_c, piece_color, from_r, from_c, moving_piece):
        for jump in self.airborne:
            if (jump['row'] == to_r and jump['col'] == to_c
                    and jump['piece'][0] != piece_color
                    and jump['start'] <= self.game_clock <= jump['end']):
                if self._board.get(from_r, from_c) == moving_piece:
                    self._board.set(from_r, from_c, EMPTY)
                return True
        return False

    # ── arrival / landing processing ─────────────────────────────────────

    def _process_arrivals(self):
        remaining = []
        for move in sorted(self.pending_moves, key=lambda m: m['arrival']):
            if move['arrival'] != self.game_clock:
                remaining.append(move)
                continue

            from_r, from_c = move['from']
            to_r,   to_c   = move['to']
            moving_piece   = move['piece']
            piece_color    = moving_piece[0]

            if self._try_capture_by_jump(to_r, to_c, piece_color, from_r, from_c, moving_piece):
                continue

            target = self._board.get(to_r, to_c)
            if target != EMPTY and target[1] == 'K' and target[0] != piece_color:
                self.game_over = True

            if moving_piece[1] == 'P':
                last_row = 0 if piece_color == WHITE else (self._board.rows - 1)
                if to_r == last_row:
                    moving_piece = f"{piece_color}Q"

            if self._board.get(from_r, from_c) == move['piece']:
                self._board.set(from_r, from_c, EMPTY)
            self._board.set(to_r, to_c, moving_piece)

        self.pending_moves = remaining

    def _process_landings(self):
        still_airborne = []
        for jump in self.airborne:
            if jump['end'] > self.game_clock:
                still_airborne.append(jump)
            else:
                self._board.set(jump['row'], jump['col'], jump['piece'])
        self.airborne = still_airborne

    # ── public commands ───────────────────────────────────────────────────

    def select_or_move(self, row, col):
        if self.game_over:
            return

        clicked = self._piece_at(row, col)

        if self.selected is None:
            if clicked != EMPTY and not self._is_piece_moving(row, col):
                self.selected = (row, col)
            return

        cur_row, cur_col = self.selected
        selected = self._piece_at(cur_row, cur_col)

        if clicked != EMPTY and clicked[0] == selected[0]:
            if not self._is_piece_moving(row, col):
                self.selected = (row, col)
        else:
            board_view = self._board_view_for(cur_row, cur_col, selected)
            if is_legal_move(selected[1], cur_row, cur_col, row, col, board_view):
                if not self._has_opponent_moving(selected[0]):
                    duration = PIECE_TYPES[selected[1]].move_duration
                    self.pending_moves.append({
                        'piece':   selected,
                        'from':    (cur_row, cur_col),
                        'to':      (row, col),
                        'arrival': self.game_clock + duration,
                    })
            self.selected = None

    def handle_click(self, x, y):
        col, row = x // TILE_SIZE, y // TILE_SIZE
        if self._board.in_bounds(row, col):
            self.select_or_move(row, col)

    def jump(self, row, col):
        if self.game_over:
            return
        piece = self._board.get(row, col)
        if piece == EMPTY or self._is_piece_moving(row, col):
            return
        if any(j['row'] == row and j['col'] == col for j in self.airborne):
            return

        self.airborne.append({
            'piece': piece,
            'row':   row,
            'col':   col,
            'start': self.game_clock,
            'end':   self.game_clock + JUMP_DURATION,
        })
        self._board.set(row, col, EMPTY)

    def handle_jump(self, x, y):
        col, row = x // TILE_SIZE, y // TILE_SIZE
        if self._board.in_bounds(row, col):
            self.jump(row, col)

    def handle_wait(self, ms):
        target_time = self.game_clock + ms

        while self.game_clock < target_time and not self.game_over:
            next_event = target_time
            for m in self.pending_moves:
                if self.game_clock < m['arrival'] <= next_event:
                    next_event = m['arrival']
            for j in self.airborne:
                if self.game_clock < j['end'] <= next_event:
                    next_event = j['end']
            self.game_clock = next_event

            self._process_arrivals()
            self._process_landings()

    def print_board(self):
        snap = self._board.snapshot()
        for jump in self.airborne:
            r, c = jump['row'], jump['col']
            if snap[r][c] == EMPTY:
                snap[r][c] = jump['piece']
        for row in snap:
            print(' '.join(row))
