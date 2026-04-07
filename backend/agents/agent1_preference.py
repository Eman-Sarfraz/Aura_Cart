from typing import Dict, Any
import json
import re

from langchain_core.prompts import PromptTemplate
from .llm_helper import invoke_llm_text, _api_key_ok
from .query_match import phrase_or_word_in_query

VALID_CATEGORIES = frozenset(
    {
        "Smartphone",
        "Laptop",
        "Heels",
        "Shoes",
        "Earbuds",
        "Headphones",
        "Tablet",
        "Smartwatch",
        "Camera",
        "Monitor",
        "Keyboard",
        "Mouse",
        "Powerbank",
        "Speaker",
        "Gaming Headset",
        "Cooling Pad",
        "Bags",
        "Clothing",
        "Makeup",
        "Skincare",
        "Fragrance",
    }
)

CATEGORY_MAP = {
    "gaming laptop": "Laptop",
    "power bank": "Powerbank",
    "gaming headset": "Gaming Headset",
    "cooling pad": "Cooling Pad",
    "noise cancelling": "Headphones",
    "noise canceling": "Headphones",
    "stiletto": "Heels",
    "stilettos": "Heels",
    "heel": "Heels",
    "heels": "Heels",
    "pump": "Heels",
    "pumps": "Heels",
    "sneaker": "Shoes",
    "sneakers": "Shoes",
    "running shoe": "Shoes",
    "running shoes": "Shoes",
    "shoe": "Shoes",
    "shoes": "Shoes",
    "boot": "Shoes",
    "boots": "Shoes",
    "sandal": "Shoes",
    "sandals": "Shoes",
    "loafer": "Shoes",
    "smartphone": "Smartphone",
    "smartphones": "Smartphone",
    "iphone": "Smartphone",
    "android": "Smartphone",
    "galaxy": "Smartphone",
    "mobile": "Smartphone",
    "cellphone": "Smartphone",
    "cell phone": "Smartphone",
    "phone": "Smartphone",
    "macbook": "Laptop",
    "chromebook": "Laptop",
    "notebook": "Laptop",
    "ultrabook": "Laptop",
    "laptop": "Laptop",
    "laptops": "Laptop",
    "gaming pc": "Laptop",
    "gaming phone": "Smartphone",
    "earbuds": "Earbuds",
    "earbud": "Earbuds",
    "airpods": "Earbuds",
    "airpod": "Earbuds",
    "tws": "Earbuds",
    "headphones": "Headphones",
    "headphone": "Headphones",
    "earphones": "Headphones",
    "earphone": "Headphones",
    "headset": "Headphones",
    "over-ear": "Headphones",
    "over ear": "Headphones",
    "anc": "Headphones",
    "tablet": "Tablet",
    "tablets": "Tablet",
    "ipad": "Tablet",
    "smartwatch": "Smartwatch",
    "smartwatches": "Smartwatch",
    "watch": "Smartwatch",
    "fitness band": "Smartwatch",
    "fitness tracker": "Smartwatch",
    "dslr": "Camera",
    "mirrorless": "Camera",
    "gopro": "Camera",
    "action camera": "Camera",
    "vlogging": "Camera",
    "camera": "Camera",
    "cameras": "Camera",
    "monitor": "Monitor",
    "monitors": "Monitor",
    "display": "Monitor",
    "screen": "Monitor",
    "144hz": "Monitor",
    "mechanical keyboard": "Keyboard",
    "keyboard": "Keyboard",
    "keyboards": "Keyboard",
    "mouse": "Mouse",
    "mice": "Mouse",
    "speaker": "Speaker",
    "speakers": "Speaker",
    "bluetooth speaker": "Speaker",
    "powerbank": "Powerbank",
    "powerbanks": "Powerbank",
    "handbag": "Bags",
    "handbags": "Bags",
    "backpack": "Bags",
    "backpacks": "Bags",
    "tote": "Bags",
    "briefcase": "Bags",
    "purse": "Bags",
    "clutch": "Bags",
    "leather bag": "Bags",
    "shoulder bag": "Bags",
    "bag": "Bags",
    "bags": "Bags",
    "kurta": "Clothing",
    "shirt": "Clothing",
    "dress": "Clothing",
    "jeans": "Clothing",
    "apparel": "Clothing",
    "lipstick": "Makeup",
    "foundation": "Makeup",
    "concealer": "Makeup",
    "makeup": "Makeup",
    "lotion": "Skincare",
    "cleanser": "Skincare",
    "moisturizer": "Skincare",
    "skincare": "Skincare",
    "perfume": "Fragrance",
    "cologne": "Fragrance",
    "scent": "Fragrance",
    "fragrance": "Fragrance",
}

