# Development Specification Guidelines: Multiplayer Game Server (KungFu Chess)

This document is designed to guide the AI Developer Agent in implementing the network infrastructure and backend services for a real-time KungFu Chess game. The core gameplay logic and graphics are already fully implemented and decoupled (Decoupled Layered Architecture). The agent's primary objective is to build the multiplayer game server and real-time communication layers following the steps detailed below.

---

## 🛠 Architectural Principles & Design Guidelines
1. **Client-Server Separation:** The central server acts as the authoritative source of truth. Clients are responsible solely for rendering the UI/graphics and sending player command events.
2. **Real-Time Communication:** Utilize **WebSockets** to establish high-throughput, bidirectional, full-duplex communication channels between the server and clients.
3. **Event-Driven Message Bus (Pub/Sub):** All inner-system communications (e.g., scoring updates, moves, sound events, logging, and animations) must be routed through a central Message Bus utilizing a publish/subscribe paradigm.
4. **Asynchronous / Non-blocking I/O:** Implement asynchronous patterns or proper thread safety to ensure continuous, simultaneous real-time actions from multiple players without causing server blocks.

---

## 🗺 Implementation Roadmap

### Phase A: Single-Process Server & Communication Foundation
* **Server Mission:** Establish a simple local WebSocket server (running on Localhost) handling asynchronous connection requests.
* **Connection Lifecycle:** The first client to connect is automatically assigned as `White`, and the second connected client is designated as `Black`.
* **Command Processing:** Define a concise text-based command format (e.g., `WQe2e5` representing a White Queen moving from e2 to e5). The server processes the command, evaluates game state validity, updates the board, and broadens the unified game state payload to both connected clients.

### Phase B: Authentication System & Persistent Database
* **Database Engine:** Integrate a lightweight **SQLite** database instance on the server side.
* **User Management (CLI/Shell):** Implement command-line interface prompts for registration (`Register`) and login (`Login`) inputs.
* **Security:** Enforce secure one-way password hashing algorithms (e.g., bcrypt or argon2) prior to committing credentials to the database.
* **Rating System (ELO):**
  * Newly registered accounts default to an initial ranking of **1200 ELO**.
  * Following game completions, the server must dynamically compute and persist revised ELO ratings for both participants using standard international formulas.

### Phase C: Matchmaking Queue
* **Play Button Integration:** When a player requests a match, place the user object into an in-memory Matchmaking Queue.
* **Match Logic:** The queue processor should continuously parse entries to match pairs whose ELO rating difference falls within a delta of **$\pm 100$ ELO points**.
* **Timeout Handling:** If the system fails to pair an eligible opponent within **60 seconds (1 minute)**, gracefully remove the player from the queue and send a "Matchmaking Timeout" error notification to the client.

### Phase D: Network Resilience, Disconnections & Synchronization
* **Auto-Resign Routine:**
  * If a player's active WebSocket connection terminates abruptly mid-game, invoke a countdown timer lasting **20 to 30 seconds**.
  * If the disconnected player fails to reconnect within this window, declare a technical forfeit. The disconnected player loses ELO rating points, and the remaining connected client is officially designated the winner.
* **State Synchronization:**
  * Upon a successful client reconnection within the active grace period, the server must transmit a comprehensive game snapshot.
  * The state payload must encapsulate current piece coordinates, full match notation history, and precise remaining Cooldown values per piece to restore an exact synchronized game state.

### Phase E: Room Management & Comprehensive Logging
* **Multi-Room Framework:**
  * Add support for creating distinct lobbies (generating a unique `Room ID`) or joining existing sessions via an explicit room token.
  * The first two clients entering the room fill the `White` and `Black` slots. All subsequent entrants are treated as passive `Viewers`, receiving read-only game state updates with no operational input rights.
* **Logging Engine:** Implement structured logging frameworks across both client and server nodes to capture connection states, WebSocket frames, and Message Bus payloads for debugging and audit purposes.

---

## 🎯 Task Execution Directive for the Agent:
Please implement this architecture incrementally. Begin exclusively with Phase A (establishing the core WebSocket server and Pub/Sub Event Bus). Proceed to subsequent persistence, matchmaking, and state synchronization phases only after validating base end-to-end communication stability.
