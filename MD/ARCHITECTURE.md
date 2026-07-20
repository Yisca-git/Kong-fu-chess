# Kong-Fu-Chess Project Architecture

## Overview
Kong-Fu-Chess is a real-time chess game. Pieces move according to standard chess movement patterns, but moves are not instantaneous — every move has a physical duration. Both players act in parallel, with no turns.

---

## Layer Structure

The project is divided into independent layers. Each layer can be tested without the layers above it.

```
model/          — logical state only
rules/          — movement rules and legality
engine/         — application-service coordination
realtime/       — motion over time, jumps, and arrival events
input/          — input-to-command translation
text_io/        — board parsing and printing
texttests/      — runs textual DSL tests
```

---

## Layer Descriptions

### model/
**Responsibility:** Logical board state — positions, pieces, colors, kinds, and lifecycle states.

**Forbidden:** Pixels, clicks, rendering, movement rules, or timing.

| File | Contents |
|---|---|
| `position.py` | `Position(row, col)` — value object, `frozen dataclass` |
| `piece.py` | `Piece`, `Color`, `Kind`, `PieceState` (IDLE, MOVING, AIRBORNE, CAPTURED) |
| `board.py` | `Board` — owns the logical layout, based on `dict[Position, Piece]` |

---

### input/
**Responsibility:** Translating user input into game commands.

**Forbidden:** Chess legality, mutating the Board, rendering, or timing.

| File | Contents |
|---|---|
| `board_mapper.py` | `pixel_to_position(x, y)` — converts pixels to board cells |
| `controller.py` | `Controller` — manages selection, `handle_click`, and `handle_jump` |

---

### text_io/
**Responsibility:** Parsing a textual board definition and printing the logical board state.

**Forbidden:** Movement rules, executing commands, rendering, or test logic.

| File | Contents |
|---|---|
| `board_parser.py` | `parse(text)` — parses board text into a `Board` and a list of `Piece` |
| `board_printer.py` | `print_board(snapshot)` — prints a `GameSnapshot` as text |
| `command_parser.py` | `parse_commands(text)` — parses a Commands section into a list of tuples, used in `main.py` |

---

### rules/
**Responsibility:** Movement geometry for each piece kind, move-legality validation, and arrival behavior.

**Forbidden:** Mutating the Board, elapsed time, animation, rendering, or handling input.

| File | Contents |
|---|---|
| `piece_rules.py` | Abstract base class `PieceRules` with `legal_destinations` and `on_arrival` |
| `sliding.py` | Shared helper function for sliding in a direction |
| `rook_rules.py` | Horizontal and vertical sliding |
| `bishop_rules.py` | Diagonal sliding |
| `queen_rules.py` | Combination of `RookRules` and `BishopRules` |
| `knight_rules.py` | L-shaped jumps, ignores blockers |
| `king_rules.py` | One square in every direction |
| `pawn_rules.py` | One/two squares forward from the start, diagonal capture, promotion in `on_arrival` |
| `rules_registry.py` | `RULES_BY_KIND: dict[Kind, PieceRules]` mapping |
| `move_validation.py` | `MoveValidation(is_valid, reason)` — DTO |
| `rule_engine.py` | `RuleEngine.validate(board, source, destination, moving_origins)` |

---

### engine/
**Responsibility:** Application-service coordination — the public command boundary.

**Forbidden:** Piece-specific movement logic, pixel mapping, rendering, text parsing.

| File | Contents |
|---|---|
| `move_result.py` | `MoveResult(is_accepted, reason)` — DTO |
| `game_snapshot.py` | `GameSnapshot` + `PieceSnapshot` — read-only DTO for the Renderer |
| `game_engine.py` | `GameEngine` — coordinates between `RuleEngine`, `RealTimeArbiter`, `ArrivalResolver`, and `Board` |
| `arrival_resolver.py` | `ArrivalResolver` — applies motion arrivals and jump landings to the `Board`: captures, blocking, promotion (via `on_arrival`), and victory detection. The sole owner of board mutations on arrival/landing |

---

### realtime/
**Responsibility:** Active Motion and Jump objects and advancing simulated time. A pure timing scheduler — holds no reference to the `Board`.

**Forbidden:** Chess legality, clicks, rendering, script parsing, or mutating the `Board` (that's `engine.ArrivalResolver`'s job).

