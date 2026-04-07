"""
Append-only feedback log (replaces SQLite feedback table).
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict

_LOCK = threading.Lock()
_BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BACKEND_ROOT, "data")
_FEEDBACK_PATH = os.path.join(_DATA_DIR, "feedback.jsonl")


def _ensure_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def save_feedback(query: str, result_id: int, rating: int, comment: str) -> bool:
    row: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "result_id": int(result_id),
        "rating": int(rating),
        "comment": comment or "",
    }
    line = json.dumps(row, ensure_ascii=False) + "\n"
    with _LOCK:
        _ensure_dir()
        with open(_FEEDBACK_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    return True
