import re
import unicodedata


def normalize_name(value: str) -> str:
    clean = unicodedata.normalize("NFKD", value or "")
    clean = "".join(ch for ch in clean if not unicodedata.combining(ch))
    clean = re.sub(r"[^a-zA-Z0-9\s]", " ", clean).lower()
    return re.sub(r"\s+", " ", clean).strip()


def title_from_input(value: str, fallback: str = "Untitled Episode") -> str:
    words = re.findall(r"[A-Za-z0-9']+", value or "")
    if not words:
        return fallback
    return " ".join(words[:8]).title()


def split_sentences(value: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", (value or "").strip())
    return [p.strip() for p in parts if p.strip()]
