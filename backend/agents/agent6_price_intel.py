from typing import Dict, Any
import datetime


def process(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state.get("extracted_preferences", {})
    category = prefs.get("category", "") or ""
    month = datetime.datetime.now().month

    if month in [10, 11, 12]:
        trend = "Rising"
        buy_now = False
        forecast = "Prices typically rise 10-15% in Q4 festive season"
        best_time = "January-February for best deals"
        savings = "Save up to 15% by waiting till January"
    elif month in [1, 2, 3]:
        trend = "Dropping"
        buy_now = True
        forecast = "Post-holiday prices are dropping now"
        best_time = "Right now is a great time to buy"
        savings = "Currently at seasonal low prices"
    elif month in [6, 7]:
        trend = "Dropping"
        buy_now = True
        forecast = "Mid-year sales offer good discounts"
        best_time = "Buy now during mid-year sales"
        savings = "Mid-year discounts available"
    else:
        trend = "Stable"
        buy_now = True
        forecast = "Prices are stable — good time to buy"
        best_time = "Prices stable, no need to wait"
        savings = "No major price changes expected"

    state["price_intelligence"] = {
        "market_trend": trend,
        "buy_now": buy_now,
        "price_forecast": forecast,
        "best_time_to_buy": best_time,
        "savings_opportunity": savings,
        "seasonal_note": f"Based on current month analysis for {category or 'general'} category",
    }
    return state
