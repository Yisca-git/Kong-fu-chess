"""Generates synthetic sound effects for KungFu Chess.

Produces three .wav files in assets2/sounds/ using only Python stdlib:
  move.wav    — short soft click (low sine, fast decay)
  capture.wav — sharp impact (two tones mixed)
  jump.wav    — rising whoosh (frequency sweep)

Run once:
    py scripts/generate_sounds.py
"""
import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44100
OUT_DIR = Path(__file__).resolve().parent.parent / "assets2" / "sounds"


def _write_wav(path: Path, samples: list[float]) -> None:
    peak = max(abs(s) for s in samples) or 1.0
    normalized = [int(s / peak * 32767) for s in samples]
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(struct.pack(f"<{len(normalized)}h", *normalized))


def _sine(freq: float, duration: float, decay: float = 3.0) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    return [
        math.sin(2 * math.pi * freq * i / SAMPLE_RATE) * math.exp(-decay * i / SAMPLE_RATE)
        for i in range(n)
    ]


def _sweep(f0: float, f1: float, duration: float, decay: float = 2.0) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    return [
        math.sin(2 * math.pi * (f0 + (f1 - f0) * i / n) * i / SAMPLE_RATE)
        * math.exp(-decay * i / SAMPLE_RATE)
        for i in range(n)
    ]


def _mix(a: list[float], b: list[float]) -> list[float]:
    length = max(len(a), len(b))
    a += [0.0] * (length - len(a))
    b += [0.0] * (length - len(b))
    return [x + y for x, y in zip(a, b)]


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sounds = {
        "move.wav":    _sine(220, 0.25, decay=8.0),
        "capture.wav": _mix(_sine(440, 0.3, decay=10.0), _sine(330, 0.3, decay=6.0)),
        "jump.wav":    _sweep(200, 800, 0.35, decay=2.5),
    }
    for filename, samples in sounds.items():
        path = OUT_DIR / filename
        _write_wav(path, samples)
        print(f"  wrote {path}")
    print("Done.")
