from typing import Dict, Any, List


def process(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state.get("extracted_preferences", {})
    budget = prefs.get("budget_num")
    budget = int(budget) if budget is not None and budget < 99999999 else None
    products = state.get("products", [])
    category = prefs.get("category", "") or ""

    alt = {
        "budget_stretch_option": None,
        "category_alternative": None,
        "refurbished_note": "Consider certified refurbished options to save 20-30% on premium products.",
        "wait_recommendation": False,
    }

    if budget is not None:
        over_budget: List[Dict[str, Any]] = [
            p
            for p in products
            if float(p.get("price_pkr") or 0) > budget
            and float(p.get("price_pkr") or 0) <= budget * 1.3
        ]
        if over_budget:
            best = max(
                over_budget,
                key=lambda x: x.get("scores", {}).get("total_score", 0),
            )
            diff = int(float(best["price_pkr"]) - budget)
            alt["budget_stretch_option"] = {
                "product": best["name"],
                "price_diff": diff,
                "justification": f"{best['name']} is ₨{diff:,} over budget but scores significantly higher",
            }

    category_alts = {
        "laptop": "Consider a tablet with keyboard for lighter workloads at lower cost",
        "smartphone": "Consider last year's flagship model for 30-40% savings",
        "camera": "Consider a smartphone with pro camera mode as a budget alternative",
        "headphones": "Consider earbuds for a more portable and affordable option",
        "earbuds": "Consider wired earphones for a lower price",
    }
    alt["category_alternative"] = category_alts.get((category or "").lower())

    alt["wait_recommendation"] = (
        state.get("price_intelligence", {}).get("buy_now") is False
    )

    state["alternatives"] = alt
    return state
