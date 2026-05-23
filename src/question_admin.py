"""Panel en Streamlit para gestionar el banco de preguntas."""
from __future__ import annotations

import streamlit as st

from src.config import get_questions_path
from src.parser import Question
from src.questions_io import (
    FORMAT_HELP,
    TEMPLATE,
    load_questions,
    merge_questions,
    questions_to_text,
    renumber,
    save_questions,
    validate_upload,
)

def render_question_admin():
    st.markdown('<p class="game-title">📝 Banco de preguntas</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="game-subtitle">Sube un .txt, pega desde Word/WhatsApp o agrega una por una</p>',
        unsafe_allow_html=True,
    )

    questions_path = get_questions_path()
    questions = load_questions(questions_path)
    st.metric("Preguntas en el juego", len(questions))

    tab_ver, tab_pegar, tab_subir, tab_agregar, tab_formato = st.tabs(
        ["Ver banco", "Pegar texto", "Subir archivo", "Agregar una", "Formato"]
    )

    with tab_ver:
        _render_view(questions)

    with tab_pegar:
        _render_paste(questions)

    with tab_subir:
        _render_upload(questions)

    with tab_agregar:
        _render_add_form(questions)

    with tab_formato:
        st.markdown(FORMAT_HELP)
        st.download_button(
            "⬇️ Descargar plantilla de ejemplo",
            data=TEMPLATE,
            file_name="plantilla_preguntas.txt",
            mime="text/plain",
            use_container_width=True,
        )
        if questions:
            st.download_button(
                "⬇️ Descargar banco actual",
                data=questions_to_text(questions),
                file_name="Preguntas.txt",
                mime="text/plain",
                use_container_width=True,
            )

    st.divider()
    if st.button("← Volver al menú del juego", use_container_width=True):
        st.session_state.view = "game"
        st.rerun()


def _render_view(questions: list[Question]):
    if not questions:
        st.info("Aún no hay preguntas. Usa **Pegar texto**, **Subir archivo** o **Agregar una**.")
        return

    for q in questions:
        with st.expander(f"{q.number}. {q.text[:70]}{'…' if len(q.text) > 70 else ''}"):
            for letter in "ABCD":
                mark = " ✅" if letter == q.correct else ""
                st.markdown(f"**{letter})** {q.options[letter]}{mark}")

    st.divider()
    st.markdown("##### Eliminar preguntas")
    labels = {q.number: f"{q.number}. {q.text[:50]}…" if len(q.text) > 50 else f"{q.number}. {q.text}" for q in questions}
    to_delete = st.multiselect(
        "Selecciona las que quieres quitar",
        options=list(labels.keys()),
        format_func=lambda n: labels[n],
    )
    if to_delete and st.button("🗑️ Eliminar seleccionadas", type="primary"):
        remaining = [q for q in questions if q.number not in to_delete]
        save_questions(get_questions_path(), renumber(remaining))
        st.success(f"Se eliminaron {len(to_delete)} pregunta(s). Total: {len(remaining)}")
        st.rerun()


def _render_import_preview(parsed: list[Question], errors: list[str], source: str):
    st.markdown(f"**Vista previa ({source}):** {len(parsed)} pregunta(s) válida(s)")
    if errors:
        for err in errors:
            st.warning(err)
    if parsed:
        with st.expander("Ver preguntas detectadas"):
            for q in parsed[:20]:
                st.caption(f"{q.number}. {q.text} → correcta: {q.correct}")
            if len(parsed) > 20:
                st.caption(f"… y {len(parsed) - 20} más")


def _render_import_actions(questions: list[Question], parsed: list[Question], key_prefix: str):
    if not parsed:
        st.info("No hay preguntas válidas para guardar. Revisa el formato en la pestaña **Formato**.")
        return

    mode = st.radio(
        "¿Qué hacer con estas preguntas?",
        options=["append", "replace"],
        format_func=lambda m: "Agregar al banco actual" if m == "append" else "Reemplazar todo el banco",
        horizontal=True,
        key=f"{key_prefix}_mode",
    )

    if mode == "replace":
        st.warning("Esto borrará las preguntas actuales y dejará solo las nuevas.")

    if st.button("💾 Guardar en el juego", type="primary", use_container_width=True, key=f"{key_prefix}_save"):
        final = merge_questions(questions, parsed, mode)
        save_questions(get_questions_path(), final)
        st.success(f"¡Listo! El banco tiene **{len(final)}** preguntas.")
        st.balloons()
        st.rerun()


def _render_paste(questions: list[Question]):
    st.markdown(
        """
        Copia tus preguntas desde **Word, WhatsApp, correo o cualquier documento**
        y pégalas aquí. Usa el **mismo formato** que el archivo `.txt` (ver pestaña **Formato**).
        """
    )
    with st.expander("Ver ejemplo para copiar"):
        st.code(TEMPLATE.strip(), language=None)

    raw = st.text_area(
        "Pega aquí una o varias preguntas",
        height=280,
        placeholder=(
            "1. ¿Qué significa evangelio?\n"
            "A. Buenas noticias\n"
            "B. Reglas religiosas\n"
            "C. Castigo divino\n"
            "D. Esfuerzo humano\n"
            "Respuesta correcta: A"
        ),
        key="paste_questions_area",
    )

    if not raw.strip():
        st.caption("Pega el texto arriba: la vista previa aparecerá automáticamente.")
        return

    parsed, errors = validate_upload(raw)
    _render_import_preview(parsed, errors, "texto pegado")
    _render_import_actions(questions, parsed, "paste")


def _render_upload(questions: list[Question]):
    st.markdown(
        """
        Sube un archivo **.txt** con el formato indicado en la pestaña **Formato**.
        Puedes **reemplazar** todo el banco o **agregar** al final.
        """
    )
    uploaded = st.file_uploader("Archivo de preguntas (.txt)", type=["txt"])

    if uploaded is None:
        return

    raw = uploaded.read().decode("utf-8")
    parsed, errors = validate_upload(raw)
    _render_import_preview(parsed, errors, "archivo")
    _render_import_actions(questions, parsed, "upload")


def _render_add_form(questions: list[Question]):
    st.markdown("Completa el formulario para añadir **una** pregunta al banco.")

    with st.form("add_question_form", clear_on_submit=True):
        text = st.text_area("Pregunta", placeholder="Ej: ¿Qué significa evangelio?")
        c1, c2 = st.columns(2)
        with c1:
            opt_a = st.text_input("Opción A")
            opt_c = st.text_input("Opción C")
        with c2:
            opt_b = st.text_input("Opción B")
            opt_d = st.text_input("Opción D")
        correct = st.selectbox("Respuesta correcta", ["A", "B", "C", "D"])
        submitted = st.form_submit_button("➕ Agregar pregunta", type="primary", use_container_width=True)

    if not submitted:
        return

    opts = {"A": opt_a.strip(), "B": opt_b.strip(), "C": opt_c.strip(), "D": opt_d.strip()}
    if not text.strip():
        st.error("Escribe el texto de la pregunta.")
        return
    if not all(opts.values()):
        st.error("Las cuatro opciones son obligatorias.")
        return

    new_q = Question(
        number=len(questions) + 1,
        text=text.strip(),
        options=opts,
        correct=correct,
    )
    updated = renumber(questions + [new_q])
    save_questions(get_questions_path(), updated)
    st.success(f"Pregunta agregada. Total en el banco: **{len(updated)}**")
    st.rerun()