def _map_key_rank(key: str) -> tuple:
    return (-len(key.replace("-", " ").split()), -len(key))

# Normalizes common LLM / user phrasing not present in CATEGORY_MAP keys
CATEGORY_ALIASES = {
    "smart phone": "Smartphone",
    "smart phones": "Smartphone",
    "mobile phone": "Smartphone",
    "mobile phones": "Smartphone",
    "cell phone": "Smartphone",
    "cell phones": "Smartphone",
    "wristwatch": "Smartwatch",
    "wrist watch": "Smartwatch",
    "smart watch": "Smartwatch",
    "running shoes": "Shoes",
    "walking shoes": "Shoes",
    "casual shoes": "Shoes",
    "dress shoes": "Shoes",
    "high heels": "Heels",
    "high heel": "Heels",
    "pumps": "Heels",
    "wireless earbuds": "Earbuds",
    "tws earbuds": "Earbuds",
    "over ear headphones": "Headphones",
    "on ear headphones": "Headphones",
    "bluetooth speaker": "Speaker",
    "external monitor": "Monitor",
    "computer monitor": "Monitor",
    "gaming monitor": "Monitor",
    "wireless mouse": "Mouse",
    "gaming mouse": "Mouse",
    "gaming keyboard": "Keyboard",
    "mechanical keyboard": "Keyboard",
    "power bank": "Powerbank",
    "portable charger": "Powerbank",
}


def validate_category(raw_cat: str) -> str:
    """Normalizes the extracted category securely."""
    if not raw_cat:
        return ""
    q = raw_cat.strip().lower()
    if q in CATEGORY_MAP:
        return CATEGORY_MAP[q]
    if q in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[q]

    for valid in VALID_CATEGORIES:
        if q == valid.lower():
            return valid

    return ""

def _python_preference(query: str) -> Dict[str, Any]:
    raw = query.strip()
    q = raw.lower()

    category = ""
    matched_cat_key = ""
    # Prefer earbuds when the user explicitly mentions them (over "noise cancelling" → headphones)
    if re.search(r"\bearbuds?\b", q) or "airpods" in q or "tws" in q:
        category = "Earbuds"
        matched_cat_key = "earbuds"

    if not category:
        for key in sorted(CATEGORY_MAP.keys(), key=_map_key_rank):
            if phrase_or_word_in_query(key, q):
                category = CATEGORY_MAP[key]
                matched_cat_key = key
                break

    if not category:
        for cat in sorted(VALID_CATEGORIES, key=lambda c: (-len(c.split()), -len(c))):
            if phrase_or_word_in_query(cat, q):
                category = cat
                matched_cat_key = cat.lower()
                break

    budget_num = None
    # "100k", "80 k" → thousands PKR
    km = re.search(r"(?:under|below|less than|budget)?\s*(\d[\d,]*)\s*k\b", q)
    if km:
        budget_num = int(km.group(1).replace(",", "")) * 1000
    if budget_num is None:
        patterns = [
            r"under\s+(\d[\d,]*)",
            r"below\s+(\d[\d,]*)",
            r"less than\s+(\d[\d,]*)",
            r"(\d[\d,]*)\s*pkr",
            r"(\d[\d,]*)\s*rupees",
            r"(\d[\d,]*)\s*rs",
            r"budget\s+(\d[\d,]*)",
            r"(\d{4,7})",
        ]
        for pattern in patterns:
            match = re.search(pattern, q)
            if match:
                num_str = match.group(1).replace(",", "")
                budget_num = int(num_str)
                break

    if budget_num is None:
        nums = re.findall(r"\d+", q.replace(",", ""))
        candidates = [int(n) for n in nums if int(n) > 500]
        if candidates:
            budget_num = max(candidates)

    priorities = []
    
    clean_q = q
    if matched_cat_key:
        clean_q = clean_q.replace(matched_cat_key, "")
        if matched_cat_key != category.lower():
            priorities.append(matched_cat_key)

    stop_words = ["under", "below", "less than", "pkr", "rupees", "rs", "budget", "i", "need", "a", "good", "best", "give", "me", "show", "want", "for", "the", "with", "buy"]
    for sw in stop_words:
        clean_q = re.sub(rf"\b{sw}\b", "", clean_q)
    clean_q = re.sub(r"\d[\d,]*", "", clean_q)

    for word in clean_q.split():
        if len(word) >= 3 and word not in priorities:
            priorities.append(word)

    return {
        "category": category, # Initial python guess
        "brand": None,
        "price_min": None,
        "price_max": budget_num,
        "keywords": priorities
    }