| File | Contents |
|---|---|
| `motion.py` | `Motion` — a single move with computed `arrival_time` and `ready_time` (`COOLDOWN_MS = 1000ms`) |
| `jump.py` | `Jump` — an in-place jump with computed `land_time` and `ready_time` (`JUMP_COOLDOWN_MS = 500ms`) |
| `real_time_arbiter.py` | `RealTimeArbiter` — manages motions, jumps, time advancement, and `_cooldowns`; delegates arrival/landing resolution to an injected `ArrivalHandler` (a local `Protocol`, implemented by `engine.ArrivalResolver`) |

---

### texttests/
**Responsibility:** Parsing and running textual DSL scripts for integration tests.

**Forbidden:** Game logic, mutating the Board, rendering, or real user input.

| File | Contents |
|---|---|
| `script_parser.py` | `parse_script(text)` — parses a `.kfc` file into `board_text` and a list of `Command` (ClickCommand, WaitCommand, PrintBoardCommand) |
| `script_runner.py` | `run_script(text)` — builds the entire stack (Board, RuleEngine, Arbiter, Engine, Controller) and runs the commands, returns a list of `(actual, expected)` |

---

## Test Structure

```
tests/
├── unit/                        — unit tests for each layer separately
│   ├── test_position.py
│   ├── test_board.py
│   ├── test_piece_rules.py
│   ├── test_rule_engine.py
│   ├── test_real_time_arbiter.py
│   ├── test_game_engine.py
│   ├── test_board_mapper.py
│   ├── test_controller.py
│   ├── test_board_parser.py
│   └── test_board_printer.py
└── integration/
    ├── scripts/                 — DSL scripts in .kfc format
    │   ├── 01_board_parsing.kfc
    │   ├── 02_click_to_move.kfc
    │   ├── 03_rook_moves.kfc
    │   ├── 04_invalid_moves.kfc
    │   ├── 05_capture.kfc
    │   └── 06_game_over.kfc
    └── test_text_scripts.py     — loads all .kfc files and runs them via script_runner
```

**Running the tests:**
```bash
py -m pytest tests/
```

**HTML report:**
```bash
py -m pytest tests/ --html=report.html --self-contained-html
```

---

## Architectural Decisions

### 1. Position as a frozen dataclass
**Decision:** `@dataclass(frozen=True)` with `row` and `col`.

**Reason:** `Position` is a value object — it should be immutable. `frozen=True` gives equality, `hash`, and automatic mutation blocking, which allows it to be used as a `dict` key.

---

### 2. Piece as a regular dataclass with Enum
**Decision:** A regular `@dataclass` (not `frozen`) with `Color`, `Kind`, `PieceState` as `Enum`.

**Reason:** `cell` and `state` change during the game, so it isn't `frozen`. `Enum` gives type safety and readability. There is no logic inside `Piece` — it's data only.

**Rejected:** An interface/base class per piece kind — unnecessary, because the difference between pieces is expressed only via `kind`, and the logic belongs to the `rules` layer.

---

### 3. Board based on dict[Position, Piece]
**Decision:** `Board` holds a `dict[Position, Piece]` instead of a 2D grid.

**Reason:** Direct O(1) access by position, simple emptiness checks, and no need to represent empty cells. Allows boards of different sizes easily.

---

### 4. PieceRules as a Strategy Pattern with an on_arrival hook
**Decision:** Abstract base class `PieceRules` with `legal_destinations(board, piece)` and `on_arrival(piece, board_rows)`.

**Reason:** The Strategy pattern allows adding a new piece kind without touching existing code — just a new class and a line in `RULES_BY_KIND`. `on_arrival` is an optional hook (default — does nothing), so only pieces with special arrival behavior implement it.

**Rejected:** A long `if/elif` by piece kind — hard to extend. A separate `PostMoveRules` class — unnecessary because the logic belongs to the specific piece.

---

### 5. sliding.py as a separate helper file
**Decision:** A `slide` function in its own file, imported by `RookRules` and `BishopRules`.

**Reason:** SRP — each file is responsible for one thing. DRY — the sliding logic is written once.

---

### 6. MoveValidation and MoveResult as separate DTOs with class attributes
**Decision:** Each DTO in its own file. The `reason` values are defined as string class attributes, not free-form strings.

**Reason:** Other layers use `MoveValidation` — if it lived in `rule_engine.py`, they'd need to import from it just for the DTO, creating an unnecessary dependency. Class attributes give readability and safety without the complexity of an Enum.

**Rejected:** An Enum for reasons — unnecessary complexity.

---

### 7. Board has no capture logic
**Decision:** `Board` exposes only `add_piece`, `remove_piece`, and `move_piece`. `move_piece` assumes the destination cell is free.

