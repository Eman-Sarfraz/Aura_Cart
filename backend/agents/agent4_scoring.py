from typing import Dict, Any, List


def _specs_text(p: Dict[str, Any]) -> str:
    s = p.get("specs", [])
    if isinstance(s, list):
        return " ".join(str(x) for x in s).lower()
    return str(s or "").lower()


def process(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state.get("extracted_preferences", {})
    budget = prefs.get("budget_num")
    budget = int(budget) if budget is not None else 99999999
    priorities = prefs.get("priorities") or []

    scored: List[Dict[str, Any]] = []
    for p in state.get("products", []):
        price = float(p.get("price_pkr") or 0)
        rating = float(p.get("rating") or 3.5)
        specs_text = _specs_text(p)

        if budget < 99999999:
            if price <= budget:
                price_fit = 35
            elif price <= budget * 1.1:
                price_fit = 25
            elif price <= budget * 1.2:
                price_fit = 15
            else:
                price_fit = 5
        else:
            price_fit = 35

        feature_match = 0
        for priority in priorities:
            if priority.lower() in specs_text:
                feature_match += 7
        feature_match = min(35, feature_match + 15)

        review_score = int((rating / 5.0) * 30)
        total = price_fit + feature_match + review_score

        ratio = total / (price / 10000) if price > 0 else total
        if ratio > 8:
            value_rating = "Exceptional Value"
        elif ratio > 4:
            value_rating = "Good Value"
        else:
            value_rating = "Overpriced"

        p["scores"] = {
            "price_fit": price_fit,
            "feature_match": feature_match,
            "review_score": review_score,
            "total_score": total,
            "value_rating": value_rating,
        }
        scored.append(p)

    scored.sort(key=lambda x: x.get("scores", {}).get("total_score", 0), reverse=True)
    state["products"] = scored
    return state
