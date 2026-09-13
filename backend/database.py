import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import settings

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables and seeds initial reviews if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        platform TEXT NOT NULL,
        rating INTEGER NOT NULL,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        text TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        score INTEGER NOT NULL,
        issues_json TEXT NOT NULL DEFAULT '[]',
        sent INTEGER NOT NULL DEFAULT 0,
        response TEXT,
        response_type TEXT DEFAULT 'Standard Recovery',
        churn_risk_score INTEGER DEFAULT 0,
        urgency TEXT DEFAULT 'normal',
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        badge_color TEXT DEFAULT 'accent'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hotel_info (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        tagline TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        checkin TEXT,
        checkout TEXT,
        rooms INTEGER,
        owner TEXT,
        rating REAL DEFAULT 4.6
    );
    """)

    conn.commit()

    # Check if reviews are already seeded
    cursor.execute("SELECT COUNT(*) as count FROM reviews;")
    count = cursor.fetchone()["count"]

    if count == 0:
        seed_initial_data(cursor, conn)

    # Check hotel info
    cursor.execute("SELECT COUNT(*) as count FROM hotel_info;")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
        INSERT INTO hotel_info (id, name, tagline, phone, email, address, checkin, checkout, rooms, owner, rating)
        VALUES (1, 'The Grand ClearVision', 'Luxury Redefined in the Heart of the City', 
                '+91 40 4567 8900', 'guestrelations@grandclearvision.com', 
                'Road No. 2, Banjara Hills, Hyderabad, Telangana 500034',
                '2:00 PM', '12:00 PM', 248, 'ClearVision Luxury Hospitality Group', 4.6);
        """)
        conn.commit()

    conn.close()

