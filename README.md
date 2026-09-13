# Clear Vision — Hospitality Sentiment Repair Agent

An intelligent web-based sentiment analysis and guest experience repair system designed for luxury hotels and hospitality businesses.

---

## 🛠️ Complete Tech Stack

- **Python**: Asynchronous backend using **FastAPI** + **Uvicorn**
- **Selenium**: Automated review scraper with Headless Chrome/Edge driver for Google Maps, TripAdvisor, Yelp, and Booking.com
- **LLM APIs**: Multi-provider AI Sentiment Analysis and 5-stage personalized recovery response generation supporting:
  - **Google Gemini API** (`gemini-1.5-flash` / `gemini-2.5-flash`)
  - **OpenAI API** (`gpt-4o-mini`)
  - **Anthropic Claude API**
  - **Built-in Offline Heuristic NLP Engine** (Works 100% out of the box without any API keys required!)
- **REST APIs**: Full CRUD operations for reviews, AI analysis, response drafting, live scraping, metrics, churn alerts, and hotel profiles
- **WebSockets**: Bi-directional real-time communication channel (`/ws/live`) for live review streaming, scraper progress updates, sentiment alerts, and pipeline logs
- **JavaScript · HTML/CSS**: Responsive luxury hospitality aesthetic with real-time WebSocket connectivity, light/dark mode, and interactive dashboards

---

## 🚀 Quick Start & Running the Backend

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
Create a `.env` file in the project root:
```env
HOST=0.0.0.0
PORT=8000
SELENIUM_HEADLESS=true
GEMINI_API_KEY=your_gemini_api_key_here  # Optional: Fallback NLP works without it
OPENAI_API_KEY=your_openai_api_key_here  # Optional
```

### 3. Launch the Server
```bash
python run_backend.py
```
Or using Uvicorn directly:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running:
- 🌐 **Web Application**: [http://localhost:8000/](http://localhost:8000/)
- 📖 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 📡 **Live WebSocket Stream**: `ws://localhost:8000/ws/live`
- 🩺 **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health, LLM provider status, active review count |
| `GET` | `/api/reviews` | List all reviews (filterable by `sentiment`, `rating`, `platform`) |
| `POST` | `/api/reviews` | Ingest new review, run LLM analysis, draft AI recovery response, broadcast via WebSocket |
| `GET` | `/api/reviews/{id}` | Get review by ID |
| `PUT` | `/api/reviews/{id}` | Update review content or status |
| `DELETE` | `/api/reviews/{id}` | Remove review from database |
| `POST` | `/api/reviews/{id}/respond` | Draft or regenerate custom AI response |
| `POST` | `/api/reviews/{id}/send` | Dispatch response to guest and log to activity timeline |
| `POST` | `/api/analyze` | Direct sentiment analysis endpoint for arbitrary review text |
| `POST` | `/api/scrape` | Trigger asynchronous Selenium review scraper for a hotel URL or platform |
| `GET` | `/api/stats` | Dashboard statistics, sentiment breakdown, and category scores |
| `GET` | `/api/activity` | Recent agent activity timeline logs |
| `GET` | `/api/churn-alerts` | Predictive churn radar and at-risk guest escalations |
| `GET` | `/api/staff` | Staff performance tracker (praise vs. complaint ratio) |
| `GET` | `/api/competitors` | Competitor benchmarking rankings and market gap insights |
| `GET` / `PUT` | `/api/hotel` | View and edit hotel profile metadata |

---

## 🧪 Testing

Run the automated test suite:
```bash
python tests/test_backend.py
python tests/test_scraper.py
```
