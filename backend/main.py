import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.graph import build_graph
from catalog_api import browse_products, get_all_categories, get_stats, verify_catalog_connectivity
from feedback_store import save_feedback

pipeline = build_graph()


def run_pipeline(query: str):
    return pipeline.invoke({"query": query})


@asynccontextmanager
async def lifespan(app: FastAPI):
    verify_catalog_connectivity()
    yield


app = FastAPI(title="AuraCart API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class FeedbackRequest(BaseModel):
    query: str
    result_id: int
    rating: int
    comment: str


@app.post("/advise")
async def advise(req: QueryRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, run_pipeline, req.query.strip()),
            timeout=90.0,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Request timed out. Try a simpler query.",
        )
    except Exception as e:
        print(f"Error in pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "catalog": "DummyJSON"}


@app.get("/categories")
def categories():
    return get_all_categories()


@app.get("/products/{category}")
def products(category: str):
    return browse_products(category)


@app.get("/stats")
def stats():
    return get_stats()


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    save_feedback(req.query, req.result_id, req.rating, req.comment)
    return {"status": "saved"}


@app.get("/test-queries")
def test_queries():
    return {
        "Smartphones": [
            "I need a good phone under 100k",
            "Best camera phone for a traveler",
            "Cheapest smartphone for a student",
            "Give me a gaming phone under 150000",
            "I want to upgrade my old phone, budget is high",
            "Samsung phone with best battery",
            "iPhone alternative under 60k",
            "Phone with best display for watching movies",
            "Latest flip phone with good hinges",
            "Waterproof phone for outdoors",
        ],
        "Laptops": [
            "Best value laptop for CS student",
            "Heavy gaming laptop no budget",
            "Lightest laptop for office work",
            "MacBook alternative for office",
            "Laptop under 120000",
            "Good cooling laptop for render",
            "Dell or HP for daily tasks",
            "Cheap laptop",
            "Touchscreen laptop for artists",
            "Longest battery life laptop for travel",
        ],
        "Footwear": [
            "Comfortable heels for office",
            "Black heels for a wedding under 10000",
            "Best running shoes Nike",
            "Cheap walking shoes",
            "White sneakers for men",
            "Leather boots for winter",
            "Sandals for beach",
        ],
        "Audio": [
            "Noise cancelling earbuds for traveler",
            "Best ANC headphones under 20k",
            "Loud bluetooth speaker for parties",
            "Earbuds with longest battery",
            "Cheap earphones",
            "Over-ear studio headphones",
            "Waterproof speaker for shower",
        ],
        "Wearables": [
            "Smartwatch with 2 week battery",
            "Fitness tracker under 15k",
            "Apple watch for office",
            "Cheap watch that looks good",
            "Smart band with heart rate monitor",
        ],
        "Cameras": [
            "Camera for vlogging",
            "Action camera for traveler",
            "Beginner DSLR camera",
            "Sony camera",
            "Compact camera for street photography",
        ],
        "Gaming": [
            "Mechanical keyboard red switches",
            "Lightweight gaming mouse",
            "Surround sound headset",
            "144hz monitor for student",
            "RGB gaming monitor keyboard bundle",
            "Wireless gaming mouse for competitive play",
        ],
        "Edge Cases": [
            "I have no budget show me best things",
            "i want product",
            "gjhgjg",
            "10 million budget",
            "nothing specific just buy",
            "Show me everything you have",
            "Search for nothing",
        ],
        "Conflicting Preferences": [
            "Gaming laptop but must be very lightweight and cheap",
            "Best ANC headphones under 3000",
            "Heavy duty camera but feather light",
            "RTX 4060 laptop under 50000",
            "High end smartphone but price should be zero",
        ],
        "Accessories": [
            "Fast powerbank for traveling",
            "Cooling pad for gaming laptop",
            "Small powerbank",
            "USB-C hub for MacBook",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
