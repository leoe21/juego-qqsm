"""Genera y gestiona efectos de sonido WAV para el juego."""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from src.config import AUDIO_DIR

SOUNDS_DIR = AUDIO_DIR
SAMPLE_RATE = 22050


def _write_wav(path: Path, samples: list[float], volume: float = 0.45) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for s in samples:
            val = max(-1.0, min(1.0, s * volume))
            frames.extend(struct.pack("<h", int(val * 32767)))
        wav.writeframes(frames)


def _tone(freq: float, duration: float, fade: float = 0.02) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out: list[float] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = min(1.0, t / fade) * min(1.0, (duration - t) / fade)
        out.append(env * math.sin(2 * math.pi * freq * t))
    return out


def _silence(duration: float) -> list[float]:
    return [0.0] * int(SAMPLE_RATE * duration)


def _concat(*parts: list[float]) -> list[float]:
    merged: list[float] = []
    for p in parts:
        merged.extend(p)
    return merged


def _sweep(start: float, end: float, duration: float) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out: list[float] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / max(n - 1, 1)
        freq = start + (end - start) * progress
        env = min(1.0, 8 * t) * min(1.0, 8 * (duration - t))
        out.append(env * math.sin(2 * math.pi * freq * t))
    return out


def _buzz(duration: float = 0.55) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out: list[float] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = min(1.0, 12 * t) * min(1.0, 12 * (duration - t))
        s = math.sin(2 * math.pi * 110 * t) + 0.5 * math.sin(2 * math.pi * 155 * t)
        out.append(env * s / 1.5)
    return out


def _fanfare() -> list[float]:
    notes = [523, 659, 784, 988, 784, 988, 1047]
    parts: list[list[float]] = []
    for i, f in enumerate(notes):
        parts.append(_tone(f, 0.22 if i < len(notes) - 1 else 0.5))
        parts.append(_silence(0.04))
    return _concat(*parts)


def _tension_loop() -> list[float]:
    """~8 s de tensión suave, pensado para repetir en bucle."""
    pattern = _concat(
        _tone(196, 1.2),
        _silence(0.15),
        _tone(247, 1.0),
        _silence(0.2),
        _tone(294, 1.4),
        _silence(0.35),
    )
    return _concat(pattern, pattern)


def ensure_sounds() -> None:
    """Crea los WAV si no existen."""
    catalog = {
        "click": lambda: _concat(_tone(880, 0.05)),
        "start": lambda: _concat(
            _sweep(220, 440, 0.35),
            _silence(0.05),
            _tone(523, 0.25),
            _tone(659, 0.35),
        ),
        "correct": lambda: _concat(
            _tone(523, 0.12),
            _silence(0.03),
            _tone(659, 0.12),
            _silence(0.03),
            _tone(784, 0.22),
        ),
        "wrong": _buzz,
        "lifeline": lambda: _concat(_sweep(600, 200, 0.4), _silence(0.05), _tone(440, 0.15)),
        "safe": lambda: _concat(_tone(440, 0.15), _tone(554, 0.15), _tone(659, 0.3)),
        "walk": lambda: _concat(_tone(392, 0.2), _tone(494, 0.25), _tone(587, 0.3)),
        "win": _fanfare,
        "tension": _tension_loop,
    }
    for name, builder in catalog.items():
        path = SOUNDS_DIR / f"{name}.wav"
        if not path.exists():
            _write_wav(path, builder())


def sound_path(name: str) -> Path:
    ensure_sounds()
    return SOUNDS_DIR / f"{name}.wav"
