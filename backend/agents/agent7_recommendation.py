from typing import Dict, Any, List


def _specs_text(p: Dict[str, Any]) -> str:
    s = p.get("specs", [])
    if isinstance(s, list):
        return " ".join(str(x) for x in s).lower()
    return str(s or "").lower()


def _use_case_tokens(p: Dict[str, Any]) -> str:
    u = p.get("use_cases", [])
    if isinstance(u, list):
        return " ".join(str(x).lower() for x in u)
    return str(u or "").lower()


def process(state: Dict[str, Any]) -> Dict[str, Any]:
    products = list(state.get("products", []))
    prefs = state.get("extracted_preferences", {})
    use_case = prefs.get("use_case", "general")

    profiles = {
        "student": {
            "note": "Great for students — good value for money",
            "boost_words": ["battery", "lightweight", "affordable"],
        },
        "gamer": {
            "note": "Strong performance for gaming",
            "boost_words": ["performance", "cooling", "fast", "gaming", "rtx", "144hz"],
        },
        "office": {
            "note": "Reliable choice for professional use",
            "boost_words": ["reliable", "keyboard", "display", "lightweight"],
        },
        "traveler": {
            "note": "Compact and portable — ideal for travel",
            "boost_words": ["lightweight", "battery", "compact", "portable"],
        },
        "general": {"note": "Well-rounded choice for everyday use", "boost_words": []},
    }

    profile = profiles.get(use_case, profiles["general"])
    for p in products:
        specs_text = _specs_text(p)
        uc = _use_case_tokens(p)
        boost = sum(1 for w in profile["boost_words"] if w in specs_text)
        if use_case != "general" and use_case in uc:
            boost += 2
        sc = p.get("scores") or {}
        total = int(sc.get("total_score", 0)) + (boost * 3)
        total = min(100, total)
        sc["total_score"] = total
        p["scores"] = sc
        p["personalization_note"] = profile["note"]

    products.sort(
        key=lambda x: x.get("scores", {}).get("total_score", 0), reverse=True
    )
    state["products"] = products
    state["user_profile"] = {
        "user_profile_summary": f"Profile: {str(use_case).title()} user — {profile['note']}"
    }
    return state
