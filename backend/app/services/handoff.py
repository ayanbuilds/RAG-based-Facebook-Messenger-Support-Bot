import re

HUMAN_PATTERNS = [
    r"\bhuman\b",
    r"\bagent\b",
    r"\brepresentative\b",
    r"\bcustomer support\b",
    r"\bperson\b",
    r"\btalk to\b",
    r"\bcall me\b",
]

_rx = re.compile("|".join(HUMAN_PATTERNS), re.IGNORECASE)

def wants_human(text: str) -> bool:
    return bool(_rx.search(text or ""))
