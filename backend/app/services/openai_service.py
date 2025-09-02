import os
from typing import Dict, List, Optional


def _get_openai_client():
    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:
        raise RuntimeError("openai package not installed. Add 'openai' to requirements.") from exc
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


SYSTEM_PROMPT = (
    "You are an assistant that rewrites multiple-choice quiz questions to be clear and concise, "
    "keeping the original meaning. Provide the correct option letter and a short reason explaining "
    "why it is correct and why others are not."
)


def _build_user_prompt(item: Dict) -> str:
    lines = [
        "Rewrite the question but keep the meaning. Identify the correct answer.",
        "Return JSON with fields: question, correct_label, correct_text, reason.",
        "Original question and options:",
        f"Question: {item.get('question','').strip()}",
    ]
    options = item.get("options", {})
    for label in ["A", "B", "C", "D"]:
        if label in options:
            lines.append(f"{label}. {options[label]}")
    if item.get("correct_label"):
        lines.append(f"Hint correct label: {item.get('correct_label')}")
    return "\n".join(lines)


def rewrite_questions_with_reasoning(items: List[Dict], model_override: Optional[str] = None) -> List[Dict]:
    client = _get_openai_client()
    model = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    outputs: List[Dict] = []
    for item in items:
        user_prompt = _build_user_prompt(item)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or "{}"
        # Be defensive if model does not return valid JSON
        import json
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {
                "question": item.get("question", ""),
                "correct_label": item.get("correct_label", ""),
                "correct_text": item.get("correct_text", ""),
                "reason": content.strip(),
            }

        # Build final formatted display fields
        q_text = parsed.get("question", "").strip() or item.get("question", "")
        label = (parsed.get("correct_label") or item.get("correct_label") or "").upper()
        opt_text = parsed.get("correct_text") or item.get("options", {}).get(label, "")
        reason = parsed.get("reason", "").strip()

        outputs.append({
            "question": q_text,
            "options": item.get("options", {}),
            "correct_label": label,
            "correct_text": opt_text,
            "reason": reason,
            "display": {
                "question": f"Question: {q_text}",
                "answer": f"✅ Correct Answer: {label}. {opt_text}" if label else "",
                "reason": f"Reason: {reason}" if reason else "",
            },
        })

    return outputs


