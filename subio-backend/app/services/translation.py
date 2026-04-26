import logging
import re
from dataclasses import dataclass
from typing import Optional, Protocol

from app.services.srt import validate_srt
from app.settings import settings

logger = logging.getLogger("subio.translation")

TARGET_LANGUAGE_LABELS = {
    "en": "English",
    "de": "German",
    "tr": "Turkish",
    "uk": "Ukrainian",
}


class TranslationError(Exception):
    pass


@dataclass
class Cue:
    index: int
    timestamp: str
    text: str


def parse_srt(text: str) -> list[Cue]:
    if not text or not text.strip():
        return []
    blocks = [b for b in text.replace("\r\n", "\n").split("\n\n") if b.strip()]
    cues: list[Cue] = []
    for blk in blocks:
        lines = blk.split("\n")
        if len(lines) < 3:
            raise TranslationError(f"Malformed SRT block: {blk[:60]!r}")
        try:
            idx = int(lines[0].strip())
        except ValueError as exc:
            raise TranslationError(f"Bad cue index: {lines[0]!r}") from exc
        ts = lines[1].strip()
        body = "\n".join(lines[2:]).strip()
        cues.append(Cue(index=idx, timestamp=ts, text=body))
    return cues


def rebuild_srt(cues: list[Cue]) -> str:
    parts: list[str] = []
    for c in cues:
        parts.append(str(c.index))
        parts.append(c.timestamp)
        parts.append(c.text if c.text.strip() else "...")
        parts.append("")
    return "\n".join(parts) + ("\n" if parts else "")


class Translator(Protocol):
    def translate_srt(
        self,
        srt_text: str,
        target_language: str,
        repair_reason: Optional[str] = None,
    ) -> str:
        """Return the full translated SRT body as a string."""
        ...

    def translate_text(self, text: str, target_language: str) -> str:
        """Translate a short single-cue text. Used only for per-cue repair."""
        ...


def _system_prompt_full_srt(target_language: str, repair_reason: Optional[str] = None) -> str:
    label = TARGET_LANGUAGE_LABELS.get(target_language, target_language)
    base = (
        "You are translating an SRT subtitle file. "
        "Return only a valid SRT file. "
        "Preserve every cue number exactly. "
        "Preserve every timestamp line exactly. "
        "Preserve the number of cues exactly. "
        "Preserve the blank line separation between cues. "
        "Preserve the SRT block order exactly. "
        "Do not add comments, explanations, markdown, or code fences. "
        f"Translate only the subtitle text into {label}."
    )
    if repair_reason:
        base += (
            "\n\nYour previous response was rejected: "
            f"{repair_reason}. "
            "Reply again with a strict, valid SRT only — same cue numbers, "
            "same timestamps, same number of cues, no markdown, no commentary. "
            "Do NOT drop or merge any cues."
        )
    return base


def _system_prompt_single_text(target_language: str) -> str:
    label = TARGET_LANGUAGE_LABELS.get(target_language, target_language)
    return (
        f"Translate the following subtitle text into {label}. "
        "Reply with only the translated text. "
        "Do not add quotes, commentary, markdown, code fences, or numbering."
    )


class OpenAITranslator:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_TRANSLATION_MODEL
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise TranslationError("OPENAI_API_KEY is not configured")
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise TranslationError("openai package not installed") from exc
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def translate_srt(
        self,
        srt_text: str,
        target_language: str,
        repair_reason: Optional[str] = None,
    ) -> str:
        client = self._get_client()
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _system_prompt_full_srt(target_language, repair_reason)},
                    {"role": "user", "content": srt_text},
                ],
                temperature=0.2,
            )
        except Exception as exc:
            raise TranslationError(f"OpenAI request failed: {exc}") from exc
        return resp.choices[0].message.content or ""

    def translate_text(self, text: str, target_language: str) -> str:
        client = self._get_client()
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _system_prompt_single_text(target_language)},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
            )
        except Exception as exc:
            raise TranslationError(f"OpenAI single-cue request failed: {exc}") from exc
        return (resp.choices[0].message.content or "").strip()


_translator: Optional[Translator] = None


def get_translator() -> Translator:
    global _translator
    if _translator is None:
        _translator = OpenAITranslator()
    return _translator


def set_translator(t: Optional[Translator]) -> None:
    global _translator
    _translator = t


_FENCE_HEAD_RE = re.compile(r"^```[A-Za-z0-9_+-]*\s*\n?")
_FENCE_TAIL_RE = re.compile(r"\n?```\s*$")
_TS_LINE_RE = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$")


def _strip_markdown_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = _FENCE_HEAD_RE.sub("", s)
        s = _FENCE_TAIL_RE.sub("", s)
    s = s.strip()
    if not s.endswith("\n"):
        s += "\n"
    return s


