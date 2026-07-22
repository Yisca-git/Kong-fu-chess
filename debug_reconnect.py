"""Debug script: starts server, connects two players, disconnects one, watches for timer."""
import asyncio
import json
import subprocess
import threading
import websockets

PY = r"C:\Users\Owner\AppData\Local\Programs\Python\Python313\python.exe"
WS = "ws://localhost:8765"


async def run_client(name: str, disconnect_after: float | None = None):
    print(f"[{name}] connecting...")
    try:
        async with websockets.connect(WS) as ws:
            await ws.send(json.dumps({"auth": name}))
            async for raw in ws:
                msg = json.loads(raw)
                assigned = msg.get("assigned")
                print(f"[{name}] << {list(msg.keys())}")
                if assigned and assigned != "waiting":
                    print(f"[{name}] matched as {assigned}")
                    break
            else:
                print(f"[{name}] connection closed before match")
                return
            if disconnect_after is not None:
                await asyncio.sleep(disconnect_after)
                print(f"[{name}] disconnecting now")
            else:
                print(f"[{name}] staying connected, reading until server closes...")
                async for raw in ws:
                    msg = json.loads(raw)
                    print(f"[{name}] post-match << {list(msg.keys())}")
    except Exception as e:
        print(f"[{name}] ended: {e}")


async def main():
    print("[test] starting server...")
    srv = subprocess.Popen(
        [PY, "-m", "server.network.ws_server"],
        cwd=r"C:\Users\Owner\Documents\Kong-fu-chess",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    threading.Thread(
        target=lambda: [print(f"[SERVER] {l}", end="") for l in srv.stdout],
        daemon=True,
    ).start()

    await asyncio.sleep(1.5)

    try:
        await asyncio.gather(
            run_client("aaa", disconnect_after=3),
            run_client("bbb", disconnect_after=None),
            return_exceptions=True,
        )
    finally:
        srv.terminate()
        print("[test] done")


asyncio.run(main())
