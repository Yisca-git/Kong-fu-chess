"""SpectatorSession: wires SpectatorClient (network) + RenderLoop (UI)."""
from __future__ import annotations
from engine.game_snapshot import GameSnapshot
from client.network.spectator_client import SpectatorClient
from client.ui.render_loop import RenderLoop

CONNECT_TIMEOUT = 10


class SpectatorSession(RenderLoop):
    """Composition root for a spectating client."""

    def __init__(self, username: str, game_id: int) -> None:
        super().__init__(window_name=f"Kong-Fu-Chess — Spectating #{game_id}")
        self._net = SpectatorClient(
            username=username,
            game_id=game_id,
            on_snapshot=self._on_snapshot_received,
        )

    def _ready_event(self):
        return self._net.ready

    def _start_ws_thread(self) -> None:
        self._net.start()

    def _on_snapshot_received(self, snap: GameSnapshot) -> None:
        self._snapshot = snap

    def run(self) -> None:
        self._start_ws_thread()
        if not self._net.ready.wait(timeout=CONNECT_TIMEOUT):
            print("[spectator] Could not connect to game.")
            return
        self._run_loop()
