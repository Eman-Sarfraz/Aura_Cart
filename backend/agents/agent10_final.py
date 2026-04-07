from typing import Dict, Any, List

from langchain_core.prompts import PromptTemplate

from .llm_helper import invoke_llm_text, _api_key_ok


def process(state: Dict[str, Any]) -> Dict[str, Any]:
    products = state.get("products", [])
    query = state.get("query", "")
    pref = state.get("extracted_preferences", {})

    if not products:
        state["final_report"] = {
            "executive_summary": "No products found matching your query. Try a different search.",
            "decision_framework": [
                "Broaden category or budget.",
                "Try a related search from suggestions.",
            ],
            "confidence_level": state.get("query_intelligence", {}).get(
                "query_confidence", 40
            ),
            "disclaimer": "Prices and availability may change. Verify on retailer sites.",
        }
        return state

    top3 = products[:3]
    top_details = [f"{p['name']} at ₨{int(p['price_pkr']):,}" for p in top3]

    executive_summary = (
        f"Based on '{query}', the top picks are {', '.join(top_details[:2])}. "
        f"They balance score, reviews, and fit for a {pref.get('use_case', 'general')} user."
    )

    if _api_key_ok():
        prompt = PromptTemplate.from_template(
            """You are a shopping assistant. User query: '{query}'
Top products: {top_products}
Write exactly 2 short sentences summarizing why these are good picks. Plain text only."""
        )
        try:
            executive_summary = invoke_llm_text(
                prompt,
                {"query": query, "top_products": "; ".join(top_details)},
                timeout_sec=8.0,
                max_tokens=400,
            )
        except Exception as e:
            print(f"Agent 10 LLM summary skipped: {e}")

    for i, p in enumerate(top3):
        feat = ""
        specs = p.get("specs", [])
        if isinstance(specs, list) and specs:
            feat = str(specs[0])
        elif specs:
            feat = str(specs)
        else:
            feat = "solid specs and reviews"
        reason = (p.get("personalization_note") or "it fits your query well.").strip()
        if not reason.endswith("."):
            reason += "."
        p["justification"] = (
            f'Since you searched for "{query}", the {p["name"]} at ₨{int(p["price_pkr"]):,} '
            f"is your #{i + 1} match. Key angle: {feat}. {reason}"
        )

    state["final_report"] = {
        "executive_summary": executive_summary,
        "decision_framework": [
            "Scored on budget fit, spec match, and ratings.",
            "Personalized for your stated use case.",
            "Ethics and price timing reviewed.",
        ],
        "confidence_level": state.get("query_intelligence", {}).get(
            "query_confidence", 85
        ),
        "disclaimer": "Prices and availability are subject to change. Always verify on the retailer site.",
    }

    state["products"] = products
    return state