def seed_initial_data(cursor: sqlite3.Cursor, conn: sqlite3.Connection):
    initial_reviews = [
        {
            "name": "Sarah M.",
            "platform": "TripAdvisor",
            "rating": 1,
            "date": "Feb 27, 2026 · 08:14",
            "category": "Room Quality",
            "text": "Absolutely terrible experience. The room was filthy — hair in the bathtub, stained sheets, and the AC didn't work all night. Despite calling reception three times, no one came to fix anything. Never coming back. Demanded a refund but got nothing.",
            "sentiment": "negative",
            "score": 12,
            "issues": ["Cleanliness", "Maintenance", "Staff Responsiveness"],
            "sent": 0,
            "response": "Dear Sarah, we are deeply sorry for the unacceptable experience you had during your stay. The conditions you described — unclean room, faulty AC, and unresponsive staff — fall far below our standards. We take this very seriously and are investigating immediately. As a gesture of apology, we would like to offer you a full refund plus a complimentary stay for you to experience the hotel as it should be. A member of our team will contact you within 24 hours. Thank you for bringing this to our attention.",
            "response_type": "Manager Escalation",
            "churn_risk_score": 94,
            "urgency": "critical"
        },
        {
            "name": "Rahul K.",
            "platform": "Google",
            "rating": 2,
            "date": "Feb 26, 2026 · 23:45",
            "category": "Staff Service",
            "text": "The check-in process was a nightmare. Waited 45 minutes at the front desk even though I had a reservation. Staff seemed uninterested and didn't apologize at all. Room was ok but the service completely ruined the stay.",
            "sentiment": "negative",
            "score": 22,
            "issues": ["Check-in/out", "Staff Attitude"],
            "sent": 0,
            "response": "Dear Rahul, we sincerely apologize for the frustrating check-in experience. A 45-minute wait with no acknowledgment is inexcusable. We've flagged this to our Front Office Manager for immediate retraining. We'd love to welcome you back with a 20% discount on your next booking and a guaranteed express check-in. Thank you for your honest feedback — it helps us improve.",
            "response_type": "Service Recovery",
            "churn_risk_score": 82,
            "urgency": "high"
        },
        {
            "name": "Priya S.",
            "platform": "Booking.com",
            "rating": 5,
            "date": "Feb 26, 2026 · 18:30",
            "category": "Staff Service",
            "text": "Absolutely wonderful stay! The concierge team went above and beyond to arrange a surprise anniversary dinner for us. Rooms were immaculate and the breakfast was superb. Will definitely return and recommend to all my friends!",
            "sentiment": "positive",
            "score": 97,
            "issues": [],
            "sent": 1,
            "response": "Dear Priya, your kind words truly made our day! We're thrilled the anniversary dinner was memorable — our concierge team loves creating special moments. We look forward to welcoming you back soon. Thank you for being our guest! 🌹",
            "response_type": "VIP Delight",
            "churn_risk_score": 5,
            "urgency": "low"
        },
        {
            "name": "Tom B.",
            "platform": "Yelp",
            "rating": 2,
            "date": "Feb 26, 2026 · 11:10",
            "category": "Food & Dining",
            "text": "The restaurant food was cold and the portion sizes were laughably small for the price. Waiter spilled water on my laptop and didn't even apologize properly. Pretty disappointed considering the hotel's reputation.",
            "sentiment": "negative",
            "score": 18,
            "issues": ["Food Quality", "Staff Service", "Value"],
            "sent": 0,
            "response": "Dear Tom, we are very sorry about your dining experience. Cold food, unsatisfactory portions, and the incident with your laptop are all unacceptable. We've already spoken with the restaurant manager. We'd like to compensate you with a full dining credit and, if there was any damage to your laptop, please contact our guest relations team and we'll arrange repair/replacement. Thank you for your patience.",
            "response_type": "Incident Compensation",
            "churn_risk_score": 79,
            "urgency": "high"
        },
        {
            "name": "Aisha N.",
            "platform": "Google",
            "rating": 3,
            "date": "Feb 25, 2026 · 14:22",
            "category": "Amenities",
            "text": "Location is great and the pool was clean. However the gym equipment is outdated and two treadmills were out of service. WiFi in the room was also quite slow. Average overall — nothing spectacular but nothing terrible.",
            "sentiment": "neutral",
            "score": 50,
            "issues": ["Amenities", "Connectivity"],
            "sent": 0,
            "response": "Dear Aisha, thank you for your balanced feedback! We're glad you enjoyed the pool and location. We've noted your concerns about the gym equipment — upgrades are actually planned for next month. Our IT team is also reviewing room WiFi speeds. We hope to impress you more on your next visit!",
            "response_type": "Standard Acknowledgment",
            "churn_risk_score": 45,
            "urgency": "normal"
        },
        {
            "name": "David L.",
            "platform": "Airbnb",
            "rating": 1,
            "date": "Feb 25, 2026 · 09:05",
            "category": "Noise/Comfort",
            "text": "Could not sleep at all. Construction noise started at 6am and went on until 10pm. This was never mentioned at booking. Walls are paper-thin and I could hear neighbors' conversations clearly. Total waste of money.",
            "sentiment": "negative",
            "score": 8,
            "issues": ["Noise", "Transparency", "Value"],
            "sent": 0,
            "response": "Dear David, we are truly mortified to hear about your experience. Lack of sleep due to construction noise without prior notice is unacceptable. We have enacted strict quiet hours on our contractors and are re-insulating rooms in that wing. We would like to process an immediate 50% refund and offer you an upgraded quiet suite on your next trip. Please reach out to management directly.",
            "response_type": "Manager Escalation",
            "churn_risk_score": 91,
            "urgency": "critical"
        }
    ]

    now_iso = datetime.now().isoformat()
    for rev in initial_reviews:
        cursor.execute("""
        INSERT INTO reviews (name, platform, rating, date, category, text, sentiment, score, issues_json, sent, response, response_type, churn_risk_score, urgency, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rev["name"], rev["platform"], rev["rating"], rev["date"],
            rev["category"], rev["text"], rev["sentiment"], rev["score"],
            json.dumps(rev["issues"]), rev["sent"], rev["response"],
            rev["response_type"], rev["churn_risk_score"], rev["urgency"], now_iso
        ))

    initial_logs = [
        ("alert", "High Churn Risk Flagged", "Sarah M. (TripAdvisor) flagged at 94% churn risk due to 3 unaddressed complaints.", "accent2"),
        ("response_sent", "Response Dispatched", "VIP appreciation sent to Priya S. (Booking.com 5★).", "accent3"),
        ("scraped", "Live Scraper Ingested", "Initial hotel review corpus synchronized across 5 channels.", "accent4"),
        ("alert", "Escalation to GM", "David L. (Airbnb 1★) noise complaint forwarded to Hotel Operations.", "accent2"),
        ("analysis", "Batch Sentiment Cycle", "Completed automated sentiment & issue breakdown for 6 reviews.", "accent")
    ]

    for log_type, title, desc, color in initial_logs:
        cursor.execute("""
        INSERT INTO activity_logs (timestamp, type, title, description, badge_color)
        VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().strftime("%b %d · %H:%M"), log_type, title, desc, color))

    conn.commit()

