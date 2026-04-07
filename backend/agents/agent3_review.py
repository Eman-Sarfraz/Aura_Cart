from typing import Dict, Any, List


def _reviews_list(p: Dict[str, Any]) -> List[str]:
    r = p.get("reviews", [])
    if isinstance(r, list):
        return [str(x) for x in r if x]
    if isinstance(r, str):
        return [r] if r else []
    return []


def process(state: Dict[str, Any]) -> Dict[str, Any]:
    analyzed: List[Dict[str, Any]] = []
    for p in state.get("products", []):
        rating = float(p.get("rating") or 4.0)
        if rating >= 4.5:
            sentiment = "Highly Positive"
        elif rating >= 3.5:
            sentiment = "Mixed"
        else:
            sentiment = "Negative"

        reviews = _reviews_list(p)
        p["sentiment_analysis"] = {
            "sentiment_label": sentiment,
            "review_summary": reviews[0] if reviews else "Good product overall.",
            "confidence_score": min(100, int(rating * 20)),
            "top_praise": reviews[0] if len(reviews) > 0 else "Good quality",
            "top_complaint": reviews[2] if len(reviews) > 2 else "None reported",
        }
        analyzed.append(p)

    state["products"] = analyzed
    return state
