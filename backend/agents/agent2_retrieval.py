from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.prompts import PromptTemplate

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from catalog_api import (
    PKR_PER_USD,
    DUMMYJSON_BASE,
    REQUEST_TIMEOUT_SEC,
    search_products_raw,
    get_json,
)

from .llm_helper import invoke_llm_text, _api_key_ok

# --- External APIs ---
DDG_API = "https://api.duckduckgo.com/"


def _http_get_json(url: str) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AuraCart/2.0 (academic)"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as e:
        print(f"[Agent 2] HTTP JSON failed: {url[:80]}… — {e}")
        return None


def _duckduckgo_abstract(brand: str, category: str) -> str:
    q = f"{(brand or '').strip()} {(category or '').strip()}".strip() or "popular products"
    params = urllib.parse.urlencode({"q": q, "format": "json", "no_html": "1", "skip_disambig": "1"})
    url = f"{DDG_API}?{params}"
    data = _http_get_json(url)
    if not data:
        return ""
    abstract = (data.get("AbstractText") or "").strip()
    if abstract:
        return abstract
    definition = (data.get("Definition") or "").strip()
    if definition:
        return definition
    topics = data.get("RelatedTopics") or []
    if isinstance(topics, list) and topics:
        first = topics[0]
        if isinstance(first, dict) and first.get("Text"):
            return str(first["Text"]).strip()
    return ""


def _unsplash_featured_url(product_name: str) -> str:
    q = urllib.parse.quote((product_name or "product").strip() or "product", safe="")
    return f"https://source.unsplash.com/featured/?{q}"


def _pollinations_placeholder(product_name: str) -> str:
    """Fallback when source.unsplash.com is deprecated / returns errors."""
    q = urllib.parse.quote(f"minimal product photo {product_name}", safe="")
    return f"https://image.pollinations.ai/prompt/{q}"


def _category_fetch_plan(internal_category: str) -> Tuple[Optional[str], str]:
    """
    Returns (dummyjson_category_slug or None, search_query_seed).
    """
    c = (internal_category or "").strip()
    if c in ("General",):
        return (None, "")

    direct: Dict[str, Tuple[Optional[str], str]] = {
        "Smartphone": ("smartphones", "smartphone"),
        "Laptop": ("laptops", "laptop"),
        "Tablet": ("tablets", "tablet"),
        "Fragrance": ("fragrances", "perfume"),
        "Makeup": ("beauty", "makeup"),
        "Skincare": ("skin-care", "skincare"),
        "Bags": ("womens-bags", "bag"),
        "Clothing": ("tops", "shirt"),
        "Heels": ("womens-shoes", "heels women pumps"),
        "Shoes": ("mens-shoes", "shoes sneakers footwear"),
        "Earbuds": ("mobile-accessories", "wireless earbuds bluetooth"),
        "Keyboard": ("mobile-accessories", "mechanical keyboard gaming"),
        "Monitor": ("mobile-accessories", "monitor display screen"),
        "Cooling Pad": ("laptops", "laptop cooling pad fan"),
        "Smartwatch": ("mens-watches", "smart watch digital"),
        "Headphones": ("mobile-accessories", "headphones over ear bluetooth"),
        "Gaming Headset": ("mobile-accessories", "gaming headset mic"),
        "Powerbank": ("mobile-accessories", "power bank portable charger"),
        "Mouse": ("mobile-accessories", "gaming mouse wireless"),
        "Sunglasses": ("sunglasses", "sunglasses uv protection"),
        "Fragrance": ("fragrances", "perfume scent"),
    }
    if c in direct:
        return direct[c]

    search_seeds = {
        "Camera": "camera digital",
        "Mouse": "mouse computer",
        "Speaker": "speaker bluetooth",
    }
    seed = search_seeds.get(c, c.lower())
    return (None, seed)


