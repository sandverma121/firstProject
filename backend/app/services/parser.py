import re
from typing import Dict, List


QUESTION_PATTERN = re.compile(
    r"(?P<number>\d+)\s*[\).:-]?\s*(?P<question>.+?)(?=(?:\n\s*[A-D][\).:-])|\Z)",
    re.IGNORECASE | re.DOTALL,
)

OPTION_PATTERN = re.compile(
    r"^(?P<label>[A-D])[\).:-]\s*(?P<text>.+)$",
    re.IGNORECASE,
)

CORRECT_MARKERS = [
    r"\*\s*Correct\s*Answer\s*:\s*([A-D])",
    r"Answer\s*:\s*([A-D])",
    r"Correct\s*:\s*([A-D])",
    r"\(([A-D])\)\s*is\s*correct",
]
CORRECT_REGEXES = [re.compile(pat, re.IGNORECASE) for pat in CORRECT_MARKERS]


def _find_correct_label(block: str) -> str:
    for rx in CORRECT_REGEXES:
        m = rx.search(block)
        if m:
            return m.group(1).upper()
    # fallback: option ending with an asterisk or marked with [Correct]
    lines = [l.strip() for l in block.splitlines()]
    for line in lines:
        if line.endswith("*") or "[correct]" in line.lower():
            m = OPTION_PATTERN.match(line.rstrip("* "))
            if m:
                return m.group("label").upper()
    return ""


def parse_questions_from_text(text: str) -> List[Dict]:
    """
    Parse questions with options A-D from raw text.
    Attempts to find a clearly marked correct answer.
    Returns a list of dicts:
    { question, options: {A,B,C,D}, correct_label, correct_text }
    """
    blocks = []
    # Split by blank lines or question numbers to reduce noise
    candidates = re.split(r"\n\s*\n+", text)
    for candidate in candidates:
        if re.search(r"\b[A-D][\).:-]", candidate):
            blocks.append(candidate.strip())

    results: List[Dict] = []
    for block in blocks:
        # Extract question text up to first option
        lines = [l for l in block.splitlines() if l.strip()]
        question_lines = []
        option_lines = []
        hit_option = False
        for line in lines:
            if OPTION_PATTERN.match(line.strip()):
                hit_option = True
                option_lines.append(line.strip())
            elif not hit_option:
                question_lines.append(line.strip())
            else:
                # continuation lines for the last option
                if option_lines:
                    option_lines[-1] += f" {line.strip()}"

        if not option_lines:
            # try alternative: scan entire block for option lines
            option_lines = [l.strip() for l in lines if OPTION_PATTERN.match(l.strip())]

        options: Dict[str, str] = {}
        for opt_line in option_lines:
            m = OPTION_PATTERN.match(opt_line)
            if not m:
                continue
            label = m.group("label").upper()
            text_val = m.group("text").strip()
            options[label] = text_val

        if len(options) < 2:
            continue

        question_text = " ".join(question_lines).strip()
        correct_label = _find_correct_label(block)
        correct_text = options.get(correct_label, "") if correct_label else ""

        results.append({
            "question": question_text,
            "options": options,
            "correct_label": correct_label,
            "correct_text": correct_text,
        })

    return results