def _check_structural(original: list[Cue], translated_text: str) -> Optional[str]:
    """Return an error string for STRUCTURAL problems only.

    Structural problems require a full-SRT retry: unparseable input, bad timestamp
    line format, spurious cue indices not in original, cue order corruption, or
    timestamp drift on a cue index that IS present.

    Missing cue indices (or cues with empty bodies) alone are NOT structural — those
    are repaired per-cue. Note: we deliberately don't call `validate_srt` here
    because it requires consecutive numbering 1..N, which a model response with
    dropped cues will fail.
    """
    if not translated_text or not translated_text.strip():
        return "translated SRT is empty"
    try:
        translated = parse_srt(translated_text)
    except TranslationError as exc:
        return f"could not parse translated SRT: {exc}"
    if not translated:
        return "translated SRT contains no cues"

    orig_pos = {c.index: i for i, c in enumerate(original)}
    orig_by_idx = {c.index: c for c in original}

    for c in translated:
        if not _TS_LINE_RE.match(c.timestamp):
            return f"bad timestamp line at cue #{c.index}: {c.timestamp!r}"

    extras = [c.index for c in translated if c.index not in orig_pos]
    if extras:
        return f"unknown cue indices in translated SRT: {extras[:5]}"

    last_pos = -1
    for c in translated:
        pos = orig_pos[c.index]
        if pos <= last_pos:
            return f"cue order corrupted at index {c.index}"
        last_pos = pos

    for c in translated:
        if c.timestamp != orig_by_idx[c.index].timestamp:
            return (
                f"timestamp mismatch at cue #{c.index}: "
                f"original={orig_by_idx[c.index].timestamp!r}, "
                f"translated={c.timestamp!r}"
            )

    return None


def translate_outputs(srt_text: str, target_language: str) -> tuple[str, str]:
    """Returns (translated_srt, translated_txt). Sends the full SRT to the model in one call;
    repairs missing cues per-cue if the model dropped any. Falls back to original text only
    when per-cue repair also fails. Retries the full-SRT call once on structural corruption.
    """
    if target_language not in TARGET_LANGUAGE_LABELS:
        raise TranslationError(f"unsupported target language: {target_language}")

    original_cues = parse_srt(srt_text)
    if not original_cues:
        raise TranslationError("no cues to translate")

    translator = get_translator()

    logger.info("Starting full-SRT translation request: %d cues, target=%s", len(original_cues), target_language)
    raw = translator.translate_srt(srt_text, target_language)
    translated_text = _strip_markdown_fences(raw)
    structural_err = _check_structural(original_cues, translated_text)
    if structural_err:
        logger.warning("Full-SRT structural problem, retrying once: %s", structural_err)
        raw = translator.translate_srt(srt_text, target_language, repair_reason=structural_err)
        translated_text = _strip_markdown_fences(raw)
        structural_err2 = _check_structural(original_cues, translated_text)
        if structural_err2:
            raise TranslationError(f"translation failed validation: {structural_err2}")

    translated_cues_by_idx = {c.index: c for c in parse_srt(translated_text)}
    original_by_idx = {c.index: c for c in original_cues}

    missing = [
        c.index
        for c in original_cues
        if c.index not in translated_cues_by_idx
        or not translated_cues_by_idx[c.index].text.strip()
    ]
    repaired_text: dict[int, str] = {}
    fallback_indices: list[int] = []

    if missing:
        logger.warning("Full-SRT validation found missing cues: %s", missing)
        logger.info("Repairing missing cue translations: %s", missing)
        translate_text_fn = getattr(translator, "translate_text", None)
        for idx in missing:
            orig = original_by_idx[idx]
            tr_text: Optional[str] = None
            if translate_text_fn is not None:
                try:
                    tr_text = translate_text_fn(orig.text, target_language)
                    if not tr_text or not tr_text.strip():
                        tr_text = None
                except Exception as exc:
                    logger.warning("Per-cue repair failed for cue #%s: %s", idx, exc)
                    tr_text = None
            if tr_text is None:
                repaired_text[idx] = orig.text
                fallback_indices.append(idx)
            else:
                repaired_text[idx] = tr_text.strip()
        if fallback_indices:
            logger.warning("Fallback used for untranslated cues: %s", fallback_indices)

    final_cues: list[Cue] = []
    for orig in original_cues:
        tr = translated_cues_by_idx.get(orig.index)
        if tr is not None and tr.text.strip():
            body = tr.text
        else:
            body = repaired_text[orig.index]
        final_cues.append(Cue(index=orig.index, timestamp=orig.timestamp, text=body))

    final_srt = rebuild_srt(final_cues)
    validate_srt(final_srt)

    translated_txt = (
        "\n".join(c.text for c in final_cues if c.text.strip()) + "\n"
    )
    logger.info("Full-SRT translation completed")
    return final_srt, translated_txt
