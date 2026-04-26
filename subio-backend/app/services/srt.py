import re

SAFETY_GAP_SECONDS = 0.04
LAST_CUE_EXTRA_DURATION_SECONDS = 1.0


def _format_ts(t: float) -> str:
    if t < 0:
        t = 0.0
    total_ms = int(round(t * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def _wrap_words(words: list[str], max_words: int, max_chars: int) -> list[list[str]]:
    lines: list[list[str]] = []
    current: list[str] = []
    current_len = 0
    for w in words:
        if not w:
            continue
        if current:
            new_len = current_len + 1 + len(w)
            if len(current) >= max_words or new_len > max_chars:
                lines.append(current)
                current = [w]
                current_len = len(w)
            else:
                current.append(w)
                current_len = new_len
        else:
            current.append(w)
            current_len = len(w)
    if current:
        lines.append(current)
    return lines


def build_srt(segments: list[dict], preset: dict) -> str:
    max_words = int(preset["max_words_per_line"])
    max_chars = int(preset["max_chars_per_line"])
    max_lines = int(preset["max_lines_per_block"])
    max_words_cue = int(preset.get("max_words_per_cue", max_words * max_lines))
    min_dur = float(preset["min_duration"])
    max_dur = float(preset["max_duration"])

    cues: list[tuple[float, float, list[str]]] = []

    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        if end < start:
            end = start

        words = text.split()
        if not words:
            continue

        word_lines = _wrap_words(words, max_words, max_chars)
        if not word_lines:
            continue

        chunks = _chunk_lines(word_lines, max_lines, max_words_cue)
        total_words = sum(sum(len(wl) for wl in chunk) for chunk in chunks)
        seg_duration = max(0.0, end - start)
        cursor = start
        for ci, chunk in enumerate(chunks):
            if ci == len(chunks) - 1:
                chunk_end = end
            elif total_words > 0:
                chunk_words = sum(len(wl) for wl in chunk)
                chunk_end = cursor + seg_duration * (chunk_words / total_words)
            else:
                chunk_end = end
            cues.append((cursor, chunk_end, [" ".join(wl) for wl in chunk]))
            cursor = chunk_end

    cues = _merge_one_word_cues(cues, max_words, max_chars, max_lines, max_words_cue)
    cues = _merge_short_cues(cues, max_words, max_chars, max_lines, max_words_cue, min_dur)
    cues = _extend_or_clamp(cues, min_dur, max_dur)
    cues = _fill_gaps(cues, SAFETY_GAP_SECONDS, LAST_CUE_EXTRA_DURATION_SECONDS)

    if not cues:
        return ""

    parts: list[str] = []
    for idx, (s, e, lines) in enumerate(cues, start=1):
        parts.append(str(idx))
        parts.append(f"{_format_ts(s)} --> {_format_ts(e)}")
        parts.extend(lines)
        parts.append("")
    return "\n".join(parts) + "\n"


def _chunk_lines(
    word_lines: list[list[str]],
    max_lines: int,
    max_words_cue: int,
) -> list[list[list[str]]]:
    chunks: list[list[list[str]]] = []
    cur: list[list[str]] = []
    cur_words = 0
    for wl in word_lines:
        line_words = len(wl)
        if cur and (
            len(cur) + 1 > max_lines
            or (max_words_cue > 0 and cur_words + line_words > max_words_cue)
        ):
            chunks.append(cur)
            cur = [wl]
            cur_words = line_words
        else:
            cur.append(wl)
            cur_words += line_words
    if cur:
        chunks.append(cur)
    return chunks


def _try_merge_lines(
    a_lines: list[str],
    b_lines: list[str],
    max_words: int,
    max_chars: int,
    max_lines: int,
    max_words_cue: int,
) -> list[str] | None:
    combined_text = " ".join(a_lines + b_lines).strip()
    words = combined_text.split()
    if not words:
        return None
    if max_words_cue > 0 and len(words) > max_words_cue:
        return None
    wrapped = _wrap_words(words, max_words, max_chars)
    if len(wrapped) > max_lines:
        return None
    return [" ".join(wl) for wl in wrapped]


def _merge_one_word_cues(
    cues: list[tuple[float, float, list[str]]],
    max_words: int,
    max_chars: int,
    max_lines: int,
    max_words_cue: int,
) -> list[tuple[float, float, list[str]]]:
    if not cues:
        return cues
    out: list[tuple[float, float, list[str]]] = []
    i = 0
    while i < len(cues):
        s, e, lines = cues[i]
        text = " ".join(lines).strip()
        if len(text.split()) == 1:
            if out:
                ps, pe, plines = out[-1]
                merged = _try_merge_lines(plines, lines, max_words, max_chars, max_lines, max_words_cue)
                if merged is not None:
                    out[-1] = (ps, e, merged)
                    i += 1
                    continue
            if i + 1 < len(cues):
                ns, ne, nlines = cues[i + 1]
                merged = _try_merge_lines(lines, nlines, max_words, max_chars, max_lines, max_words_cue)
                if merged is not None:
                    out.append((s, ne, merged))
                    i += 2
                    continue
        out.append((s, e, lines))
        i += 1
    return out


def _merge_short_cues(
    cues: list[tuple[float, float, list[str]]],
    max_words: int,
    max_chars: int,
    max_lines: int,
    max_words_cue: int,
    min_dur: float,
) -> list[tuple[float, float, list[str]]]:
    if not cues:
        return cues
    out: list[tuple[float, float, list[str]]] = []
    i = 0
    while i < len(cues):
        s, e, lines = cues[i]
        if (e - s) < min_dur and i + 1 < len(cues):
            ns, ne, nlines = cues[i + 1]
            merged = _try_merge_lines(lines, nlines, max_words, max_chars, max_lines, max_words_cue)
            if merged is not None:
                out.append((s, ne, merged))
                i += 2
                continue
        out.append((s, e, lines))
        i += 1
    return out


def _extend_or_clamp(
    cues: list[tuple[float, float, list[str]]],
    min_dur: float,
    max_dur: float,
) -> list[tuple[float, float, list[str]]]:
    if not cues:
        return cues
    result: list[tuple[float, float, list[str]]] = []
    for i, (s, e, lines) in enumerate(cues):
        if e < s:
            e = s
        dur = e - s
        if dur < min_dur:
            next_start = cues[i + 1][0] if i + 1 < len(cues) else None
            target = s + min_dur
            if next_start is not None and target > next_start:
                e = max(e, next_start)
            else:
                e = target
        if (e - s) > max_dur:
            e = s + max_dur
        if result and s < result[-1][1]:
            s = result[-1][1]
            if e < s:
                e = s
        result.append((s, e, lines))
    return result


def _fill_gaps(
    cues: list[tuple[float, float, list[str]]],
    safety_gap: float,
    last_cue_extra: float,
) -> list[tuple[float, float, list[str]]]:
    if not cues:
        return cues
    out: list[tuple[float, float, list[str]]] = []
    n = len(cues)
    for i, (s, e, lines) in enumerate(cues):
        if i < n - 1:
            next_start = cues[i + 1][0]
            target_end = next_start - safety_gap
            if target_end < s:
                target_end = s
            if e < target_end:
                e = target_end
            if e > next_start - safety_gap:
                e = max(s, next_start - safety_gap)
        else:
            if last_cue_extra > 0:
                e = max(e, s) + last_cue_extra
        if e < s:
            e = s
        out.append((s, e, lines))
    return out


_TS_RE = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$")


def validate_srt(text: str) -> None:
    if not text.strip():
        raise ValueError("SRT is empty")
    text.encode("utf-8")
    blocks = [b for b in text.replace("\r\n", "\n").split("\n\n") if b.strip()]
    expected = 1
    for blk in blocks:
        lines = blk.split("\n")
        if len(lines) < 3:
            raise ValueError(f"SRT cue {expected}: missing lines")
        try:
            num = int(lines[0].strip())
        except ValueError as exc:
            raise ValueError(f"SRT cue {expected}: bad index") from exc
        if num != expected:
            raise ValueError(f"SRT cue index {num} out of order (expected {expected})")
        if not _TS_RE.match(lines[1].strip()):
            raise ValueError(f"SRT cue {expected}: bad timestamps")
        body = "\n".join(lines[2:]).strip()
        if not body:
            raise ValueError(f"SRT cue {expected}: empty body")
        expected += 1