**Reason:** `Board` doesn't decide who captures whom — that's `ArrivalResolver`'s responsibility (see decision #22). The flow: `ArrivalResolver` detects a capture → `remove_piece` on the captured piece → `add_piece` on the capturing piece.

---

### 8. Parallel motion — targeted blocking for a specific piece
**Decision:** `request_move` blocks only if the **specific piece** is already in motion, not if there is any motion at all on the board.

**Reason:** Kong-Fu-Chess has no turns — both players move in parallel, and every piece is independent. Blanket blocking ("some motion exists") contradicts the game's core principle.

**_BoardWithoutMoving proxy:** `RuleEngine.validate` accepts `moving_origins: set[Position]` and uses a proxy that hides in-motion pieces from path checks — because a piece that left its cell shouldn't block a path.

**friendly_airborne:** `RuleEngine.validate` also accepts `friendly_airborne: set[Position]` — the cells of friendly airborne pieces. A cell a friendly piece jumped from is considered free for movement purposes, because that piece is no longer logically there. `GameEngine` supplies this via `arbiter.friendly_airborne_cells(piece.color)`.

---

### 9. Logical motion stays on the source cell until arrival
**Decision:** A moving piece logically stays on its source cell until it reaches its destination.

**Reason:** Keeps a single authoritative logical board state. `print board` is deterministic — before arrival it shows the old board, after arrival it shows the updated board.

---

### 10. Jump — the airborne piece is removed from the logical board
**Decision:** `GameEngine.request_jump` removes the piece from the `Board` and calls `RealTimeArbiter.start_jump`, which adds it to the `_jumps` list. `snapshot()` includes airborne pieces too so they appear in `print board`.

