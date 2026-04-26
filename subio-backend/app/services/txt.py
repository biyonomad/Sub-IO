def build_txt(segments: list[dict], full_text: str = "") -> str:
    lines = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if text:
            lines.append(text)
    if not lines and full_text:
        return full_text.strip() + "\n"
    return "\n".join(lines) + "\n"
