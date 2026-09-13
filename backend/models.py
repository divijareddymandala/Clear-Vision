from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ReviewBase(BaseModel):
    name: str = Field(..., description="Name of the guest / reviewer")
    platform: str = Field("Google", description="Review platform e.g. Google, TripAdvisor, Yelp, Booking.com, Airbnb")
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")
    category: str = Field("Room Quality", description="Primary category of the review")
    text: str = Field(..., description="Review text content")

class ReviewCreate(ReviewBase):
    date: Optional[str] = None
    auto_analyze: bool = True
    auto_respond: bool = True

class AnalysisResult(BaseModel):
    sentiment: str = Field(..., description="Sentiment classification: positive, neutral, negative")
    score: int = Field(..., ge=0, le=100, description="Sentiment score from 0 to 100")
    issues: List[str] = Field(default_factory=list, description="Extracted hospitality issue categories")
    churn_risk_score: int = Field(0, ge=0, le=100, description="Predicted churn probability (0-100)")
    urgency: str = Field("normal", description="Urgency level: low, normal, high, critical")
    root_cause: Optional[str] = None
    department: Optional[str] = None
    staff_mentioned: Optional[List[str]] = None

class Review(ReviewBase):
    id: int
    date: str
    sentiment: str = "neutral"
    score: int = 50
    issues: List[str] = Field(default_factory=list)
    sent: bool = False
    response: Optional[str] = None
    response_type: Optional[str] = None  # e.g. 'Standard Recovery', 'Manager Escalation', 'VIP Delight'
    churn_risk_score: int = 0
    urgency: str = "normal"
    created_at: Optional[str] = None

class ManualAnalyzeRequest(BaseModel):
    text: str
    rating: Optional[int] = 3
    platform: Optional[str] = "Google"
    guest_name: Optional[str] = "Guest"
    category: Optional[str] = "General"

class ResponseDraftRequest(BaseModel):
    tone: Optional[str] = "empathetic_luxury"  # 'empathetic_luxury', 'professional', 'concise'
    custom_compensation: Optional[str] = None
    manager_name: Optional[str] = "General Manager"

class SendResponseRequest(BaseModel):
    response: str

class ScrapeRequest(BaseModel):
    url: Optional[str] = Field(None, description="Direct URL to Google Maps / TripAdvisor / Yelp / Booking.com hotel page")
    hotel_name: Optional[str] = Field("The Grand ClearVision", description="Hotel name to search for")
    platform: str = Field("Google", description="Target platform: Google, TripAdvisor, Yelp, Booking.com")
    max_reviews: int = Field(5, ge=1, le=25, description="Maximum number of reviews to extract")
    simulate_if_blocked: bool = Field(True, description="Fallback to high-fidelity live simulation if anti-bot blocks Selenium")

class ScrapeJobStatus(BaseModel):
    job_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    platform: str
    total_found: int = 0
    message: str = ""
    logs: List[str] = Field(default_factory=list)

class HotelInfo(BaseModel):
    name: str = "The Grand ClearVision"
    tagline: str = "Luxury Redefined in the Heart of the City"
    phone: str = "+91 40 4567 8900"
    email: str = "guestrelations@grandclearvision.com"
    address: str = "Road No. 2, Banjara Hills, Hyderabad, Telangana 500034"
    checkin: str = "2:00 PM"
    checkout: str = "12:00 PM"
    rooms: int = 248
    owner: str = "ClearVision Luxury Hospitality Group"
    rating: float = 4.6

class ActivityLogItem(BaseModel):
    id: int
    timestamp: str
    type: str  # 'alert', 'response_sent', 'scraped', 'churn_flag', 'analysis'
    title: str
    description: str
    badge_color: Optional[str] = "accent"

class WebSocketBroadcast(BaseModel):
    event: str  # 'new_review', 'review_updated', 'scraper_log', 'scraper_completed', 'churn_alert', 'stats_updated'
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
