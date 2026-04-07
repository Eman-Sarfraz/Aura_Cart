"""
Live product catalog via DummyJSON (no local SQLite for products).
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

DUMMYJSON_BASE = (os.getenv("DUMMYJSON_BASE") or "https://dummyjson.com").rstrip("/")
PKR_PER_USD = float(os.getenv("PKR_PER_USD") or "278.0")
REQUEST_TIMEOUT_SEC = float(os.getenv("HTTP_TIMEOUT_SEC") or "12.0")


def get_json(url: str, retries: int = 4) -> Optional[Dict[str, Any]]:
    last_err: Optional[Exception] = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AuraCart/2.0 (edu)"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 502, 503, 504) and attempt < retries - 1:
                time.sleep(0.75 * (attempt + 1))
                continue
            print(f"[catalog_api] GET failed {url}: {e}")
            return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            print(f"[catalog_api] GET failed {url}: {e}")
            return None
    if last_err:
        print(f"[catalog_api] GET failed {url}: {last_err}")
    return None


def verify_catalog_connectivity() -> bool:
    data = get_json(f"{DUMMYJSON_BASE}/products?limit=1")
    ok = bool(data and "products" in data)
    print(f"[catalog_api] DummyJSON reachable: {ok}")
    return ok


def get_stats() -> Dict[str, Any]:
    data = get_json(f"{DUMMYJSON_BASE}/products?limit=1")
    if not data:
        return {"total_products": 0, "categories_count": 0, "avg_rating": 0.0}
    total = int(data.get("total") or 0)
    cats = get_json(f"{DUMMYJSON_BASE}/products/categories")
    n_cats = len(cats) if isinstance(cats, list) else 0
    return {
        "total_products": total,
        "categories_count": n_cats,
        "avg_rating": 4.2,
        "source": "DummyJSON",
    }


def _emoji_for_slug(s: str) -> str:
    mapping = {
        "smartphones": "📱",
        "laptops": "💻",
        "tablets": "📱",
        "fragrances": "🌸",
        "beauty": "💄",
        "skin-care": "✨",
        "womens-shoes": "👠",
        "mens-shoes": "👟",
        "womens-bags": "👜",
        "mens-watches": "⌚",
        "womens-watches": "⌚",
        "mobile-accessories": "🔋",
        "furniture": "🪑",
        "groceries": "🛒",
        "home-decoration": "🏠",
        "kitchen-accessories": "🍳",
        "sports-accessories": "⚽",
        "sunglasses": "🕶️",
    }
    return mapping.get(s, "🛍️")


def get_all_categories() -> List[Dict[str, str]]:
    raw = get_json(f"{DUMMYJSON_BASE}/products/categories")
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug") or "")
        name = str(item.get("name") or slug)
        out.append({"name": name, "slug": slug, "emoji": _emoji_for_slug(slug)})
    return out


def get_products_by_category_slug(slug: str, limit: int = 30) -> List[Dict[str, Any]]:
    slug = urllib.parse.quote(slug.strip().lower(), safe="")
    data = get_json(f"{DUMMYJSON_BASE}/products/category/{slug}?limit={limit}")
    if not data or not isinstance(data.get("products"), list):
        return []
    return data["products"]


_BROWSE_ALIASES = {
    "smartphones": "smartphones",
    "smartphone": "smartphones",
    "phones": "smartphones",
    "laptops": "laptops",
    "laptop": "laptops",
    "notebook": "laptops",
    "tablets": "tablets",
    "tablet": "tablets",
    "fragrances": "fragrances",
    "fragrance": "fragrances",
    "perfume": "fragrances",
    "beauty": "beauty",
    "makeup": "beauty",
    "skin-care": "skin-care",
    "skincare": "skin-care",
    "womens-bags": "womens-bags",
    "bags": "womens-bags",
    "purses": "womens-bags",
    "tops": "tops",
    "clothing": "tops",
    "shirts": "tops",
    "womens-shoes": "womens-shoes",
    "heels": "womens-shoes",
    "mens-shoes": "mens-shoes",
    "shoes": "mens-shoes",
    "sneakers": "mens-shoes",
    "mens-watches": "mens-watches",
    "womens-watches": "womens-watches",
    "watches": "mens-watches",
    "mobile-accessories": "mobile-accessories",
    "earbuds": "mobile-accessories",
    "headphones": "mobile-accessories",
}


def browse_products(param: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Resolve friendly or slug category names for GET /products/{category}."""
    key = param.strip().lower().replace(" ", "-")
    slug = _BROWSE_ALIASES.get(key, key)
    return get_products_by_category_slug(slug, limit=limit)


def search_products_raw(q: str, limit: int = 50) -> List[Dict[str, Any]]:
    q = q.strip()
    if not q:
        return []
    enc = urllib.parse.quote(q, safe="")
    data = get_json(f"{DUMMYJSON_BASE}/products/search?q={enc}&limit={limit}")
    if not data or not isinstance(data.get("products"), list):
        return []
    return data["products"]
