"""WebSocket connection handlers: routing, play loop, spectator loop."""
from __future__ import annotations
import asyncio
import json
from websockets import ServerConnection
from websockets.connection import State as WsState

from model.position import Position
from server.network.protocol import decode_command, encode_snapshot
from server.db.db import get_user, get_all_users
from server.services.auth import register, login
from server.core.server_state import ServerState

TIMEOUT_POLL = 65


async def handle(ws: ServerConnection, state: ServerState) -> None:
    try:
        raw  = await asyncio.wait_for(ws.recv(), timeout=10)
        auth = json.loads(raw)
    except (asyncio.TimeoutError, json.JSONDecodeError):
        await ws.close(1008, "Auth timeout")
        return

    if auth.get("register"):
        ok, msg = register(auth.get("username", ""), auth.get("password", ""))
        await ws.send(json.dumps({"ok": ok, "msg": msg}))
        await ws.close()
        return

    if auth.get("login"):
        ok, msg = login(auth.get("username", ""), auth.get("password", ""))
        await ws.send(json.dumps({"ok": ok, "msg": msg}))
        await ws.close()
        return

    if auth.get("leaderboard"):
        rows = [{"username": r["username"], "elo": r["elo"]} for r in get_all_users()]
        await ws.send(json.dumps({"leaderboard": rows}))
        await ws.close()
        return

    username = auth.get("auth", "")
    user     = get_user(username)
    if not user:
        await ws.send(json.dumps({"error": "Unknown user. Please register first."}))
        await ws.close()
        return

    if auth.get("list_games"):
        await ws.send(json.dumps({"games": state.list_games()}))
        await ws.close()
        return

    watch_id = auth.get("watch")
    if watch_id is not None:
        await _watch_game(ws, state, watch_id, username)
        return

    rejoin_id = auth.get("rejoin")
    if rejoin_id is not None:
        assignment = state.find_user_game(username)
        if assignment and assignment[0] == rejoin_id:
            game_id, slot = assignment
            game = state.get_game(game_id)
            if game and state.reconnect.has_timer(game_id, slot):
                print(f"[server] {username} reconnected to game {game_id}")
                color = "white" if slot == 0 else "black"
                await ws.send(json.dumps({"assigned": color, "elo": user["elo"],
                                          "game_id": game_id, "reconnected": True}))
                await _play_game(ws, state, game_id, slot)
                return
        await ws.send(json.dumps({"error": "No active game to rejoin."}))
        await ws.close()
        return

    print(f"[server] {username} (ELO {user['elo']}) connected — entering queue")
    await ws.send(json.dumps({"assigned": "waiting", "elo": user["elo"]}))

    matched_event = state.register_waiting(ws)
    state.queue.enqueue(username, user["elo"], ws)

    try:
        wait_match = asyncio.ensure_future(matched_event.wait())
        wait_close = asyncio.ensure_future(ws.wait_closed())
        done, pending = await asyncio.wait(
            [wait_match, wait_close],
            timeout=TIMEOUT_POLL,
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
        if not done or wait_match not in done:
            state.queue.dequeue(username)
            state.unregister_waiting(ws)
            return
    finally:
        state.unregister_waiting(ws)

    assignment = state.ws_game(ws)
    if assignment is None:
        return
    game_id, slot = assignment

    if ws.state != WsState.OPEN:
        game = state.get_game(game_id)
        if game:
            await game.clear_slot(slot)
            state.reconnect.start_timer(game_id, slot)
        return

    await _play_game(ws, state, game_id, slot)


async def _watch_game(ws: ServerConnection, state: ServerState,
                      game_id: int, username: str) -> None:
    game = state.get_game(game_id)
    if game is None:
        await ws.send(json.dumps({"error": "Game not found."}))
        await ws.close()
        return
    async with game.lock:
        game.spectators.add(ws)
    print(f"[server] {username} watching game {game_id}")
    await ws.send(encode_snapshot(game.session.engine.snapshot()))
    try:
        await ws.wait_closed()
    finally:
        async with game.lock:
            game.spectators.discard(ws)
        print(f"[server] {username} stopped watching game {game_id}")


async def _play_game(ws: ServerConnection, state: ServerState,
                     game_id: int, slot: int) -> None:
    game = state.get_game(game_id)
    if game is None:
        return

    state.reconnect.cancel_timer(game_id, slot)
    await game.set_slot(slot, ws)
    await state._register_ws_game(ws, game_id, slot)

    if await game.wait_ready():
        if not game.session.is_running():
            game.session.start()
            print(f"[server] Game {game_id} started")
            await game.broadcast(encode_snapshot(game.session.engine.snapshot()))
    else:
        return

    try:
        async for message in ws:
            game = state.get_game(game_id)
            if game is None:
                break
            try:
                data = json.loads(message) if message.startswith('{') else None
                if data and data.get("disconnect"):
                    print(f"[server] slot {slot} voluntarily disconnected from game {game_id}")
                    await game.clear_slot(slot)
                    if not state.reconnect.has_timer(game_id, slot):
                        state.reconnect.start_timer(game_id, slot)
                        opp_ws = game.slots.get(1 - slot)
                        if opp_ws:
                            try:
                                await opp_ws.send(json.dumps({"opponent_disconnected": True}))
                            except OSError:
                                pass
                    break
                if state.reconnect.has_timer(game_id, 1 - slot):
                    continue  # opponent disconnected — ignore moves until resolved
                _color, src, dst = decode_command(message)
                src_pos = Position(*src)
                if dst is None:
                    result = game.session.engine.request_jump(src_pos)
                else:
                    result = game.session.engine.request_move(src_pos, Position(*dst))
                if not result.is_accepted:
                    await ws.send(json.dumps({"rejection": result.reason}))
            except Exception as e:
                await ws.send(json.dumps({"error": str(e)}))
    except Exception:
        pass  # connection dropped (ping timeout, network error, etc.)
    finally:
        print(f"[server] slot {slot} disconnected from game {game_id}")
        state.deregister_ws_game(ws)
        game = state.get_game(game_id)
        print(f"[server] finally: game={game}, forfeited={game.forfeited if game else 'N/A'}, game_over={game.session.engine.game_over if game else 'N/A'}")
        if game:
            await game.clear_slot(slot)
            if game.session.engine.game_over or game.forfeited:
                print(f"[server] finally: cleaning up game {game_id}")
                game.session.stop()
                await state.remove_game(game_id)
            elif not state.reconnect.has_timer(game_id, slot):
                print(f"[server] finally: starting reconnect timer for slot {slot}")
                state.reconnect.start_timer(game_id, slot)
                opp_ws = game.slots.get(1 - slot)
                if opp_ws:
                    try:
                        await opp_ws.send(json.dumps({"opponent_disconnected": True}))
                    except OSError:
                        pass
