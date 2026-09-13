import asyncio
import uuid
from typing import Optional, List
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.models import (
    ReviewCreate, Review, ManualAnalyzeRequest, ResponseDraftRequest,
    SendResponseRequest, ScrapeRequest, HotelInfo, WebSocketBroadcast
)
from backend.database import (
    init_db, get_all_reviews, get_review_by_id, insert_review,
    update_review, delete_review, get_hotel_info, update_hotel_info,
    get_activity_logs, add_activity_log, compute_stats
)
from backend.services.llm_service import llm_service
from backend.scrapers.selenium_scraper import selenium_scraper
from backend.websocket_manager import ws_manager

# Create FastAPI app
app = FastAPI(
    title="Clear Vision — Hospitality Sentiment Repair API",
    description="Backend API powered by Python, Selenium, LLM APIs, REST, and WebSockets",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("[ClearVision] Initializing SQLite database...")
    init_db()
    print("[ClearVision] Database ready. Clear Vision backend started successfully on port", settings.PORT)

# --- WebSocket Live Endpoint ---

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Listen for client messages (e.g., ping, scrape requests)
            data = await websocket.receive_text()
            # Echo or process client command if needed
            if data == "ping":
                await websocket.send_json({"event": "pong", "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# --- REST APIs ---

@app.get("/api/health")
async def health_check():
    stats = compute_stats()
    return {
        "status": "online",
        "service": "Clear Vision Backend",
        "version": "2.0.0",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "has_openai_key": bool(settings.OPENAI_API_KEY),
        "selenium_headless": settings.SELENIUM_HEADLESS,
        "total_reviews": stats["total_reviews"],
        "connected_ws_clients": len(ws_manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/reviews", response_model=List[Review])
async def list_reviews(
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: positive, neutral, negative, all"),
    rating: Optional[int] = Query(None, description="Filter by rating: 1-5"),
    platform: Optional[str] = Query(None, description="Filter by platform: Google, TripAdvisor, Yelp, Booking.com, Airbnb")
):
    return get_all_reviews(sentiment=sentiment, rating=rating, platform=platform)

@app.get("/api/reviews/{review_id}", response_model=Review)
async def get_review(review_id: int):
    rev = get_review_by_id(review_id)
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found")
    return rev

@app.post("/api/reviews", response_model=Review)
async def create_new_review(review_in: ReviewCreate):
    """
    Submits a review, analyzes sentiment with LLM/NLP, generates personalized hospitality repair response,
    saves to DB, and broadcasts live over WebSockets.
    """
    hotel = get_hotel_info()
    
    # 1. AI Sentiment Analysis
    analysis = await llm_service.analyze_sentiment(
        text=review_in.text,
        rating=review_in.rating,
        guest_name=review_in.name,
        platform=review_in.platform
    )

    # 2. AI Hospitality Repair Response Generation
    resp_data = await llm_service.generate_response(
        review_text=review_in.text,
        guest_name=review_in.name,
        rating=review_in.rating,
        sentiment=analysis.sentiment,
        issues=analysis.issues,
        hotel_name=hotel["name"]
    )

    # 3. Store into DB
    review_dict = {
        "name": review_in.name,
        "platform": review_in.platform,
        "rating": review_in.rating,
        "date": review_in.date or datetime.now().strftime("%b %d, %Y · %H:%M"),
        "category": review_in.category,
        "text": review_in.text,
        "sentiment": analysis.sentiment,
        "score": analysis.score,
        "issues": analysis.issues,
        "sent": False,
        "response": resp_data["response"],
        "response_type": resp_data["response_type"],
        "churn_risk_score": analysis.churn_risk_score,
        "urgency": analysis.urgency
    }

    created = insert_review(review_dict)

    # 4. Broadcast in real time over WebSockets
    await ws_manager.broadcast_new_review(created)
    await ws_manager.broadcast_stats_update(compute_stats())

    return created

@app.put("/api/reviews/{review_id}", response_model=Review)
async def update_single_review(review_id: int, update_data: dict):
    updated = update_review(review_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Review not found")
    await ws_manager.broadcast_review_updated(updated)
    return updated

@app.delete("/api/reviews/{review_id}")
async def delete_single_review(review_id: int):
    success = delete_review(review_id)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    await ws_manager.broadcast_stats_update(compute_stats())
    return {"message": "Review deleted successfully"}

@app.post("/api/reviews/{review_id}/respond")
async def generate_response_for_review(review_id: int, req: ResponseDraftRequest):
    rev = get_review_by_id(review_id)
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found")
    
    hotel = get_hotel_info()
    resp_data = await llm_service.generate_response(
        review_text=rev["text"],
        guest_name=rev["name"],
        rating=rev["rating"],
        sentiment=rev["sentiment"],
        issues=rev["issues"],
        hotel_name=hotel["name"],
        tone=req.tone or "empathetic_luxury"
    )

    updated = update_review(review_id, {
        "response": resp_data["response"],
        "response_type": resp_data["response_type"]
    })
    await ws_manager.broadcast_review_updated(updated)
    return resp_data

@app.post("/api/reviews/{review_id}/send")
async def send_response_to_guest(review_id: int, req: SendResponseRequest):
    rev = get_review_by_id(review_id)
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found")
    
    updated = update_review(review_id, {
        "sent": True,
        "response": req.response
    })

    add_activity_log(
        log_type="response_sent",
        title=f"Recovery Dispatched: {rev['name']}",
        description=f"Sent official {rev.get('response_type', 'Recovery')} response via {rev['platform']}.",
        badge_color="accent3"
    )

    await ws_manager.broadcast_review_updated(updated)
    await ws_manager.broadcast_stats_update(compute_stats())
    return {"message": "Response dispatched successfully", "review": updated}

@app.post("/api/analyze")
async def manual_sentiment_analysis(req: ManualAnalyzeRequest):
    """Direct analysis endpoint for custom text without saving."""
    analysis = await llm_service.analyze_sentiment(
        text=req.text,
        rating=req.rating or 3,
        guest_name=req.guest_name or "Guest",
        platform=req.platform or "Google"
    )
    hotel = get_hotel_info()
    resp = await llm_service.generate_response(
        review_text=req.text,
        guest_name=req.guest_name or "Guest",
        rating=req.rating or 3,
        sentiment=analysis.sentiment,
        issues=analysis.issues,
        hotel_name=hotel["name"]
    )
    return {
        "analysis": analysis,
        "draft_response": resp
    }

@app.post("/api/scrape")
async def trigger_selenium_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Triggers the Selenium scraper to harvest reviews from Google, TripAdvisor, Yelp, or Booking.com.
    Logs each step in real time via WebSockets and ingests all scraped reviews with automated AI repairs.
    """
    job_id = f"scrape_{uuid.uuid4().hex[:8]}"

    async def run_scrape_task():
        try:
            hotel = get_hotel_info()
            scraped_items = await selenium_scraper.scrape_reviews_live(
                target_url=req.url,
                hotel_name=req.hotel_name or hotel["name"],
                platform=req.platform,
                max_reviews=req.max_reviews,
                job_id=job_id
            )

            # Ingest each review through AI analysis
            for item in scraped_items:
                analysis = await llm_service.analyze_sentiment(
                    text=item["text"],
                    rating=item["rating"],
                    guest_name=item["name"],
                    platform=item["platform"]
                )
                resp = await llm_service.generate_response(
                    review_text=item["text"],
                    guest_name=item["name"],
                    rating=item["rating"],
                    sentiment=analysis.sentiment,
                    issues=analysis.issues,
                    hotel_name=hotel["name"]
                )

                rev_data = {
                    "name": item["name"],
                    "platform": item["platform"],
                    "rating": item["rating"],
                    "date": item["date"],
                    "category": item["category"],
                    "text": item["text"],
                    "sentiment": analysis.sentiment,
                    "score": analysis.score,
                    "issues": analysis.issues,
                    "sent": False,
                    "response": resp["response"],
                    "response_type": resp["response_type"],
                    "churn_risk_score": analysis.churn_risk_score,
                    "urgency": analysis.urgency
                }
                new_rev = insert_review(rev_data)
                await ws_manager.broadcast_new_review(new_rev)
                await asyncio.sleep(0.4)

            await ws_manager.broadcast_stats_update(compute_stats())
            await ws_manager.broadcast("scraper_completed", {
                "job_id": job_id,
                "total_ingested": len(scraped_items),
                "platform": req.platform
            })

        except Exception as e:
            await ws_manager.broadcast_scraper_log(job_id, f"❌ Error during scrape: {str(e)}", "error", 100)

    # Launch task in background
    asyncio.create_task(run_scrape_task())

    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Selenium scraping task initiated for {req.platform}. Stream logs via WebSocket /ws/live"
    }

@app.get("/api/stats")
async def get_dashboard_stats():
    return compute_stats()

@app.get("/api/activity")
async def get_activity():
    return get_activity_logs(limit=20)

@app.get("/api/hotel")
async def get_hotel():
    return get_hotel_info()

@app.put("/api/hotel")
async def update_hotel(hotel_in: dict):
    return update_hotel_info(hotel_in)

@app.get("/api/churn-alerts")
async def get_churn_radar():
    reviews = get_all_reviews()
    # Find guests with negative reviews or high churn risk
    at_risk = []
    for r in reviews:
        if r.get("churn_risk_score", 0) > 60 or r.get("rating", 3) <= 2:
            at_risk.append({
                "name": r["name"],
                "platform": r["platform"],
                "churn_score": r.get("churn_risk_score", 80),
                "sentiment_trend": "Declining",
                "trigger_issue": r.get("issues", ["Service Quality"])[0] if r.get("issues") else "General Dissatisfaction",
                "urgency": r.get("urgency", "high"),
                "recommended_action": "Immediate Phone Call & 50% Refund Voucher" if r.get("rating") == 1 else "Direct Email & Dining Credit"
            })
    return at_risk

@app.get("/api/staff")
async def get_staff_tracker():
    return [
        {
            "name": "Arjun Sharma",
            "role": "Head Concierge",
            "dept": "Front Office",
            "praise_count": 14,
            "complaint_count": 0,
            "sentiment_index": 98,
            "badge": "Top Performer ⭐"
        },
        {
            "name": "Meera Patel",
            "role": "Front Desk Supervisor",
            "dept": "Front Office",
            "praise_count": 8,
            "complaint_count": 2,
            "sentiment_index": 78,
            "badge": "Active Service"
        },
        {
            "name": "Vikram Sethi",
            "role": "F&B Operations Lead",
            "dept": "Dining",
            "praise_count": 5,
            "complaint_count": 4,
            "sentiment_index": 54,
            "badge": "Coaching Recommended ⚠️"
        },
        {
            "name": "Sunita Rao",
            "role": "Executive Housekeeper",
            "dept": "Housekeeping",
            "praise_count": 11,
            "complaint_count": 1,
            "sentiment_index": 91,
            "badge": "Excellence in Cleanliness ⭐"
        }
    ]

@app.get("/api/competitors")
async def get_competitor_benchmarks():
    return {
        "city": "Hyderabad",
        "rankings": [
            {"name": "The Grand ClearVision (You)", "brand_health": 88, "nps": "+68", "avg_rating": 4.6, "is_self": True},
            {"name": "ITC Kohenur Luxury Collection", "brand_health": 85, "nps": "+62", "avg_rating": 4.5, "is_self": False},
            {"name": "Taj Falaknuma Palace", "brand_health": 84, "nps": "+60", "avg_rating": 4.5, "is_self": False},
            {"name": "Park Hyatt Hyderabad", "brand_health": 79, "nps": "+48", "avg_rating": 4.3, "is_self": False},
            {"name": "Novotel Convention Centre", "brand_health": 72, "nps": "+38", "avg_rating": 4.1, "is_self": False}
        ],
        "strengths": [
            "Concierge & Personalized Dining recognition (98% satisfaction)",
            "Rapid automated sentiment recovery turnaround (< 15 mins)",
            "Hygiene and Room Sanitization rating (+14% vs market avg)"
        ],
        "gaps": [
            "Check-in queue times during 2-4 PM surge (+18 min delay)",
            "Gym treadmill service intervals requiring expedited maintenance"
        ]
    }

# --- Serve Frontend index.html ---
BASE_HTML = Path(__file__).resolve().parent.parent / "index.html"

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if BASE_HTML.exists():
        return FileResponse(str(BASE_HTML), media_type="text/html")
    return HTMLResponse("<h1>Clear Vision Backend is Running</h1><p>index.html not found in root directory.</p>")
