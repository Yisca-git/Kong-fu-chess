"""Central UI configuration constants.

All view-layer magic numbers live here — import from this module,
never redefine them in individual files.
"""

PANEL_W      = 200   # width in pixels of each side panel (left=White, right=Black)
CELL_SIZE    = 100   # pixels per board square — the single source of truth for UI sizing
TICK_MS      = 16    # main loop tick (~60 FPS)
LOG_FONT     = 0.4
LOG_COLOR    = (220, 220, 220)
HEADER_COLOR = (255, 255, 100)
MAX_LOG_ENTRIES = 20
WINDOW_NAME  = "Kong-Fu-Chess"
