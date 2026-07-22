"""Entry point for the network client.

Imports are re-exported so existing code (cli/shell.py) continues to work.
"""
from client.network.network_client import NetworkClient    # noqa: F401
from client.network.spectator_client import SpectatorClient  # noqa: F401

if __name__ == "__main__":
    NetworkClient().run()
