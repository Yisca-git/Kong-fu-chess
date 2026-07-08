from config import EMPTY


class Board:
    def __init__(self, raw_rows):
        self._grid = [row.split() for row in raw_rows]
        self.rows  = len(self._grid)
        self.cols  = len(self._grid[0]) if self.rows > 0 else 0

    def get(self, row, col):
        return self._grid[row][col]

    def set(self, row, col, value):
        self._grid[row][col] = value

    def is_empty(self, row, col):
        return self._grid[row][col] == EMPTY

    def in_bounds(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_path_clear(self, from_row, from_col, to_row, to_col):
        step_row = 0 if to_row == from_row else (1 if to_row > from_row else -1)
        step_col = 0 if to_col == from_col else (1 if to_col > from_col else -1)
        r, c = from_row + step_row, from_col + step_col
        while (r, c) != (to_row, to_col):
            if not self.is_empty(r, c):
                return False
            r += step_row
            c += step_col
        return True

    def snapshot(self):
        return [row[:] for row in self._grid]
