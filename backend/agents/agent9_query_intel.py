from typing import Dict, Any, List


def process(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state.get("query", "")
    pref = state.get("extracted_preferences", {})
    q = query.lower()

    missing: List[str] = []
    if not pref.get("budget_num") or int(pref.get("budget_num") or 0) >= 99999999:
        missing.append("budget not specified")
    if not pref.get("use_case") or pref.get("use_case") == "general":
        missing.append("use case unclear")

    category = pref.get("category", "") or ""

    related_map = {
        "smartphone": [
            "Best camera phone under 80000",
            "Smartphone with 5000mAh battery",
            "iPhone alternative under 100000",
            "Budget Android phone",
            "5G smartphone Pakistan",
        ],
        "laptop": [
            "Gaming laptop under 150000",
            "Lightweight laptop for students",
            "MacBook alternative",
            "Laptop for programming",
            "Best battery life laptop",
        ],
        "heels": [
            "Block heels for wedding",
            "Comfortable daily wear heels",
            "Heels under 5000 PKR",
            "Party heels Pakistan",
            "Flat sandals alternative",
        ],
        "shoes": [
            "Running shoes under 10000",
            "Casual sneakers Pakistan",
            "Formal shoes for office",
            "Lightweight gym shoes",
            "Waterproof shoes",
        ],
        "earbuds": [
            "Noise cancelling earbuds",
            "Earbuds under 5000",
            "Wireless earbuds for gym",
            "Best bass earbuds",
            "Long battery earbuds",
        ],
    }

    related = related_map.get(
        (category or "").lower(),
        [
            f"Best {category} under 50000",
            f"Top rated {category}",
            f"Budget {category} Pakistan",
            f"{category} buying guide",
            f"Best {category} 2026",
        ],
    )

    confidence = 90
    if not category or category == "unknown":
        confidence -= 30
    if not pref.get("budget_num") or int(pref.get("budget_num") or 0) >= 99999999:
        confidence -= 15
    if len(missing) > 1:
        confidence -= 10

    bn = pref.get("budget_num")
    budget_part = ""
    if bn is not None and int(bn) < 99999999:
        budget_part = f" under ₨{int(bn):,}"

    suggested: List[str] = []
    if "budget not specified" in missing:
        suggested.append("What is your budget?")
    if "use case unclear" in missing:
        suggested.append("What will you use it for?")

    state["query_intelligence"] = {
        "is_ambiguous": len(missing) > 1,
        "missing_info": missing,
        "suggested_clarifications": suggested,
        "query_confidence": max(40, confidence),
        "interpreted_as": f"Looking for {category or 'products'}{budget_part} for {pref.get('use_case', 'general')} use",
        "related_searches": related[:5],
    }
    return state
