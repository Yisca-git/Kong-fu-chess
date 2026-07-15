# Project Requirements Document — Kong-Fu-Chess

> This document is based on a transcript of the project's requirements video, organized and structured for a development agent/team.

---

## 1. General Description

Kong-Fu-Chess is a **real-time** chess game, in which **both sides move in parallel**, with no turns. Every piece takes physical time to move from its current square to its destination — the move is not instantaneous.

---

## 2. Basic Game Rules (mandatory for the first implementation phase)

### 2.1 Real-time movement
- No turns — both players can move pieces at any given moment, in parallel with each other.
- Every piece move has a **movement time** — the piece is "on the way" until it reaches its destination, and does not appear there instantly.

### 2.2 Cooldown
- After a piece finishes its move and reaches its destination, it needs to **rest** for a certain period, and only then can it move again.
- Visually: there is a rest animation — a "yellow background descending" over the piece, illustrating how much time remains until the piece can move again.

### 2.3 Victory condition
- **Victory is achieved only when the opponent's king is actually captured.**
- **There is no check and no checkmate** in this game — and they have no meaning: if a piece tries to move in order to capture the king, the king has time to flee before the piece reaches it (because a move takes physical time).
- As long as the opponent's king has not actually been captured — the game is not decided.

### 2.4 Move Notation
- Uses standard chess-like notation:
  - First letter = which piece kind moved (e.g. `N` = knight).
  - The next two letters/digits = the destination square (e.g. `C6`).
  - Example: `NC6` = the knight moved to square C6.
  - A pawn move with no piece kind specified (e.g. `E4`) — defaults to a pawn.
  - `0-0` — castling notation.
  - `X` — capture notation, e.g. if a piece captures a piece on a given square.
- **Unlike regular chess** (where there are two move columns — "White" and "Black" by turn), here:
  - There is a **separate move column for each player** (White on one side, Black on the other), because there are no turns.
  - **Every move displays a timestamp** of when it was performed — the time the command was received at the server (Server Time), not client time.

### 2.5 Score
- A score is displayed at the top of the board for each player, based on the value of pieces captured/achieved:
  - Pawn = 1 point
  - Knight = 3 points
  - Bishop = 3 points
  - Rook = 5 points
  - Queen = 9 points
  - King = infinite (capturing it ends the game)
- When a pawn reaches the last row and becomes a queen (Promotion) — the player receives the queen's points (9) **even if it did not capture a piece**, in addition to any points already accumulated.
- The score shows the difference/total in pieces between the two opponents.

### 2.6 Player Name Display
- Player names must be displayed (one name on top, one on the bottom) when playing against another player on the server.

---

## 3. Extended Requirements (beyond the basic game — to be taken into account in the design, even if not implemented immediately)

### 3.1 Jump / Dodge Command
An additional command that lets a piece "jump in place" (not actually move to another square, but a kind of local evasion):
- Typical use: if an enemy piece tries to capture my piece, I can order it to "jump in place".
- **The cooldown after a jump is shorter** than after a regular move to another square — because it isn't a "real" move on the board.
- Collision rules between a jump and an incoming attack:
  - If the attacking piece "enters" the square exactly while I'm jumping (i.e. I'm still in the jump process when it arrives) — **I land on it and capture it**.
  - If I land (finish the jump) **before** the attacker arrives — then while I'm resting (on cooldown), it can capture me as usual.
  - In other words: the relative timing between the jumper's landing moment and the attacker's arrival moment determines who captures whom.

### 3.2 Support for Additional Piece Types (Extensible Piece Types)
- A core design requirement: it should be **easy to add a new piece kind** to the system, without requiring extensive changes to existing code.
- Example of a new piece: a **"Drone"**
  - Moves slower than other pieces (relatively low movement speed).
  - Can move to any free square within a **±2 square range** from it (right/left/up/down, up to 2 squares in every direction — not just diagonal or straight lines, but any square within that square-shaped range).
- Practical implication: the "piece type" structure must be modular — movement patterns, speed, and special rules per piece must be easily extensible (e.g. via configuration/interface/separate class per piece kind) and not "carved in stone" in one central logic block.

### 3.3 Animations
- There's already a "rest" animation (the yellow background descending over the piece during cooldown).
- Additional animation requirements:
  - **Idle:** the piece should "breathe"/move slightly while standing still (not completely static).
  - **Walking:** when the piece moves, the movement should be shown visually — e.g. "walking with legs" or hops, so you can visually see how the piece moves.
  - **Actual resting:** when the piece rests (on cooldown), a different animation should be shown that expresses resting.
- **Flexibility requirement:** the animation system should be built so it's **easy to swap/update animations** in the future.
- You can start with simple animations (e.g. basic color/shape change) and upgrade later to more detailed animations.

### 3.4 Server Architecture and Load Support (Scalability — a system requirement, not a game-logic requirement)
This is a requirement that isn't part of the game logic itself, but a requirement on the **system** (the surrounding infrastructure):
- The server should be designed so that it could theoretically **scale to support millions of simultaneous players**.
- A **matchmaking** mechanism is required — a player connects to the server, and some mechanism pairs/matches players into games.
- Given a strong enough server, the system should support a very large number of concurrent users.
- **The client-server communication (networking) design must not create bottlenecks** that would harm the game experience and the flow of information (moves) between different players.
- Implication: the communication layer/protocol should be designed in advance with efficiency and scalability in mind, even if the initial implementation is basic.

---

## 4. Design Principles — important for the agent to follow

1. **Measured flexibility, not overkill:**
   - The code should be designed so it's **easy to add** the capabilities expected in advance (new pieces, new animations, new commands like jump).
   - **Do not** build unused abstractions, interfaces, and flexible layers "just in case" — overly flexible code that isn't actually used is a burden, not a benefit.
   - Goal: balance between clean, focused code and room for realistic, known future growth (the requirements in section 3).

2. **Separation between "what's known today" and "what's expected tomorrow":**
   - The requirements in section 2 are the core of the game — they must be implemented first and fully.
   - The requirements in section 3 don't need immediate implementation, but **must be taken into account during design** (data model, module architecture, piece/animation/networking interfaces) so that adding them later is simple and doesn't require a massive rewrite.

3. **Server as the Source of Truth:**
   - Every move is logged with the **server's timestamp**, not the client's — this is also the basis for determining who arrived first in case of a timing collision between two moves (e.g. the jump scenario in section 3.1).

---

## 5. Summary Table — Core vs. Extensions

| # | Requirement | Status | Note |
|---|---|---|---|
| 1 | Real-time movement, no turns | Mandatory — MVP | |
| 2 | Physical movement time between squares | Mandatory — MVP | |
| 3 | Cooldown after a move | Mandatory — MVP | |
| 4 | Victory = actually capturing the king | Mandatory — MVP | No check/checkmate/stalemate |
| 5 | Move notation + server timestamp | Mandatory — MVP | Separate column per player |
| 6 | Score based on piece values | Mandatory — MVP | Includes promotion bonus |
| 7 | Player name display | Mandatory — MVP | |
| 8 | Jump/dodge command | Future extension | Plan the timing logic in advance |
| 9 | Additional piece types (e.g. Drone) | Future extension | The piece core must be modular |
| 10 | Animations (idle, walking, resting) | Future extension | Start simple, upgrade later |
| 11 | Server scalability + Matchmaking | System requirement | Not part of the game logic itself |

---

*This document is meant to serve as a complete working basis for the development agent, combining both the basic game rules and the future extension requirements, along with the design principles the client emphasized (controlled flexibility, no overkill in abstractions).*
