from config import TILE_SIZE, JUMP_DURATION, EMPTY, WHITE, KING_SYMBOL, PAWN_SYMBOL, PROMOTED_PIECE
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
        # Airborne pieces are removed from the board, so check both sources
        """Returns the piece at a square, including pieces currently airborne over it."""
        piece = self._board.get(row, col)
        if piece != EMPTY:
            return piece
        for jump in self.airborne:
            if jump['row'] == row and jump['col'] == col:
                return jump['piece']
        return EMPTY

    def _is_piece_moving(self, row, col):
        """Returns True if the piece at this square has a pending move in flight."""
        return any(m['from'] == (row, col) for m in self.pending_moves)

    def _has_opponent_moving(self, color):
        """Returns True if the opponent currently has any piece in motion."""
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
        # If an attacker arrives while an enemy piece is airborne over the same square,
        # the jumping piece lands on the attacker and captures it instead
        for jump in self.airborne:
            if (jump['row'] == to_r and jump['col'] == to_c
                    and jump['piece'][0] != piece_color
                    and jump['start'] <= self.game_clock <= jump['end']):
                if self._board.get(from_r, from_c) == moving_piece:
                    self._board.set(from_r, from_c, EMPTY)
                return True
        return False

    def _is_king_capture(self, target, piece_color):
        """Returns True if the target piece is an enemy king."""
        return target != EMPTY and target[1] == KING_SYMBOL and target[0] != piece_color

    def _apply_promotion(self, piece, to_r):
        """Returns the promoted piece symbol if a pawn reached the last row, otherwise the original piece."""
        if piece[1] != PAWN_SYMBOL:
            return piece
        last_row = 0 if piece[0] == WHITE else (self._board.rows - 1)
        return f"{piece[0]}{PROMOTED_PIECE}" if to_r == last_row else piece

    # ── arrival / landing processing ─────────────────────────────────────

    def _process_arrivals(self):
        """Resolves all moves whose arrival time matches the current game clock."""
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
            if self._is_king_capture(target, piece_color):
                self.game_over = True

            moving_piece = self._apply_promotion(moving_piece, to_r)

            # Only clear the source square if the piece hasn't already been removed
            # (e.g. captured mid-flight by another move resolving at the same tick)
            if self._board.get(from_r, from_c) == move['piece']:
                self._board.set(from_r, from_c, EMPTY)
            self._board.set(to_r, to_c, moving_piece)

        self.pending_moves = remaining

    def _process_landings(self):
        """Places airborne pieces back on the board once their jump window expires."""
        still_airborne = []
        for jump in self.airborne:
            if jump['end'] > self.game_clock:
                still_airborne.append(jump)
            else:
                self._board.set(jump['row'], jump['col'], jump['piece'])
        self.airborne = still_airborne

    # ── public accessors ──────────────────────────────────────────────────

    def cell_at(self, row, col):
        """Returns the piece symbol at the given square, including airborne pieces."""
        return self._piece_at(row, col)

    def board_cell_at(self, row, col):
        """Returns the piece symbol at the given square on the physical board only."""
        return self._board.get(row, col)

    def pending_count(self):
        """Returns the number of moves currently in flight."""
        return len(self.pending_moves)

    def pending_destination(self, index):
        """Returns the destination square of the pending move at the given index."""
        return self.pending_moves[index]['to']

    def pending_piece(self, index):
        """Returns the piece symbol of the pending move at the given index."""
        return self.pending_moves[index]['piece']

    def airborne_count(self):
        """Returns the number of pieces currently airborne."""
        return len(self.airborne)

    # ── public commands ───────────────────────────────────────────────────

    def select_or_move(self, row, col):
        """Selects a piece or moves the selected piece to the target square."""
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
        """UI entry point: converts pixel coordinates to a board square and delegates to select_or_move."""
        col, row = x // TILE_SIZE, y // TILE_SIZE
        if self._board.in_bounds(row, col):
            self.select_or_move(row, col)

    def jump(self, row, col):
        """Makes a piece airborne at its current square, allowing it to dodge incoming attackers."""
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
        """UI entry point: converts pixel coordinates to a board square and delegates to jump."""
        col, row = x // TILE_SIZE, y // TILE_SIZE
        if self._board.in_bounds(row, col):
            self.jump(row, col)

    def handle_wait(self, ms):
        """Advances the game clock by ms, resolving all arrivals and landings in order."""
        target_time = self.game_clock + ms

        while self.game_clock < target_time and not self.game_over:
            # Jump to the next event (arrival or landing) rather than ticking ms by ms
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
        """Prints the board to stdout, overlaying airborne pieces onto their squares."""
        snap = self._board.snapshot()
        for jump in self.airborne:
            r, c = jump['row'], jump['col']
            if snap[r][c] == EMPTY:
                snap[r][c] = jump['piece']
        for row in snap:
            print(' '.join(row))
