# Unified Graphics Implementation Spec — Kong-Fu-Chess

> This document unifies [ARCHITECTURE.md](ARCHITECTURE.md), [kong_fu_chess_requirements.md](kong_fu_chess_requirements.md), and [kong_fu_chess_ui_plan.md](kong_fu_chess_ui_plan.md) into a single, authoritative spec used to actually build the graphics. It contains no new information — only a consolidation and filtering of what's relevant to building the view.

---

## 1. What already exists (core, do not touch)

The project is built in independent layers (see ARCHITECTURE.md): `model/ → rules/ + realtime/ → engine/ → input/ + text_io/`. The new `view/` layer sits **on top of** `engine/` and `input/` only, and knows nothing about the layers beneath them.

**view/'s reading boundary:** only `engine.game_snapshot.GameSnapshot` (a read-only DTO) and `input.controller.Controller` (to send commands). `view` must not import `Board`, `RealTimeArbiter`, or `RuleEngine` directly — this is the project's existing Dependency Rule, and it must not be violated.

The existing `PieceState` (IDLE, MOVING, AIRBORNE, CAPTURED) + the `COOLDOWN_MS`/`JUMP_COOLDOWN_MS` distinction (ARCHITECTURE.md decision #15) are the basis for animation mapping — we are not building a new time model.

---

## 2. Binding Design Principles (from requirements.md §4, applied here)

1. **Measured flexibility, not overkill** — we are not building infrastructure for Score/move-log "just in case"; it's deferred to a separate plan (see §6 below). We are not building an overly generic animation engine before there's real use for it.
2. **Separation between known-today and expected-tomorrow** — sprite loading must be generic enough to support a future piece like the "Drone" (requirement 3.2) without a rewrite, since this is a known-in-advance extension.
3. **Server as the source of truth** — not directly relevant to view at this stage (relevant to Phase 6, deferred).

---

## 3. Technical findings on the `Img` library (must know before implementation)

Repo: [KamaTechOrg/CTD26](https://github.com/KamaTechOrg/CTD26) — **the only graphics library allowed** (no PyGame/SFML/LWJGL).

| `Img` method | Purpose |
|---|---|
| `read(path, size=None, keep_aspect=False, interpolation=...)` | Loads an image, optional resize, returns `self` (chainable) |
| `draw_on(other_img, x, y)` | alpha-blend onto another canvas, at a pixel position |
| `put_text(txt, x, y, font_size, color, thickness)` | Writes text |
| `show()` | **blocking** (`waitKey(0)`) — not for use in a live game loop |

**Critical gap:** `Img` has no API for mouse clicks/keyboard/non-blocking loop. Solution: a single file (`view/game_window.py`) talks to `cv2` directly, solely for this purpose — all actual drawing still goes exclusively through `Img` (confirmed with the user).

**Existing assets in CTD26 (to be copied, not live-linked):**
- `board.png` — board background.
- `pieces1/<KindLetter><ColorLetter>/states/{idle,move,jump,short_rest,long_rest}/sprites/<n>.png` — matches almost 1:1 to the existing `PieceState` + short/long rest distinction.

---

## 4. File structure to build

```
assets/pieces/<KindLetter><ColorLetter>/states/{idle,move,jump,short_rest,long_rest}/sprites/*.png   (copied from pieces1/)
assets/board.png                                                                                     (copied)
view/
  img.py            — the original CTD26 file, vendored as-is
  sprite_loader.py   — loads+caches Img by (kind, color, state, frame); board_image()
  piece_animator.py  — (state, elapsed_ms) -> frame index; pure view-state keyed by piece id
  renderer.py        — render(snapshot: GameSnapshot) -> Img; composes board+pieces only
  game_window.py     — the only file that touches cv2 directly: window, setMouseCallback, non-blocking imshow+waitKey
  main_gui.py        — graphical entry point, parallel to the existing textual main.py (does not replace it)
```

**Build dependency order:** `assets` ← `sprite_loader` ← (`piece_animator` + `renderer`) ← `game_window` ← `main_gui`.

---

## 5. The one required change outside view/

Add an **additive** `state: str` field to `PieceSnapshot` in [engine/game_snapshot.py](engine/game_snapshot.py), derived from the piece's `PieceState`, so `piece_animator.py` can pick an animation without touching `RealTimeArbiter` directly. This change **must not** break any existing test (107 at the time of writing) — it's an added field only.

`cooldown_remaining_ms` and `motion_progress` (for smooth walking between cells) are **not** included at this stage — deferred, not needed to show basic idle/move/jump/rest.

---

## 6. Explicitly not in this phase (deliberately deferred)

Score, player names, and a move log with server timestamps (requirements 2.4–2.6) — require adding real logic to `engine/` (not just rendering). **A separate plan, after board+pieces+clicks+animations work end-to-end.**

---

## 7. Verification before closing the task

1. Running `view/main_gui.py` — board and pieces display, clicking moves a piece, idle/move/jump/rest animations correctly match the piece's actual state.
2. New unit tests for `sprite_loader` (caching) and `piece_animator` (frame selection) — pure functions, no real window.
3. `py -m pytest tests/ -q` keeps passing **unchanged** — this is the mandatory regression check before the task is considered done.
