from typing import Dict, Any, List


def process(state: Dict[str, Any]) -> Dict[str, Any]:
    products = state.get("products", [])
    prefs = state.get("extracted_preferences", {})
    budget = prefs.get("budget_num")
    budget = int(budget) if budget is not None and budget < 99999999 else None

    flags: List[str] = []
    severity = "low"
    recommendations_affected: List[str] = []

    if budget is not None:
        over = [
            p["name"]
            for p in products
            if float(p.get("price_pkr") or 0) > budget * 1.1
        ]
        if over:
            flags.append(f"These products exceed your budget: {', '.join(over[:5])}")
            severity = "high"
            recommendations_affected.extend(over[:5])

    if len(products) < 3:
        flags.append("Limited products found for this query")
        if severity == "low":
            severity = "medium"

    brands = [p.get("brand") or "" for p in products[:5]]
    if len(brands) > 2 and len(set(brands)) == 1 and brands[0]:
        flags.append(f"All results are from one brand: {brands[0]}")

    has_flag = len(flags) > 0

    state["ethics"] = {
        "has_flag": has_flag,
        "flags": flags,
        "severity": severity if has_flag else "",
        "recommendations_affected": list(dict.fromkeys(recommendations_affected)),
        "note": (
            "Results checked for budget compliance and diversity."
            if has_flag
            else "All clear."
        ),
    }
    return state