**Reason:** Clean separation — the logical board only represents pieces "on the ground". `RealTimeArbiter` is the only place that knows about airborne pieces (as timing state); `GameEngine`/`ArrivalResolver` are the only places that mutate the `Board` itself (see decision #22).

**Collision rule:** An attacker that arrives at an airborne piece's cell — the jumper captures the attacker (not the other way around). After `JUMP_DURATION` the piece lands back if the cell is free.

**Landing on an enemy:** A piece that lands on an enemy — the enemy is captured.

**Landing on a friendly piece:** A piece that lands on a friendly piece — the jumping piece is captured (it has nowhere to land). The friendly piece is unaffected. (Not yet implemented.)

---

### 11. arrival_time/land_time/ready_time computed inside Motion/Jump
**Decision:** `Motion.__post_init__` computes `arrival_time` and `ready_time`. `Jump.__post_init__` computes `land_time` and `ready_time`.

**Reason:** Each one knows the data needed for the computation — that's the natural place for it. Keeps `RealTimeArbiter` free of time computations.

**Constants:** `MS_PER_STEP = 1000ms` per cell-step. `JUMP_DURATION = 1000ms`. Diagonal movement uses `max(|dr|, |dc|)`, not Euclidean distance.

---

### 16. Encapsulation of RealTimeArbiter
**Decision:** Neither `GameEngine` nor `ArrivalResolver` access private fields of `RealTimeArbiter` (like `_jumps`). Instead, `RealTimeArbiter` exposes public methods.

**Reason:** Encapsulation principle — callers shouldn't know about `RealTimeArbiter`'s internal structure.

**Example:** `friendly_airborne_cells(color)` returns a `set[Position]` of friendly airborne pieces, instead of searching `_jumps` directly. Likewise, `ArrivalResolver` uses `airborne_jump_at`, `cancel_jump`, and `set_cooldown` instead of touching `_jumps`/`_cooldowns` directly.

---

### 17. Processing order of motions by arrival_time
**Decision:** Motions that arrive on the same tick are processed in ascending `arrival_time` order.

**Reason:** Whoever started moving first arrives first. `reversed` was arbitrary.

---

### 18. Friendly piece at destination — the moving piece stays at its origin
**Decision:** In `_handle_destination`, if the piece at the destination is friendly — the moving piece returns to IDLE at its origin and does not receive a cooldown.

**Reason:** The moving piece can't land on a friendly piece, but it also isn't penalized for it.

---

### 19. Splitting _resolve_arrival
**Decision:** `_resolve_arrival` was split into two methods: `_handle_airborne_enemy` and `_handle_destination`. Both now live on `engine.ArrivalResolver`, not `RealTimeArbiter` (see decision #22).

**Reason:** Two logically different cases — an airborne piece at the destination is handled differently from a piece on the ground.

- `_handle_airborne_enemy`: a moving piece arrives at a destination containing an airborne enemy piece — the jumper lands and captures the attacker.
- `_handle_destination`: normal handling — empty, enemy on the ground, or friendly.

---

### 20. Victory condition isolated in _is_victory
**Decision:** The logic "does capturing this piece end the game" is isolated in `_is_victory(piece)` on `engine.ArrivalResolver` (moved there together with the rest of arrival/landing resolution — see decision #22).

**Reason:** Separation of concerns — `RealTimeArbiter` shouldn't need to know about specific victory conditions, and `GameEngine` shouldn't need to dig into landing details.

---

### 15. Cooldown in RealTimeArbiter, not in Piece
**Decision:** `RealTimeArbiter` holds `_cooldowns: dict[str, int]` — mapping `piece.id` to the time when the piece is ready again. The check is exposed via `is_piece_on_cooldown` and `cooldown_remaining`; it's set via the public `set_cooldown(piece, ready_time)` method, called by `ArrivalResolver` after resolving an arrival/landing.

**Reason:** `Piece` is a pure model — it must not contain time knowledge. All time-related information belongs to the `realtime` layer. `GameEngine` checks `is_piece_on_cooldown` before `request_move` and `request_jump` and returns `"piece_on_cooldown"`.

**Values:** `COOLDOWN_MS = 1000ms` after a regular move. `JUMP_COOLDOWN_MS = 500ms` after a jump — shorter, as required.

**Rejected:** A `cooldown_until` field on `Piece` — brings time knowledge into the pure model. Also rejected: keying `_cooldowns` by Python's built-in `id(piece)` (object identity) — `piece.id` is the correct, stable domain identifier and was already available on `Piece`.

---

### 12. Controller only knows GameEngine
**Decision:** `Controller` receives a `GameEngine` in its constructor and uses only its public interface.

**Reason:** Dependency Rule principle — every layer only knows the layers beneath it. `Controller` sits above `GameEngine`, so it must not touch `Board` or `RealTimeArbiter` directly.

---

### 13. BoardMapper as a function, not a class
**Decision:** `pixel_to_position(x, y)` is a free function, not a class.

**Reason:** There's no state to keep — a simple conversion of `x // CELL_SIZE`, `y // CELL_SIZE`. A class would be over-abstraction.

---

### 14. BoardParser returns tuple[Board, list[Piece]]
**Decision:** `parse(text)` returns both together.

**Reason:** `Board` and `Piece` are created together and always needed together — no point splitting them.

---

## Movement Rules — Pawn
- White moves one row up (row-1), Black moves one row down (row+1)
- Double step from the starting row (row 6 for White, row 1 for Black) — only if the first step is free
- Diagonal capture forward only
- Promotion to Queen on reaching the last row — implemented in `on_arrival`
- No en passant

---

## Victory Condition
Actually capturing the opponent's king — there is no check, checkmate, or stalemate.

---

### 22. RealTimeArbiter split into a pure scheduler + engine.ArrivalResolver
**Decision:** `RealTimeArbiter` (in `realtime/`) holds no `Board` reference at all — it only tracks `Motion`/`Jump`/the clock/`_cooldowns`, and exposes `advance_time(ms, resolver)`, handing each due motion/jump to an injected `ArrivalHandler` (a local `Protocol` in `real_time_arbiter.py`). `engine.arrival_resolver.ArrivalResolver` implements that protocol and is the sole owner of all `Board` mutations on arrival/landing (captures, blocking, promotion via `on_arrival`, victory detection). `GameEngine` wires the two together and also performs the one immediate (non-scheduled) board mutation itself — removing a piece from the `Board` in `request_jump` before calling `arbiter.start_jump`.

**Reason:** Keeps `RealTimeArbiter` reusable as a pure timing mechanism, independent of board-mutation rules — if the game ever needed a non-real-time (turn-based) mode, only the scheduler would need replacing, while `ArrivalResolver`'s capture/victory logic would stay unchanged. It also means `realtime/` never needs to import from `engine/`, preserving the Dependency Rule in the direction that matters (the `Protocol` is defined in `realtime/`, and `engine/` depends on `realtime/`, not the other way around).

**Rejected:** Keeping `RealTimeArbiter` as both scheduler and board-mutator (the original design) — works, but permanently couples the timing mechanism to board-mutation rules, which is unnecessary coupling given the two concerns change for different reasons.