def _fetch_raw_products(pref: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    category = (pref.get("category") or "").strip()
    keywords = pref.get("keywords") or []
    brand = (pref.get("brand") or "").strip()
    original_query = (pref.get("original_query") or "").strip()
    slug, seed = _category_fetch_plan(category)

    collected: List[Dict[str, Any]] = []
    seen: set = set()

    def add_list(items: List[Dict[str, Any]]) -> None:
        for it in items:
            pid = it.get("id")
            if pid is None or pid in seen:
                continue
            seen.add(pid)
            collected.append(it)

    strategy_parts: List[str] = []

    # When category is unknown, anchor search on the user's exact words first
    if category == "General" and original_query:
        oq_items = search_products_raw(original_query[:120], limit=50)
        add_list(oq_items)
        strategy_parts.append(f"query search: {original_query[:60]!r}")

    if slug:
        data = get_json(f"{DUMMYJSON_BASE}/products/category/{urllib.parse.quote(slug, safe='')}?limit=50")
        if data and isinstance(data.get("products"), list):
            add_list(data["products"])
            strategy_parts.append(f"DummyJSON category/{slug}")

    kw_extra = " ".join(str(k) for k in keywords[:8] if k)
    if not seed and original_query:
        seed = original_query[:100]
    search_q = f"{seed} {brand} {kw_extra}".strip()
    if not search_q:
        search_q = category or "products"
    search_items = search_products_raw(search_q, limit=50)
    add_list(search_items)
    strategy_parts.append(f"DummyJSON search q={search_q[:80]}")

    if brand:
        branded = search_products_raw(brand, limit=30)
        add_list(branded)
        strategy_parts.append(f"brand search {brand}")

    if not collected:
        # RESCUE LOGIC: Try a broader search on the category itself if specific terms failed
        rescue_q = category if category != "General" else original_query
        broad = search_products_raw(rescue_q, limit=50)
        add_list(broad)
        strategy_parts.append(f"emergency rescue/{rescue_q}")

    if not collected:
        data = get_json(f"{DUMMYJSON_BASE}/products?limit=50")
        if data and isinstance(data.get("products"), list):
            add_list(data["products"])
            strategy_parts.append("emergency GET /products")

    strategy = " + ".join(strategy_parts) if strategy_parts else "DummyJSON"
    return collected, strategy


def _usd_to_pkr(usd: float) -> int:
    return int(round(float(usd) * PKR_PER_USD))


def _safe_int(val: Any, default: Optional[int] = None) -> Optional[int]:
    if val is None:
        return default
    try:
        return int(float(str(val).replace(",", "")))
    except (TypeError, ValueError):
        return default


def _rank_by_relevance(raw_list: List[Dict[str, Any]], pref: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Boost products whose titles/descriptions match query tokens and keywords."""
    query = (pref.get("original_query") or "").lower()
    keywords = [str(k).lower() for k in (pref.get("keywords") or []) if k]
    brand = (pref.get("brand") or "").lower()
    stop = {
        "the", "a", "an", "for", "and", "with", "under", "below", "best", "need",
        "want", "give", "show", "me", "i", "my", "is", "to", "of", "in", "or", "no",
        "any", "just", "buy", "get", "looking", "some", "that", "this", "has", "have",
    }
    qtok = [
        t
        for t in re.findall(r"[a-z0-9]+", query)
        if len(t) > 2 and t not in stop
    ]

    def score(p: Dict[str, Any]) -> float:
        blob = f"{p.get('title', '')} {p.get('description', '')} {p.get('category', '')} {p.get('brand', '')}".lower()
        s = 0.0
        for kw in keywords:
            if kw and kw in blob:
                s += 4.0
        for t in qtok:
            if t in blob:
                s += 1.2
        if brand and brand in blob:
            s += 6.0
        s += float(p.get("rating") or 0) * 0.35
        return s

    raw_list.sort(key=score, reverse=True)
    return raw_list


def _heuristic_features(description: str, max_n: int = 5) -> List[str]:
    text = (description or "").replace("\n", " ").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for p in parts:
        p = p.strip()
        if 12 <= len(p) <= 220:
            out.append(p)
        if len(out) >= max_n:
            break
    if not out and text:
        out = [text[:200]]
    return out[:max_n]


def _extract_key_features_llm(
    products: List[Dict[str, Any]], ddg_context: str
) -> Dict[int, List[str]]:
    if not products or not _api_key_ok():
        return {}
    lines = []
    for i, p in enumerate(products[:8], start=1):
        desc = (p.get("description") or "")[:1200]
        lines.append(f'{i}. title={p.get("title")!r} description={desc!r}')
    block = "\n".join(lines)
    prompt = PromptTemplate.from_template(
        """You extract concise shopping bullet points. Given products and optional web context, return ONLY valid JSON:
{{"1":["bullet1","bullet2"], "2":["..."]}}
Use keys 1..N matching the numbered products. 3-5 bullets each, no prices, no markdown, short phrases.
Context: {ctx}
Products:
{block}
JSON only:"""
    )
    try:
        content = invoke_llm_text(
            prompt,
            {"ctx": (ddg_context or "")[:1500], "block": block},
            timeout_sec=14.0,
            max_tokens=800,
        )
        if "```" in content:
            content = content.split("```", 1)[-1].split("```", 1)[0]
        if content.strip().lower().startswith("json"):
            content = content.strip()[4:].lstrip()
        parsed = json.loads(content.strip())
        out: Dict[int, List[str]] = {}
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                try:
                    idx = int(str(k).strip())
                except ValueError:
                    continue
                if isinstance(v, list):
                    out[idx] = [str(x).strip() for x in v if str(x).strip()][:6]
        return out
    except Exception as e:
        print(f"[Agent 2] key_features LLM failed: {e}")
        return {}


def _normalize_product(
    raw: Dict[str, Any],
    display_category: str,
    key_features: List[str],
    ddg_text: str,
    review_snippets: List[str],
) -> Dict[str, Any]:
    title = str(raw.get("title") or "Product")
    thumb = (raw.get("thumbnail") or "").strip()
    images = raw.get("images") if isinstance(raw.get("images"), list) else []
    first_img = str(images[0]) if images else ""

    image_url = thumb or first_img or _unsplash_featured_url(title)
    image_placeholder_alt = _pollinations_placeholder(title)

    desc = str(raw.get("description") or "")
    deep = desc
    if ddg_text:
        deep = f"{ddg_text}\n\n{desc}".strip()

    brand = str(raw.get("brand") or "Unknown")
    rating = float(raw.get("rating") or 4.2)
    price_usd = float(raw.get("price") or 0.0)
    price_pkr = _usd_to_pkr(price_usd)

    q_enc = urllib.parse.quote(f"{brand} {title}")
    daraz = f"https://www.daraz.pk/catalog/?q={q_enc}"
    amazon = f"https://www.amazon.com/s?k={q_enc}"

    specs = key_features if key_features else _heuristic_features(desc)

    return {
        "id": int(raw.get("id") or 0),
        "name": title,
        "brand": brand,
        "category": display_category,
        "dummyjson_category": str(raw.get("category") or ""),
        "price_pkr": price_pkr,
        "price_usd": round(price_usd, 2),
        "rating": rating,
        "specs": specs,
        "key_features": specs,
        "description": desc,
        "deep_description": deep,
        "reviews": review_snippets,
        "search_url_daraz": daraz,
        "search_url_amazon": amazon,
        "image_emoji": "🛍️",
        "image_url": image_url,
        "image_placeholder_alt": image_placeholder_alt,
        "use_cases": [],
        "release_year": 2024,
        "ddg_abstract": ddg_text[:2000] if ddg_text else "",
    }


def _filter_budget(
    products: List[Dict[str, Any]], pref: Dict[str, Any], relax: bool
) -> List[Dict[str, Any]]:
    pmin = _safe_int(pref.get("price_min"))
    pmax = _safe_int(pref.get("price_max"))
    if relax:
        pmin, pmax = None, None
    if pmax is None or pmax >= 99999999:
        pmax = None

    out: List[Dict[str, Any]] = []
    for raw in products:
        usd = float(raw.get("price") or 0.0)
        pkr = _usd_to_pkr(usd)
        if pmax is not None and pkr > pmax:
            continue
        if pmin is not None and pkr < pmin * 0.98:
            continue
        out.append(raw)
    return out


def _rescue_search_seed(category: str, pref: Dict[str, Any]) -> str:
    kws = " ".join(str(k) for k in (pref.get("keywords") or [])[:5])
    oq = (pref.get("original_query") or "").strip()
    rescue: Dict[str, str] = {
        "Keyboard": f"keyboard mechanical {kws}".strip(),
        "Headphones": f"headphones audio {kws}".strip(),
        "Earbuds": f"earbuds wireless {kws}".strip(),
        "Smartwatch": f"smart watch digital {kws}".strip(),
        "Monitor": f"monitor display {kws}".strip(),
        "Mouse": f"mouse computer {kws}".strip(),
        "Camera": f"camera digital {kws}".strip(),
        "Gaming Headset": f"gaming headset {kws}".strip(),
        "Powerbank": f"power bank {kws}".strip(),
        "Cooling Pad": f"laptop cooling pad {kws}".strip(),
    }
    base = rescue.get(category) or f"{category} {kws}".strip()
    if not base.strip():
        base = oq[:100] or "electronics"
    return base[:120]


def _filter_plausible_products(raw_list: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    """
    DummyJSON search/category can return unrelated items (e.g. groceries for 'keyboard').
    Drop obvious mismatches; if nothing remains, return the original list.
    """
    if not raw_list:
        return raw_list

    hint_patterns: Dict[str, List[str]] = {
        "Smartphone": [
            r"phone",
            r"smartphone",
            r"iphone",
            r"galaxy",
            r"pixel",
            r"mobile",
            r"android",
            r"cell",
        ],
        "Laptop": [
            r"laptop",
            r"notebook",
            r"macbook",
            r"ultrabook",
            r"chromebook",
            r"computer",
        ],
        "Tablet": [r"tablet", r"ipad", r"pad"],
        "Keyboard": [
            r"keyboard",
            r"keycap",
            r"mechanical",
            r"gaming\s*keyboard",
            r"rgb",
            r"laptop",
            r"macbook",
            r"notebook",
            r"chromebook",
            r"\bpc\b",
        ],
        "Earbuds": [
            r"earbud",
            r"ear\s*pod",
            r"air\s*pod",
            r"\btws\b",
            r"headphone",
            r"headset",
            r"earphone",
            r"wireless\s*ear",
        ],
        "Headphones": [
            r"headphone",
            r"headset",
            r"earphone",
            r"\banc\b",
            r"over[- ]ear",
        ],
        "Smartwatch": [
            r"smart\s*watch",
            r"apple\s*watch",
            r"galaxy\s*watch",
            r"fitness",
            r"fitbit",
            r"garmin",
            r"amazfit",
            r"mi\s*band",
            r"digital\s*watch",
            r"wearable",
            r"smart\s*band",
        ],
        "Mouse": [
            r"\bmouse\b",
            r"gaming\s*mouse",
            r"wireless\s*mouse",
            r"laptop",
            r"macbook",
            r"notebook",
            r"computer",
        ],
        "Monitor": [
            r"monitor",
            r"display",
            r"\bscreen\b",
            r"\d+\s*inch",
            r"retina",
            r"laptop",
            r"\bhz\b",
            r"oled",
            r"full\s*hd",
        ],
        "Camera": [r"camera", r"lens", r"dslr", r"mirrorless", r"gopro"],
        "Powerbank": [r"power\s*bank", r"charger", r"battery\s*pack", r"mah"],
        "Cooling Pad": [r"cooling", r"pad", r"laptop\s*cool"],
        "Gaming Headset": [r"headset", r"gaming", r"surround"],
    }

    luxury_watch = re.compile(
        r"rolex|omega|cartier|patek|cellini|submariner|daytona",
        re.IGNORECASE,
    )

    def keep(p: Dict[str, Any]) -> bool:
        dc = str(p.get("category") or "").lower()
        title = str(p.get("title") or "")
        desc = str(p.get("description") or "")
        blob = f"{title} {desc}".lower()

        if dc == "groceries" and category != "General":
            return False
        if category == "General" and dc == "groceries":
            return False

        if category == "Keyboard" and dc in ("beauty", "fragrances", "skin-care", "womens-dresses"):
            return False

        if category == "Headphones" and dc in ("kitchen-accessories", "groceries", "home-decoration"):
            if not re.search(r"headphone|headset|earphone|audio", blob, re.IGNORECASE):
                return False

        if category == "Smartwatch" and luxury_watch.search(title):
            return False

        if category == "Earbuds" and re.search(r"\b(speaker|echo)\b", title, re.IGNORECASE):
            if not re.search(r"earbud|headphone|headset|earphone", blob, re.IGNORECASE):
                return False

        if category not in hint_patterns:
            return True

        return any(re.search(pat, blob, re.IGNORECASE) for pat in hint_patterns[category])

    filtered = [p for p in raw_list if keep(p)]
    if filtered:
        return filtered

    def _blob(p: Dict[str, Any]) -> str:
        return f"{p.get('title', '')} {p.get('description', '')}".lower()

    if category in hint_patterns:
        hinted: List[Dict[str, Any]] = []
        for p in raw_list:
            blob = _blob(p)
            if category == "Smartwatch" and luxury_watch.search(str(p.get("title") or "")):
                continue
            if any(re.search(pat, blob, re.IGNORECASE) for pat in hint_patterns[category]):
                hinted.append(p)
        return hinted

    no_groceries = [
        p for p in raw_list if str(p.get("category") or "").lower() != "groceries"
    ]
    if category == "Smartwatch":
        no_lux = [
            p
            for p in no_groceries
            if not luxury_watch.search(str(p.get("title") or ""))
        ]
        return no_lux
    return no_groceries


def _brand_keyword_match(raw: Dict[str, Any], pref: Dict[str, Any]) -> bool:
    brand = (pref.get("brand") or "").strip().lower()
    if not brand:
        return True
    title = str(raw.get("title") or "").lower()
    b = str(raw.get("brand") or "").lower()
    return brand in title or brand in b


def _retrieve(pref: Dict[str, Any], relax_budget: bool) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    category = (pref.get("category") or "").strip()
    if not category:
        pref["category"] = "General"
        pref["category_inferred"] = True
        category = "General"

    raw_list, strat = _fetch_raw_products(pref)
    raw_list = [r for r in raw_list if _brand_keyword_match(r, pref)]

    if not raw_list and (pref.get("brand") or "").strip():
        print("[Agent 2] 0 results with brand filter; broadening catalog search (keeping your brand as a soft signal).")
        pref["brand_relaxed"] = True
        loose = dict(pref)
        loose["brand"] = None
        raw_list, strat = _fetch_raw_products(loose)
        raw_list = _rank_by_relevance(raw_list, pref)

    raw_list = _filter_plausible_products(raw_list, category)

    if not raw_list:
        rescue_q = _rescue_search_seed(category, pref)
        print(f"[Agent 2] Plausibility empty; rescue search: {rescue_q!r}")
        raw_list = search_products_raw(rescue_q, limit=40)
        raw_list = [r for r in raw_list if _brand_keyword_match(r, pref)]
        raw_list = _filter_plausible_products(raw_list, category)

    raw_list = _filter_budget(raw_list, pref, relax=relax_budget)

    if not raw_list and not relax_budget:
        # If the user specified a budget, we should honor it. 
        # We do not relax the budget here to ensure strict adherence.
        print(f"[Agent 2] 0 results found under strict budget. Passing empty list to Alternatives agent.")

    raw_list = _rank_by_relevance(raw_list, pref)
    raw_list = raw_list[:24]

    if not raw_list:
        print("[Agent 2] Still empty; loading emergency category feed.")
        emergency_slug = {
            "Keyboard": "laptops",
            "Monitor": "laptops",
            "Cooling Pad": "laptops",
            "Headphones": "mobile-accessories",
            "Earbuds": "mobile-accessories",
            "Gaming Headset": "mobile-accessories",
            "Smartwatch": "mobile-accessories",
            "Powerbank": "mobile-accessories",
        }.get(category, "smartphones")
        data = get_json(
            f"{DUMMYJSON_BASE}/products/category/{urllib.parse.quote(emergency_slug, safe='')}?limit=40"
        )
        raw_list = (data or {}).get("products") or []
        raw_list = [p for p in raw_list if str(p.get("category") or "").lower() != "groceries"]
        # CRITICAL: Even emergency feed MUST respect budget
        raw_list = _filter_budget(raw_list, pref, relax=False)
        raw_list = _rank_by_relevance(raw_list, pref)
        strat += f" | emergency cat/{emergency_slug} (budget-filtered)"

    brand = (pref.get("brand") or "").strip()
    ddg_text = _duckduckgo_abstract(brand, category)

    llm_map = _extract_key_features_llm(raw_list, ddg_text)
    normalized: List[Dict[str, Any]] = []
    for i, raw in enumerate(raw_list[:10], start=1):
        feats = llm_map.get(i) or _heuristic_features(str(raw.get("description") or ""))
        rev = []
        if ddg_text:
            rev.append(ddg_text[:400])
        desc = str(raw.get("description") or "")
        if desc:
            rev.append(desc[:320])
        np = _normalize_product(raw, category, feats, ddg_text, rev)
        normalized.append(np)

    strategy = f"DummyJSON + DDG + features | {strat}"
    return normalized[:10], strategy, pref


def process(state: Dict[str, Any]) -> Dict[str, Any]:
    pref = state.get("extracted_preferences") or {}
    products, strategy_used, pref = _retrieve(pref, relax_budget=False)
    state["products"] = products
    state["retrieval_strategy"] = strategy_used
    state["extracted_preferences"] = pref
    return state


def recover_for_empty_state(state: Dict[str, Any]) -> Dict[str, Any]:
    pref = state.get("extracted_preferences") or {}
    pref["fallback_used"] = True
    products, strategy_used, pref = _retrieve(pref, relax_budget=True)
    return {
        "products": products,
        "retrieval_strategy": f"{strategy_used} [empty_recovery]",
        "extracted_preferences": pref,
    }
