"""
Word/phrase boundary matching so category keys do not match inside unrelated words
(e.g. 'phone' inside 'headphones', 'ear' inside 'search').
"""

from __future__ import annotations

import re


def phrase_or_word_in_query(needle: str, query_lower: str) -> bool:
    needle = (needle or "").strip().lower()
    q = query_lower.lower()
    if not needle:
        return False
    if " " in needle or "-" in needle:
        parts = re.split(r"[\s\-]+", needle)
        parts = [p for p in parts if p]
        if not parts:
            return False
        sep = r"[\s\-]+"
        inner = sep.join(re.escape(p) for p in parts)
        pat = rf"(?<![a-z0-9]){inner}(?![a-z0-9])"
        return re.search(pat, q, flags=re.IGNORECASE) is not None
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", q, flags=re.IGNORECASE) is not None
