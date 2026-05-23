"""
¿Quién quiere ser millonario? — versión bíblica en Streamlit.
"""
import random
import time
from datetime import timedelta

import streamlit as st

from src.audio_assets import ensure_sounds
from src.config import get_questions_path
from src.parser import Question, parse_questions
from src.question_admin import render_question_admin
from src.questions_io import load_questions
from src.sound_player import queue_sound, render_audio, render_sound_controls

# Escalera de premios (16 niveles; casillas seguras en 5 y 10)
PRIZES = [
    100,
    200,
    500,
    1_000,
    2_000,  # seguro
    5_000,
    10_000,
    20_000,
    40_000,
    80_000,  # seguro
    160_000,
    320_000,
    500_000,
    750_000,
    900_000,
    1_000_000,
]
SAFE_LEVELS = {4, 9}  # índices 0-based → preguntas 5 y 10

LIFELINE_DURATIONS = {"publico": 20, "amigo": 30}


def init_session():
    defaults = {
        "phase": "menu",  # menu | playing | result
        "deck": [],
        "current_idx": 0,
        "score": 0,
        "guaranteed": 0,
        "lifelines": {"5050": True, "publico": True, "amigo": True},
        "hidden_options": set(),
        "lifeline_timer_duration": 0,
        "wrong_pick": None,
        "correct_pick": None,
        "game_over_reason": None,
        "sound_enabled": True,
        "music_enabled": True,
        "pending_sound": None,
        "stop_music": False,
        "feedback": None,  # None | "correct"
        "feedback_idx": 0,
        "view": "game",  # game | admin
        "lifeline_timer_end": None,
        "lifeline_timer_type": None,  # "publico" | "amigo"
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def start_game():
    all_q = parse_questions(get_questions_path())
    if not all_q:
        st.error("No se encontraron preguntas válidas en Preguntas.txt")
        return
    random.shuffle(all_q)
    st.session_state.phase = "playing"
    st.session_state.deck = all_q
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.guaranteed = 0
    st.session_state.lifelines = {"5050": True, "publico": True, "amigo": True}
    st.session_state.hidden_options = set()
    st.session_state.wrong_pick = None
    st.session_state.correct_pick = None
    st.session_state.game_over_reason = None
    st.session_state.feedback = None
    clear_lifeline_timer()
    queue_sound("start")


def current_question() -> Question | None:
    deck = st.session_state.deck
    idx = st.session_state.current_idx
    if idx < len(deck):
        return deck[idx]
    return None


def safe_amount_at(idx: int) -> int:
    """Premio garantizado si fallas en el nivel idx (0-based)."""
    for level in sorted(SAFE_LEVELS, reverse=True):
        if idx > level:
            return PRIZES[level]
    return 0


def end_game(won: bool, walked: bool = False):
    st.session_state.phase = "result"
    st.session_state.stop_music = True
    if walked:
        st.session_state.game_over_reason = "retirado"
        queue_sound("walk")
    elif won:
        st.session_state.game_over_reason = "millonario"
        queue_sound("win")
    else:
        st.session_state.game_over_reason = "incorrecto"
        queue_sound("wrong")


def reset_lifeline_hints():
    st.session_state.hidden_options = set()
    clear_lifeline_timer()


def clear_lifeline_timer():
    st.session_state.lifeline_timer_end = None
    st.session_state.lifeline_timer_type = None
    st.session_state.lifeline_timer_duration = 0


def lifeline_timer_remaining() -> int | None:
    end = st.session_state.get("lifeline_timer_end")
    if end is None:
        return None
    return max(0, int(end - time.time()))


def lifeline_timer_running() -> bool:
    remaining = lifeline_timer_remaining()
    return remaining is not None and remaining > 0


def start_lifeline_timer(lifeline_type: str):
    seconds = LIFELINE_DURATIONS[lifeline_type]
    st.session_state.lifeline_timer_type = lifeline_type
    st.session_state.lifeline_timer_duration = seconds
    st.session_state.lifeline_timer_end = time.time() + seconds
    st.session_state.lifelines[lifeline_type] = False
    queue_sound("lifeline")


def finish_lifeline_timer():
    clear_lifeline_timer()


def apply_5050(q: Question):
    wrong = [k for k in q.options if k != q.correct]
    random.shuffle(wrong)
    to_hide = wrong[:2]
    st.session_state.hidden_options = set(to_hide)
    st.session_state.lifelines["5050"] = False
    queue_sound("lifeline")


def check_answer(letter: str, q: Question):
    if st.session_state.get("lifeline_timer_end") is not None:
        finish_lifeline_timer()
    idx = st.session_state.current_idx
    if letter == q.correct:
        st.session_state.feedback = "correct"
        st.session_state.feedback_idx = idx
        passed_safe = idx in SAFE_LEVELS
        queue_sound("safe" if passed_safe else "correct")
    else:
        st.session_state.score = st.session_state.guaranteed or safe_amount_at(idx)
        st.session_state.wrong_pick = letter
        st.session_state.correct_pick = q.correct
        end_game(won=False)


def advance_after_correct():
    idx = st.session_state.feedback_idx
    st.session_state.score = PRIZES[min(idx, len(PRIZES) - 1)]
    if idx in SAFE_LEVELS:
        st.session_state.guaranteed = st.session_state.score
    st.session_state.current_idx = idx + 1
    st.session_state.feedback = None
    reset_lifeline_hints()
    if st.session_state.current_idx >= len(st.session_state.deck):
        end_game(won=True)


def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');

        .stApp {
            background: radial-gradient(ellipse at top, #1a237e 0%, #0d1117 55%, #000 100%);
        }

        h1, h2, h3, p, label, .stMarkdown {
            font-family: 'Outfit', sans-serif !important;
        }

        .game-title {
            text-align: center;
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1.15;
            background: linear-gradient(135deg, #ffd54f, #ff8f00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1.2rem;
        }

        .game-subtitle {
            text-align: center;
            color: #b0bec5;
            font-size: 1.05rem;
            margin-bottom: 1.5rem;
        }

        .game-subtitle strong {
            color: #ffd54f;
            font-weight: 700;
        }

        .prize-ladder {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 213, 79, 0.25);
            border-radius: 12px;
            padding: 0.6rem 0.9rem;
            margin: 0.15rem 0;
            font-size: 0.95rem;
            color: #eceff1;
        }

        .prize-active {
            background: linear-gradient(90deg, #ff8f00, #ffd54f) !important;
            color: #1a1a1a !important;
            font-weight: 700;
            border: none !important;
            box-shadow: 0 0 18px rgba(255, 213, 79, 0.45);
        }

        .prize-safe {
            border-left: 4px solid #66bb6a;
        }

        .feedback-ok {
            padding: 1rem;
            border-radius: 10px;
            background: rgba(102, 187, 106, 0.2);
            border: 1px solid #66bb6a;
            color: #c8e6c9;
            text-align: center;
            font-size: 1.1rem;
        }

        .feedback-bad {
            padding: 1rem;
            border-radius: 10px;
            background: rgba(239, 83, 80, 0.2);
            border: 1px solid #ef5350;
            color: #ffcdd2;
            text-align: center;
            font-size: 1.1rem;
        }

        .feedback-correct {
            text-align: center;
            padding: 1.5rem 1rem;
            margin: 1rem 0 1.5rem 0;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(102, 187, 106, 0.35), rgba(56, 142, 60, 0.2));
            border: 2px solid #66bb6a;
            box-shadow: 0 0 28px rgba(102, 187, 106, 0.35);
            animation: pulse-correct 1.2s ease-in-out infinite;
        }

        .feedback-correct-title {
            font-size: 2.4rem;
            font-weight: 800;
            color: #a5d6a7;
            margin: 0;
        }

        .feedback-correct-sub {
            font-size: 1.1rem;
            color: #e8f5e9;
            margin-top: 0.5rem;
        }

        @keyframes pulse-correct {
            0%, 100% { box-shadow: 0 0 28px rgba(102, 187, 106, 0.35); }
            50% { box-shadow: 0 0 42px rgba(102, 187, 106, 0.55); }
        }

        .lifeline-timer-box {
            text-align: center;
            padding: 1.2rem 1rem;
            margin: 1rem 0;
            border-radius: 14px;
            background: rgba(33, 150, 243, 0.15);
            border: 2px solid #42a5f5;
            box-shadow: 0 0 24px rgba(66, 165, 245, 0.25);
        }

        .lifeline-timer-label {
            font-size: 1.15rem;
            color: #90caf9;
            margin: 0 0 0.4rem 0;
        }

        .lifeline-timer-clock {
            font-size: 3rem;
            font-weight: 800;
            color: #ffd54f;
            margin: 0;
            letter-spacing: 0.05em;
        }

        .lifeline-timer-hint {
            font-size: 0.95rem;
            color: #b0bec5;
            margin-top: 0.5rem;
        }

        div[data-testid="stHorizontalBlock"] button {
            min-height: 3.2rem;
            font-weight: 600;
            border-radius: 10px !important;
        }

        .lifeline-used {
            opacity: 0.45;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_prize_ladder():
    idx = st.session_state.current_idx
    st.markdown("#### 💰 Escalera de premios")
    for i in range(len(st.session_state.deck) - 1, -1, -1):
        prize = PRIZES[min(i, len(PRIZES) - 1)]
        label = f"{i + 1:>2}. ${prize:,}"
        classes = "prize-ladder"
        if i in SAFE_LEVELS:
            classes += " prize-safe"
        if i == idx and st.session_state.phase == "playing":
            classes += " prize-active"
        st.markdown(f'<div class="{classes}">{label}</div>', unsafe_allow_html=True)


def render_lifeline_countdown():
    remaining = lifeline_timer_remaining()
    if remaining is None:
        return

    duration = st.session_state.get("lifeline_timer_duration") or 20
    t = st.session_state.get("lifeline_timer_type", "")
    if t == "publico":
        label = "👥 Consulta al público"
        hint = "Discutan en grupo con las personas (20 segundos)."
    else:
        label = "📞 Llamada a un amigo"
        hint = "Hablen con su amigo o equipo (30 segundos)."

    clock = f"0:{remaining:02d}"
    progress = 1 - (remaining / duration) if duration else 0

    st.markdown(
        f"""
        <div class="lifeline-timer-box">
            <p class="lifeline-timer-label">{label}</p>
            <p class="lifeline-timer-clock">{clock}</p>
            <p class="lifeline-timer-hint">{hint}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(progress, text=f"Tiempo restante · {remaining} s")

    if st.button("Terminar tiempo", use_container_width=True, key="lifeline_skip_timer"):
        finish_lifeline_timer()
        st.rerun()


@st.fragment(run_every=timedelta(seconds=1))
def lifeline_timer_fragment():
    """Actualiza solo el reloj sin duplicar toda la pantalla."""
    if not lifeline_timer_running():
        end = st.session_state.get("lifeline_timer_end")
        if end is not None and time.time() >= end:
            finish_lifeline_timer()
            st.rerun()
        return
    render_lifeline_countdown()


def render_lifelines(q: Question):
    st.markdown("#### 🎯 Comodines")
    c1, c2, c3 = st.columns(3)
    ll = st.session_state.lifelines
    timer_on = lifeline_timer_running()

    with c1:
        if ll["5050"] and not timer_on:
            if st.button("50 : 50", use_container_width=True, key="ll_5050"):
                queue_sound("click")
                apply_5050(q)
                st.rerun()
        else:
            st.button("50 : 50", use_container_width=True, disabled=True)

    with c2:
        if ll["publico"] and not timer_on:
            if st.button("👥 Público", use_container_width=True, key="ll_pub"):
                queue_sound("click")
                start_lifeline_timer("publico")
                st.rerun()
        else:
            st.button("👥 Público", use_container_width=True, disabled=True)

    with c3:
        if ll["amigo"] and not timer_on:
            if st.button("📞 Amigo", use_container_width=True, key="ll_amigo"):
                queue_sound("click")
                start_lifeline_timer("amigo")
                st.rerun()
        else:
            st.button("📞 Amigo", use_container_width=True, disabled=True)

def render_menu():
    st.markdown('<p class="game-title">¿Quién quiere ser millonario?</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            **Cómo jugar**
            - Responde preguntas de la Biblia y la doctrina estudiada.
            - Cada acierto sube en la escalera hasta **$1,000,000** (puntos).
            - Casillas **seguras** en las preguntas 5 y 10.
            - Comodines: **50:50**, **Público** (20 s) y **Amigo** (30 s) para consultar en vivo.
            - Puedes **retirarte** con lo acumulado antes de responder.
            """
        )
        render_sound_controls()
        if st.button("🎮 ¡Comenzar juego!", type="primary", use_container_width=True):
            queue_sound("click")
            start_game()
            st.rerun()

        n = len(load_questions(get_questions_path()))
        st.caption(f"{n} preguntas cargadas · orden aleatorio en cada partida")

        if st.button("📝 Gestionar preguntas", use_container_width=True):
            st.session_state.view = "admin"
            st.rerun()


def render_correct_feedback():
    idx = st.session_state.feedback_idx
    prize = PRIZES[min(idx, len(PRIZES) - 1)]
    extra = ""
    if idx in SAFE_LEVELS:
        extra = "<p class='feedback-correct-sub'>¡Casilla segura alcanzada!</p>"
    st.markdown(
        f"""
        <div class="feedback-correct">
            <p class="feedback-correct-title">✅ ¡Correcto!</p>
            <p class="feedback-correct-sub">Ganas <strong>${prize:,}</strong></p>
            {extra}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("➡️ Siguiente pregunta", type="primary", use_container_width=True):
        advance_after_correct()
        st.rerun()


def render_playing():
    if st.session_state.get("feedback") == "correct":
        q = current_question()
        if not q:
            return
        left, right = st.columns([1, 1])
        with left:
            st.markdown('<p class="game-title">¿Quién quiere ser millonario?</p>', unsafe_allow_html=True)
            render_correct_feedback()
        with right:
            render_prize_ladder()
            st.metric("Acumulado", f"${st.session_state.score:,}")
        return

    q = current_question()
    if not q:
        return

    idx = st.session_state.current_idx
    total = len(st.session_state.deck)
    prize_now = PRIZES[min(idx, len(PRIZES) - 1)]

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<p class="game-title">¿Quién quiere ser millonario?</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="game-subtitle">Pregunta {idx + 1} de {total} · '
            f'Premio: <strong>${prize_now:,}</strong></p>',
            unsafe_allow_html=True,
        )

        st.markdown(f"### {q.text}")

        timer_on = lifeline_timer_running()
        if timer_on:
            lifeline_timer_fragment()

        hidden = st.session_state.hidden_options
        letters = ["A", "B", "C", "D"]
        for i in range(0, 4, 2):
            c1, c2 = st.columns(2)
            for col, letter in zip((c1, c2), letters[i : i + 2]):
                with col:
                    if letter in hidden:
                        st.button(
                            f"{letter}) —",
                            disabled=True,
                            use_container_width=True,
                            key=f"opt_{letter}",
                        )
                    else:
                        if st.button(
                            f"{letter}) {q.options[letter]}",
                            use_container_width=True,
                            key=f"opt_{letter}",
                        ):
                            queue_sound("click")
                            check_answer(letter, q)
                            st.rerun()

        st.divider()
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🏦 Retirarme con lo ganado", use_container_width=True):
                queue_sound("click")
                end_game(won=False, walked=True)
                st.rerun()
        with b2:
            if st.button("🔄 Reiniciar", use_container_width=True):
                st.session_state.stop_music = True
                st.session_state.phase = "menu"
                st.rerun()

        render_lifelines(q)

    with right:
        render_prize_ladder()
        st.metric("Acumulado", f"${st.session_state.score:,}")
        if st.session_state.guaranteed:
            st.caption(f"Seguro: ${st.session_state.guaranteed:,}")
        st.divider()
        render_sound_controls()

def render_result():
    reason = st.session_state.game_over_reason
    score = st.session_state.score

    if reason == "millonario":
        st.balloons()
        st.success(f"🏆 ¡FELICITACIONES! Llegaste al millón: **${score:,}**")
    elif reason == "retirado":
        st.warning(f"🏦 Te retiraste con: **${score:,}**")
    else:
        st.error(f"❌ Respuesta incorrecta. Te llevas: **${score:,}**")
        wp = st.session_state.get("wrong_pick")
        cp = st.session_state.get("correct_pick")
        if wp and cp:
            st.markdown(f"Elegiste **{wp}** · La correcta era **{cp}**")

    if st.button("🎮 Jugar de nuevo", type="primary"):
        queue_sound("click")
        st.session_state.stop_music = True
        st.session_state.phase = "menu"
        st.session_state.wrong_pick = None
        st.session_state.correct_pick = None
        st.rerun()


def main():
    st.set_page_config(
        page_title="¿Quién quiere ser millonario? — Biblia",
        page_icon="📖",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()
    init_session()
    ensure_sounds()
    render_audio()

    if st.session_state.get("view") == "admin":
        render_question_admin()
    elif st.session_state.phase == "menu":
        render_menu()
    elif st.session_state.phase == "playing":
        render_playing()
    else:
        render_result()


if __name__ == "__main__":
    main()
