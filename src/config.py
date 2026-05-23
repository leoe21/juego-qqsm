"""Rutas centralizadas del proyecto."""
from pathlib import Path

# Raíz del repositorio (carpeta biblia_game/)
ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
AUDIO_DIR = ASSETS_DIR / "audio"

QUESTIONS_PATH = DATA_DIR / "preguntas.txt"

# Compatibilidad si aún existe el nombre antiguo en data/
_LEGACY_QUESTIONS_PATH = DATA_DIR / "Preguntas.txt"


def get_questions_path() -> Path:
    if QUESTIONS_PATH.exists():
        return QUESTIONS_PATH
    if _LEGACY_QUESTIONS_PATH.exists():
        return _LEGACY_QUESTIONS_PATH
    return QUESTIONS_PATH
