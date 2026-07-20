# Graphical UI Implementation Plan — Kong-Fu-Chess

## Overview
This document plans the addition of a graphical presentation layer (`view/`) on top of the existing game engine described in [ARCHITECTURE.md](ARCHITECTURE.md), using exclusively the `Img` drawing library (repo [KamaTechOrg/CTD26](https://github.com/KamaTechOrg/CTD26), OpenCV-based) — no other graphics library (not PyGame, not SFML, not LWJGL).

---

## Library Research Findings

### What `Img` provides (py/img.py)
| Method | Purpose |
|---|---|
| `read(path, size=None, keep_aspect=False, interpolation=...)` | Loads an image file into `self.img`, with optional resize. Returns `self` (chainable) |
| `draw_on(other_img, x, y)` | Draws itself onto another canvas at a pixel position, with alpha-blend if there's a transparency channel |
| `put_text(txt, x, y, font_size, color, thickness)` | Writes text onto the image |
| `show()` | Displays a window — **blocking** (`cv2.waitKey(0)` + `destroyAllWindows`), not suitable for a live game loop |

**Critical limitation:** `Img` has no API for mouse clicks, keyboard, or a non-blocking render loop. This is the main gap the design needs to bridge.

### Existing graphical assets in the repo
- `board.png` at the repo root — board background image.
- `pieces1/` and `pieces2/` — two alternative sprite sets. Each piece is in a folder `<KindLetter><ColorLetter>` (e.g. `QW`=White Queen, `RB`=Black Rook), and under it `states/{idle, move, jump, short_rest, long_rest}/sprites/<n>.png`.
- **Near-perfect match to our existing model:** `states` maps to our `PieceState` (IDLE/MOVING/AIRBORNE), and the `short_rest`/`long_rest` distinction matches exactly decision #15 in ARCHITECTURE.md (short cooldown after a jump, long after a move).

---

## Planned Layer Structure

```
view/           — graphical presentation only, on top of the existing engine/ and input/
assets/         — graphical assets copied from CTD26 (not a live dependency on the external repo)
```

### view/
**Responsibility:** Rendering game state to the screen, loading/caching sprites, mapping piece state to animation, managing the window and capturing mouse input.

**Forbidden:** Touching `Board`, `RealTimeArbiter`, or `RuleEngine` directly — reads only from `GameSnapshot` (a read-only DTO), consistent with the existing Dependency Rule.

| File | Contents | Depends on |
|---|---|---|
| `img.py` | The original file from CTD26, vendored as-is | — |
| `sprite_loader.py` | Loads+caches `Img` by (kind, color, state, frame); `board_image()` | assets/, img.py |
| `piece_animator.py` | Picks a frame index by (state, elapsed_ms) — pure view-state keyed by piece id | sprite_loader.py |
| `renderer.py` | `render(snapshot: GameSnapshot) -> Img` — composes board+pieces | sprite_loader.py, piece_animator.py |
| `game_window.py` | **The only file that touches cv2 directly** — window, `setMouseCallback`, non-blocking `imshow`+`waitKey` loop | renderer.py, input/controller.py |
| `main_gui.py` | Graphical entry point, parallel to the existing textual main.py | game_window.py |

---

## Development Phases

### Phase 0 — Assets
Copy `pieces1/` → `assets/pieces/`, `board.png` → `assets/board.png`, `py/img.py` → `view/img.py`. Add `opencv-python`+`numpy` to requirements. Map our `Kind`/`Color` to CTD26's `<KindLetter><ColorLetter>` prefix.

### Phase 1 — `view/sprite_loader.py` (*depends on Phase 0*)
Loads+caches sprites by (kind, color, state, frame) key. A pure file — no game logic, no cv2.

### Phase 2 — `view/renderer.py` (*depends on Phase 1*)
Composes a board+pieces canvas from `GameSnapshot` only, drawing via `draw_on` at `col*CELL_SIZE, row*CELL_SIZE`.

### Phase 3 — `view/piece_animator.py` (*depends on Phase 1, parallel to Phase 2*)
**Requires a small additive change:** add a `state: str` field to `PieceSnapshot` in [engine/game_snapshot.py](engine/game_snapshot.py), so view can pick an animation without touching `RealTimeArbiter` directly.

### Phase 4 — `view/game_window.py` + `view/main_gui.py` (*depends on Phases 2+3*)
Window management + click capture (mapped to the existing `Controller.handle_click`/`handle_jump`) + `advance_time`→`render`→display loop.

### Phase 5 — Deferred to a separate plan
Score, player names, and a move log with server timestamps (requirements 2.4–2.6 in [kong_fu_chess_requirements.md](kong_fu_chess_requirements.md)) — requires additions to `engine/`, not just `view/`. Deferred until board+pieces+clicks+animations work end-to-end.

---

## Design Decisions

### 1. Assets are vendored, not a live dependency on the CTD26 repo
**Decision:** Physically copy `pieces1/`, `board.png`, and `img.py` into `assets/`/`view/` in this project.

**Reason:** CTD26 isn't a pip package — there's no "clean" way to import it as a dependency. Copying ensures the project works standalone without a network/external-repo dependency.

---

### 2. `view/` reads only from `GameSnapshot`
**Decision:** `Renderer`, `PieceAnimator`, and `SpriteLoader` do not import `Board`, `RealTimeArbiter`, or `RuleEngine`.

**Reason:** Preserves the existing Dependency Rule — every layer depends only on the layers beneath it. Extending `PieceSnapshot` with a `state` field (next decision) is the correct way to pass information to the view, instead of exposing internals.

---

### 3. Additive extension of `PieceSnapshot` with a `state` field
**Decision:** Add a `state: str` field to the existing `PieceSnapshot`, derived from the piece's `PieceState`.

**Reason:** `view/piece_animator.py` needs to know whether to show idle/move/jump/rest without asking the Arbiter directly. An additive change (doesn't break existing code) — all existing tests (107 at the time of writing) will keep passing unchanged.

**Deferred (for now):** `cooldown_remaining_ms` and `motion_progress` per piece — would allow a more precise distinction between `short_rest`/`long_rest` and a smooth walking animation between cells, but aren't needed for the first phase (the piece is seen "walking in place" until arrival, consistent with existing decision #9 in ARCHITECTURE.md).

---

### 4. Only one file (`game_window.py`) talks to OpenCV directly
**Decision:** `game_window.py` is the only file in the project (besides the vendored `img.py`) that imports `cv2` directly — for `namedWindow`, `setMouseCallback`, and a non-blocking `imshow`+`waitKey(delay)` loop.

**Reason:** `Img` itself exposes no API for mouse clicks or a non-blocking render loop (its `show()` is blocking and unsuitable for a real-time game). Since `Img` itself is built on top of OpenCV, this isn't "another graphics library" — it's the same underlying stack — but all actual drawing (frame composition) still goes exclusively through `Img.read`/`draw_on`/`put_text`.

**Confirmed with the user** before writing this document.

---

### 5. Score/names/move log deferred to a separate plan
**Decision:** Requirements 2.4–2.6 (score, player names, move log with server timestamp) are not included in this plan.

**Reason:** They require adding real logic to `engine/` (move log, score calculator), not just rendering — a separate scope from "displaying the board and pieces". **Confirmed with the user.**

---

## Summary Table — Phases vs. Dependencies

| # | Phase | Depends on | Status |
|---|---|---|---|
| 0 | Copy assets (`assets/`, `view/img.py`) | — | Planned |
| 1 | `view/sprite_loader.py` | Phase 0 | Planned |
| 2 | `view/renderer.py` | Phase 1 | Planned |
| 3 | `view/piece_animator.py` + `PieceSnapshot.state` extension | Phase 1 | Planned |
| 4 | `view/game_window.py` + `view/main_gui.py` | Phases 2, 3 | Planned |
| 5 | Score/names/move log | — | Deferred, separate plan |

---

## Planned Verification
1. **Manual:** running `view/main_gui.py` — board and pieces display correctly, clicking moves a piece, idle/move/jump/rest animations display correctly per the piece's actual state.
2. **Unit:** `sprite_loader` (cache correctness, no duplicate I/O) and `piece_animator` (frame selection) — both pure functions, testable without a real window.
3. **Regression:** `py -m pytest tests/ -q` must keep passing unchanged — the `PieceSnapshot` extension is purely additive and doesn't change existing behavior.
