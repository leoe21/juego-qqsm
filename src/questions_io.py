"""Guardar, exportar y validar el banco de preguntas."""
from __future__ import annotations

from pathlib import Path

from src.parser import Question, parse_questions, parse_questions_text

FORMAT_HELP = """
Cada pregunta debe seguir este formato (una pregunta por bloque):

```
1. Texto de la pregunta
A. Primera opción
B. Segunda opción
C. Tercera opción
D. Cuarta opción
Respuesta correcta: B
```

- El número puede ser cualquiera; al guardar se renumeran automáticamente.
- Las opciones pueden usar `A.` o `a.` (mayúsculas o minúsculas).
- Línea en blanco entre preguntas (opcional).
"""

TEMPLATE = """1. Ejemplo: ¿Qué significa evangelio?
A. Buenas noticias
B. Reglas religiosas
C. Castigo divino
D. Esfuerzo humano
Respuesta correcta: A

2. Ejemplo: Según Juan 3:16, ¿qué hizo Dios?
A. Envió la ley
B. Envió a su Hijo
C. Creó ídolos
D. Olvidó al mundo
Respuesta correcta: B
"""


def questions_to_text(questions: list[Question]) -> str:
    blocks: list[str] = []
    for i, q in enumerate(questions, start=1):
        lines = [f"{i}. {q.text}"]
        for letter in "ABCD":
            lines.append(f"{letter}. {q.options[letter]}")
        lines.append(f"Respuesta correcta: {q.correct}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def load_questions(path: Path) -> list[Question]:
    if not path.exists():
        return []
    return parse_questions(path)


def save_questions(path: Path, questions: list[Question]) -> None:
    path.write_text(questions_to_text(questions), encoding="utf-8")


def renumber(questions: list[Question]) -> list[Question]:
    out: list[Question] = []
    for i, q in enumerate(questions, start=1):
        out.append(
            Question(
                number=i,
                text=q.text,
                options=dict(q.options),
                correct=q.correct,
            )
        )
    return out


def merge_questions(
    existing: list[Question], new_items: list[Question], mode: str
) -> list[Question]:
    if mode == "replace":
        combined = list(new_items)
    else:
        combined = list(existing) + list(new_items)
    return renumber(combined)


def validate_upload(text: str) -> tuple[list[Question], list[str]]:
    """Devuelve preguntas válidas y lista de errores."""
    errors: list[str] = []
    try:
        parsed = parse_questions_text(text)
    except Exception as exc:
        return [], [f"No se pudo leer el archivo: {exc}"]

    if not parsed:
        errors.append("No se encontró ninguna pregunta con el formato esperado.")
        return [], errors

    blocks = text.strip().split("\n\n")
    if len(parsed) < len([b for b in blocks if b.strip()]):
        errors.append(
            f"Se leyeron {len(parsed)} preguntas válidas; "
            "revisa que cada bloque tenga 4 opciones y respuesta correcta."
        )
    return parsed, errors
