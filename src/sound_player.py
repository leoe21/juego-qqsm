"""Reproduce sonidos en Streamlit (HTML5 + base64)."""
from __future__ import annotations

import base64

import streamlit as st
import streamlit.components.v1 as components

from src.audio_assets import ensure_sounds, sound_path

_BGM_B64: str | None = None


def _bgm_data_uri() -> str:
    global _BGM_B64
    if _BGM_B64 is None:
        ensure_sounds()
        _BGM_B64 = base64.b64encode(sound_path("tension").read_bytes()).decode("ascii")
    return f"data:audio/wav;base64,{_BGM_B64}"


def sounds_enabled() -> bool:
    return st.session_state.get("sound_enabled", True)


def music_enabled() -> bool:
    return st.session_state.get("music_enabled", True)


def queue_sound(name: str) -> None:
    if sounds_enabled():
        st.session_state.pending_sound = name


def render_audio() -> None:
    """Efectos puntuales + control de música de fondo."""
    pending = st.session_state.pop("pending_sound", None)
    if pending and sounds_enabled():
        b64 = base64.b64encode(sound_path(pending).read_bytes()).decode("ascii")
        components.html(
            f"""
            <script>
            (function() {{
              const a = new Audio("data:audio/wav;base64,{b64}");
              a.volume = 0.55;
              a.play().catch(() => {{}});
            }})();
            </script>
            """,
            height=0,
        )

    play_bgm = (
        st.session_state.get("phase") == "playing"
        and music_enabled()
    )
    stop_bgm = st.session_state.pop("stop_music", False)

    if stop_bgm or not play_bgm:
        components.html(
            """
            <script>
            (function() {
              const w = window.parent || window;
              if (w.__bibliaGameBgm) {
                w.__bibliaGameBgm.pause();
                w.__bibliaGameBgm = null;
              }
            })();
            </script>
            """,
            height=0,
        )
    elif play_bgm:
        uri = _bgm_data_uri()
        components.html(
            f"""
            <script>
            (function() {{
              const w = window.parent || window;
              if (!w.__bibliaGameBgm) {{
                const a = new Audio("{uri}");
                a.loop = true;
                a.volume = 0.16;
                a.play().catch(() => {{}});
                w.__bibliaGameBgm = a;
              }} else if (w.__bibliaGameBgm.paused) {{
                w.__bibliaGameBgm.play().catch(() => {{}});
              }}
            }})();
            </script>
            """,
            height=0,
        )


def render_sound_controls() -> None:
    st.session_state.sound_enabled = st.toggle(
        "🔊 Efectos de sonido",
        value=st.session_state.get("sound_enabled", True),
        key="toggle_sfx",
    )
    st.session_state.music_enabled = st.toggle(
        "🎵 Música de tensión",
        value=st.session_state.get("music_enabled", True),
        key="toggle_bgm",
    )