def process(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state["query"]
    
    # Python extraction first — fast, no LLM needed
    data = _python_preference(query)
    
    if _api_key_ok():
        prompt = PromptTemplate.from_template(
            """Extract shopping intent from the query into strict JSON.
Rules:
- category: A single precise noun matching the user's core intent (e.g., laptop, smartphone, shoes, heels). Never use vague terms.
- brand: The company name if present (e.g., Apple, Sony, Nike), or null.
- price_min: Integer if mentioned, or null.
- price_max: Integer if mentioned, or null.
- keywords: Array of important features (e.g., "gaming", "noise cancelling", "tws").

Query: "{query}"
JSON:"""
        )
        try:
            content = invoke_llm_text(
                prompt,
                {"query": query},
                timeout_sec=6.0,
                max_tokens=200,
            )
            # Remove markdown blocks
            if "```json" in content:
                content = content.split("```json")[-1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
                
            parsed = json.loads(content.strip())
            
            # Update data safely
            if parsed.get("category"):
                data["category"] = parsed["category"]
            if parsed.get("brand"):
                data["brand"] = parsed["brand"]
            if parsed.get("price_min") is not None:
                data["price_min"] = parsed["price_min"]
            if parsed.get("price_max") is not None:
                data["price_max"] = parsed["price_max"]
            if isinstance(parsed.get("keywords"), list):
                # merge keywords
                data["keywords"] = list(set(data["keywords"] + parsed["keywords"]))
                
        except Exception as e:
            print(f"Agent 1 LLM failed: {e}")

    # Prefer Python budget when the query uses "100k" style amounts — LLMs often return 100 instead of 100000
    if re.search(r"\d[\d,]*\s*k\b", query.lower()):
        py_b = _python_preference(query).get("price_max")
        if py_b:
            data["price_max"] = py_b

    # If user clearly asked for earbuds, do not let the LLM relabel as headphones
    if re.search(r"\bearbuds?\b", query.lower()) or "airpods" in query.lower():
        data["category"] = "earbuds"

    # CATEGORY NORMALIZATION (MANDATORY)
    normalized_cat = validate_category(data.get("category") or "")
    if not normalized_cat:
        # If the LLM failed to give a valid category, or the user input is unrecognizable,
        # fallback purely on the Python categorization that we did over the raw query.
        python_cat = _python_preference(query)["category"]
        if python_cat:
            normalized_cat = validate_category(python_cat)
            
    data["category"] = normalized_cat
    if not data["category"]:
        data["category"] = "General"
        data["category_inferred"] = True

    # Store legacy fields for compatibility with other agents if they depend on them
    data["budget_num"] = data["price_max"] or 99999999
    data["budget"] = f"₨ {data['budget_num']:,}" if data["price_max"] else None
    data["priorities"] = data["keywords"]
    data["original_query"] = query

    print(f"[Agent 1] Extracted Intent: {json.dumps(data, indent=2)}")

    state["extracted_preferences"] = data
    return state
