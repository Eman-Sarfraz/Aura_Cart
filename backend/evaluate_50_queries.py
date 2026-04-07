import requests
import json
import time
import csv
import os
import sys
import io
from typing import Any, Dict, List, Optional, Set

# Force UTF-8 for Windows terminals
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_URL = os.environ.get("AURACART_API_URL", "http://127.0.0.1:8000/advise")
TEST_QUERIES_URL = os.environ.get(
    "AURACART_TEST_QUERIES_URL", "http://127.0.0.1:8000/test-queries"
)

# Test group name -> product categories we expect the TOP result to belong to
GROUP_EXPECTED_TOP_CATEGORY: Dict[str, Optional[Set[str]]] = {
    "Smartphones": {"smartphone"},
    "Laptops": {"laptop"},
    "Footwear": {"heels", "shoes"},
    "Audio": {"earbuds", "headphones", "speaker"},
    "Wearables": {"smartwatch"},
    "Cameras": {"camera"},
    "Gaming": {"keyboard", "mouse", "monitor", "gaming headset"},
    "Accessories": {"powerbank", "cooling pad"},
    "Edge Cases": None,
    "Conflicting Preferences": None,
}


def _top_category(data: Dict[str, Any]) -> str:
    products = data.get("products") or []
    if not products:
        return ""
    return str((products[0] or {}).get("category") or "").lower()


def extract_budget(q: str) -> Optional[int]:
    import re
    text = q.lower()
    match = re.search(r"(?:under|below|max|budget(?: is)?|within|less than)\s*(?:₨|rs\.?|pkr)?\s*([\d,]+(?:\s*[km]|lac|lakh)?)", text)
    if match:
        val = match.group(1).replace(",", "").strip()
        try:
            num = float(re.sub(r"[^\d.]", "", val))
            if "k" in val: num *= 1000
            if "lac" in val or "lakh" in val: num *= 100000
            if "m" in val: num *= 1000000
            return int(num)
        except:
            return None
    return None


def _relevant_result(
    group: str, data: Dict[str, Any], detected: str, query: str
) -> bool:
    products = data.get("products") or []
    if not products:
        return False

    # 1. Category relevance
    expected = GROUP_EXPECTED_TOP_CATEGORY.get(group)
    cat_match = True
    if expected:
        top = _top_category(data)
        det = (detected or "").lower().strip()
        cat_match = (top in expected) or (det in expected)

    # 2. Strict Budget relevance
    budget_limit = extract_budget(query)
    budget_match = True
    if budget_limit and products:
        price = products[0].get("price_pkr", 0)
        budget_match = price <= budget_limit

    return cat_match and budget_match


def run_eval() -> None:
    print(f"Fetching test queries from {TEST_QUERIES_URL}...")
    try:
        resp = requests.get(TEST_QUERIES_URL, timeout=30)
        resp.raise_for_status()
        queries_dict = resp.json()
    except Exception as e:
        print(f"Failed to fetch queries! Is backend running? {e}")
        return

    results: List[Dict[str, Any]] = []
    total_queries = sum(len(queries) for queries in queries_dict.values())

    print(f"Starting evaluation of {total_queries} queries...\n")

    relevant_hits = 0

    for category, queries in queries_dict.items():
        print(f"\n>>> GROUP: {category}")
        for q in queries:
            start_time = time.time()
            try:
                r = requests.post(API_URL, json={"query": q}, timeout=120)
                r.raise_for_status()
                data = r.json()

                resp_time = int((time.time() - start_time) * 1000)

                products = data.get("products", [])
                p_count = len(products)
                top_name = products[0]["name"] if p_count > 0 else "None"
                top_cat = _top_category(data)
                
                detected_prefs = data.get("extracted_preferences", {}) or {}
                detected_cat = detected_prefs.get("category", "General")

                rel = _relevant_result(category, data, str(detected_cat), q)
                if rel:
                    relevant_hits += 1

                budget_limit = extract_budget(q)
                price = products[0].get("price_pkr", 0) if p_count > 0 else 0
                is_budget_ok = not budget_limit or price <= budget_limit * 1.05 # 5% tolerance

                res_obj = {
                    "query": q,
                    "test_group": category,
                    "detected_category": detected_cat,
                    "top_product_category": top_cat,
                    "response_time_ms": resp_time,
                    "products_found": p_count,
                    "top_recommendation": top_name,
                    "top_product_price": price,
                    "relevant_top_match": rel,
                    "retrieval_strategy": data.get("retrieval_strategy", ""),
                    "budget_limit": budget_limit or "N/A",
                    "price_match": is_budget_ok,
                }

                time.sleep(2)  # Wait for rate limits
                results.append(res_obj)
                mark = "PASS" if rel else "WARN"
                print(
                    f"  {mark} {resp_time:4}ms | {q[:40]:40} | top: {top_name[:30]:30} | {top_cat}"
                )

            except Exception as e:
                print(f"  FAIL: {q} -> {e}")
                results.append({
                    "query": q,
                    "test_group": category,
                    "detected_category": "ERROR",
                    "response_time_ms": 0,
                    "products_found": 0,
                    "relevant_top_match": False,
                })

    out_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(out_dir, "evaluation_report.md")

    accuracy = (relevant_hits / total_queries * 100) if total_queries else 0.0
    avg_time = sum(r.get("response_time_ms", 0) for r in results) / total_queries if total_queries else 0

    lines = [
        "# AuraCart System Evaluation Report",
        "",
        f"- **Total Queries Tested**: {total_queries}",
        f"- **Relevance / Accuracy Rate**: {accuracy:.1f}%",
        f"- **Average Latency**: {avg_time:.0f}ms",
        f"- **Execution Timestamp**: {time.ctime()}",
        "",
        "## Detailed Results",
        "",
        "| Query | Group | Budget | Price | Top pick | Rel | ms | Strategy |",
        "|---|---|---|---|---|:---:|:---:|---|",
    ]
    for r in results:
        rel_icon = "✅" if r.get("relevant_top_match") else "❌"
        budget = r.get("budget_limit", "N/A")
        price = r.get("top_product_price", "N/A")
        lines.append(
            "| {q} | {g} | {b} | {p} | {tp} | {rel} | {ms} | {st} |".format(
                q=str(r.get("query", "")).replace("|", "\\|"),
                g=str(r.get("test_group", "")),
                b=budget,
                p=price,
                tp=str(r.get("top_recommendation", ""))[:50].replace("|", "\\|"),
                rel=rel_icon,
                ms=r.get("response_time_ms", 0),
                st=str(r.get("retrieval_strategy", ""))[:40].replace("|", "\\|"),
            )
        )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nEvaluation Complete! Report saved to: {md_path}")


if __name__ == "__main__":
    run_eval()
