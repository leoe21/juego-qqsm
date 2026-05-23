"""Parser para Preguntas.txt del juego tipo millonario."""
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Question:
    number: int
    text: str
    options: dict[str, str]  # A, B, C, D
    correct: str


def _normalize_letter(raw: str) -> str:
    return raw.strip().upper()[:1]


def parse_questions_text(text: str) -> list[Question]:
    """Parsea preguntas desde texto (archivo o carga en Streamlit)."""
    blocks = re.split(r"(?=\n\d+\.)", text.strip())
    questions: list[Question] = []

    option_re = re.compile(
        r"^([A-Da-d])[.\)\s\t]+(.+)$", re.IGNORECASE
    )
    answer_re = re.compile(
        r"respuesta\s+correcta\s*:\s*([A-Da-d])", re.IGNORECASE
    )

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue

        header = lines[0]
        m = re.match(r"^(\d+)\.\s*(.+)$", header)
        if not m:
            continue

        number = int(m.group(1))
        q_text = m.group(2).strip()
        options: dict[str, str] = {}
        correct = ""

        for line in lines[1:]:
            ans = answer_re.search(line)
            if ans:
                correct = _normalize_letter(ans.group(1))
                continue
            opt = option_re.match(line)
            if opt:
                letter = _normalize_letter(opt.group(1))
                options[letter] = opt.group(2).strip()

        if len(options) == 4 and correct in options:
            questions.append(
                Question(number=number, text=q_text, options=options, correct=correct)
            )

    return questions


def parse_questions(path: str | Path) -> list[Question]:
    text = Path(path).read_text(encoding="utf-8")
    return parse_questions_text(text)