# --- Repository Query Helpers ---

def row_to_review(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "platform": row["platform"],
        "rating": row["rating"],
        "date": row["date"],
        "category": row["category"],
        "text": row["text"],
        "sentiment": row["sentiment"],
        "score": row["score"],
        "issues": json.loads(row["issues_json"]) if row["issues_json"] else [],
        "sent": bool(row["sent"]),
        "response": row["response"],
        "response_type": row["response_type"],
        "churn_risk_score": row["churn_risk_score"],
        "urgency": row["urgency"],
        "created_at": row["created_at"]
    }

def get_all_reviews(sentiment: Optional[str] = None, rating: Optional[int] = None, platform: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM reviews WHERE 1=1"
    params = []
    
    if sentiment and sentiment.lower() != "all":
        query += " AND sentiment = ?"
        params.append(sentiment.lower())
    if rating:
        query += " AND rating = ?"
        params.append(rating)
    if platform and platform.lower() != "all":
        query += " AND platform = ?"
        params.append(platform)
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [row_to_review(r) for r in rows]

def get_review_by_id(review_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row_to_review(row)
    return None

def insert_review(review_data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    now_iso = datetime.now().isoformat()
    date_str = review_data.get("date") or datetime.now().strftime("%b %d, %Y · %H:%M")
    issues_json = json.dumps(review_data.get("issues", []))

    cursor.execute("""
    INSERT INTO reviews (name, platform, rating, date, category, text, sentiment, score, issues_json, sent, response, response_type, churn_risk_score, urgency, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        review_data["name"], review_data["platform"], review_data["rating"],
        date_str, review_data["category"], review_data["text"],
        review_data.get("sentiment", "neutral"), review_data.get("score", 50),
        issues_json, int(bool(review_data.get("sent", False))),
        review_data.get("response", ""), review_data.get("response_type", "Standard"),
        review_data.get("churn_risk_score", 0), review_data.get("urgency", "normal"),
        now_iso
    ))
    new_id = cursor.lastrowid
    conn.commit()

    # Log activity
    add_activity_log(
        log_type="analysis" if review_data.get("sentiment") != "negative" else "alert",
        title=f"New Review Analyzed: {review_data['name']} ({review_data['rating']}★)",
        description=f"Sentiment: {review_data.get('sentiment', 'neutral').upper()} (Score: {review_data.get('score', 50)}). Platform: {review_data['platform']}.",
        badge_color="accent3" if review_data.get("sentiment") == "positive" else ("accent2" if review_data.get("sentiment") == "negative" else "accent4"),
        conn=conn
    )

    conn.close()
    return get_review_by_id(new_id)

def update_review(review_id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    set_clauses = []
    params = []
    for k, v in fields.items():
        if k == "issues":
            set_clauses.append("issues_json = ?")
            params.append(json.dumps(v))
        elif k == "sent":
            set_clauses.append("sent = ?")
            params.append(1 if v else 0)
        elif k in ("response", "response_type", "score", "sentiment", "churn_risk_score", "urgency", "rating", "category", "text", "name", "platform"):
            set_clauses.append(f"{k} = ?")
            params.append(v)

    if not set_clauses:
        conn.close()
        return get_review_by_id(review_id)

    params.append(review_id)
    query = f"UPDATE reviews SET {', '.join(set_clauses)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return get_review_by_id(review_id)

def delete_review(review_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_hotel_info() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hotel_info WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "name": "The Grand ClearVision",
        "tagline": "Luxury Redefined",
        "rating": 4.6,
        "rooms": 248
    }

def update_hotel_info(data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    fields = ["name", "tagline", "phone", "email", "address", "checkin", "checkout", "rooms", "owner", "rating"]
    set_clauses = []
    params = []
    for f in fields:
        if f in data:
            set_clauses.append(f"{f} = ?")
            params.append(data[f])
    if set_clauses:
        params.append(1)
        cursor.execute(f"UPDATE hotel_info SET {', '.join(set_clauses)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return get_hotel_info()

def get_activity_logs(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_activity_log(log_type: str, title: str, description: str, badge_color: str = "accent", conn: Optional[sqlite3.Connection] = None):
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%b %d · %H:%M")
    cursor.execute("""
    INSERT INTO activity_logs (timestamp, type, title, description, badge_color)
    VALUES (?, ?, ?, ?, ?)
    """, (now_str, log_type, title, description, badge_color))
    conn.commit()
    if should_close:
        conn.close()

def compute_stats() -> Dict[str, Any]:
    reviews = get_all_reviews()
    total = len(reviews)
    if total == 0:
        return {
            "overall_rating": 5.0,
            "total_reviews": 0,
            "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0},
            "category_scores": {},
            "response_rate": 100,
            "average_sentiment_score": 100
        }

    pos = sum(1 for r in reviews if r["sentiment"] == "positive")
    neu = sum(1 for r in reviews if r["sentiment"] == "neutral")
    neg = sum(1 for r in reviews if r["sentiment"] == "negative")
    sent_count = sum(1 for r in reviews if r.get("sent"))

    total_stars = sum(r["rating"] for r in reviews)
    overall_rating = round(total_stars / total, 1)

    avg_score = round(sum(r["score"] for r in reviews) / total, 1)
    response_rate = round((sent_count / total) * 100) if total > 0 else 100

    star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        if r["rating"] in star_counts:
            star_counts[r["rating"]] += 1

    breakdown = [
        {"stars": s, "count": star_counts[s], "pct": round((star_counts[s] / total) * 100)}
        for s in [5, 4, 3, 2, 1]
    ]

    # Category scores
    cat_map = {
        'Cleanliness': ['Cleanliness', 'Room Quality'],
        'Staff Service': ['Staff Service', 'Check-in/out'],
        'Location': [],
        'Comfort': ['Noise/Comfort', 'Room Quality'],
        'Food & Dining': ['Food & Dining'],
        'Value': ['Value']
    }

    category_scores = []
    for cat, matched_cats in cat_map.items():
        if not matched_cats:
            category_scores.append({"name": cat, "score": 4.5})
            continue
        rel = [r for r in reviews if r["category"] in matched_cats]
        if rel:
            score = round(sum(r["rating"] for r in rel) / len(rel), 1)
        else:
            score = 4.0
        category_scores.append({"name": cat, "score": score})

    # Issue counts
    issue_counts = {}
    for r in reviews:
        for iss in r.get("issues", []):
            issue_counts[iss] = issue_counts.get(iss, 0) + 1

    return {
        "overall_rating": overall_rating,
        "total_reviews": total,
        "sent_count": sent_count,
        "response_rate": response_rate,
        "sentiment_counts": {
            "positive": pos,
            "neutral": neu,
            "negative": neg
        },
        "star_breakdown": breakdown,
        "category_scores": category_scores,
        "average_sentiment_score": avg_score,
        "issue_counts": issue_counts
    }
