# Clear Vision — Hospitality Sentiment Repair Agent

An intelligent web-based sentiment analysis and guest experience repair system designed for luxury hotels and hospitality businesses.

---

## 🛠️ Tech Stack

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

## 💻 Local Run Instructions

You can run **Clear Vision** locally in either **Full-Stack Mode** (FastAPI backend + Selenium + WebSockets + Frontend) or **Standalone Client Mode** (instant browser preview).

---

### Method 1: Full-Stack Mode (Recommended)

This runs the complete Python FastAPI server, live WebSocket broadcast channel, Selenium review scraper, and SQLite database while serving the frontend.

#### 1. Prerequisites
- **Python 3.10, 3.11, 3.12, or 3.13** installed ([python.org](https://www.python.org/downloads/))
- **Google Chrome** or **Microsoft Edge** (for the Selenium headless scraper)
- **Git**

#### 2. Clone the Repository
```bash
git clone https://github.com/divijareddymandala/Clear-Vision.git
cd Clear-Vision
```

#### 3. Create & Activate a Virtual Environment (Optional but Recommended)
- **On Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **On macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 5. Configure Environment Variables (Optional)
The backend is equipped with an intelligent built-in NLP engine that works **100% offline out-of-the-box without API keys**. If you wish to connect frontier LLMs (Gemini or OpenAI), create a `.env` file in the project root:
```env
HOST=0.0.0.0
PORT=8000
SELENIUM_HEADLESS=true
GEMINI_API_KEY=your_gemini_api_key_here    # Optional: for Gemini models
OPENAI_API_KEY=your_openai_api_key_here    # Optional: for OpenAI models
```

#### 6. Run the Application
Start the server using the launcher script:
```bash
python run_backend.py
```
*Or with Uvicorn directly:*
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 7. Open in Your Browser
- 🌐 **Web App UI**: [http://localhost:8000/](http://localhost:8000/)
- 📖 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 📡 **WebSocket Endpoint**: `ws://localhost:8000/ws/live`
- 🩺 **Health Status**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

When the web page opens, verify the top navigation bar displays:
`⚡ Backend: Connected (REST + WebSocket)`

---

### Method 2: Standalone Client Mode (Zero Installation)

If you just want to quickly explore the UI and client-side simulation without starting Python:
1. Double-click or open `index.html` in any modern web browser (Chrome, Edge, Firefox, Safari).
2. The frontend will automatically detect that the local backend is offline and switch into **Client Demo Mode** seamlessly.

---

## ⚡ How to Test the Live Features Locally

### 1. Test Live Selenium Scraper
1. Open [http://localhost:8000/](http://localhost:8000/).
2. Navigate to the **Demo** page from the sidebar menu.
3. In the **"Live Selenium Scraper & Real-Time Ingestion"** card, select a platform (e.g. *Google Maps*, *TripAdvisor*, or *Booking.com*) and review count (e.g. *5 Reviews*).
4. Click **"🕷️ Run Scraper"**.
5. Watch the terminal below stream the 5 execution phases live via WebSockets.
6. Once complete, switch to the **Monitor** page — the newly harvested reviews will appear immediately at the top of the feed!

### 2. Submit a Custom Review via REST & LLM Analysis
1. Open the **Submit Review** page.
2. Enter a guest name, choose a star rating (e.g., 1★), select an issue category, and paste a review.
3. Click **"🚀 Analyze & Add to Feed"**.
4. The review is sent via `POST /api/reviews`, analyzed by the AI engine, assigned a sentiment score (0–100), checked for churn probability, and auto-populated with a 5-stage personalized service recovery response.

### 3. Run Automated Tests
Verify all endpoints and components using the test scripts:
```bash
# Test REST APIs, SQLite DB, LLM Service, and WebSockets
python tests/test_backend.py

# Test Headless Selenium Scraper
python tests/test_scraper.py
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend status, active LLM model, connected WebSocket count |
| `GET` | `/api/reviews` | List all reviews (filterable by `sentiment`, `rating`, `platform`) |
| `POST` | `/api/reviews` | Submit new review, run AI analysis, draft recovery response, broadcast live |
| `GET` | `/api/reviews/{id}` | Retrieve review details by ID |
| `PUT` | `/api/reviews/{id}` | Update review content or status |
| `DELETE` | `/api/reviews/{id}` | Delete review from database |
| `POST` | `/api/reviews/{id}/respond` | Draft or customize AI recovery response |
| `POST` | `/api/reviews/{id}/send` | Mark response as sent and log to activity timeline |
| `POST` | `/api/analyze` | Standalone sentiment analysis endpoint |
| `POST` | `/api/scrape` | Trigger asynchronous Selenium review scraper |
| `GET` | `/api/stats` | Dashboard statistics, sentiment breakdown, category scores |
| `GET` | `/api/activity` | Recent activity log entries |
| `GET` | `/api/churn-alerts` | Predictive churn radar & at-risk guest escalations |
| `GET` | `/api/staff` | Staff performance tracker (praise vs. complaint ratio) |
| `GET` | `/api/competitors` | Competitor benchmarking rankings & market gap insights |
| `GET` / `PUT` | `/api/hotel` | View and update hotel profile metadata |

---

## 🔧 Troubleshooting

- **Port 8000 already in use:**
  Specify another port using `PORT=8080 python run_backend.py` or `uvicorn backend.main:app --port 8080`.
- **Chrome / ChromeDriver:**
  Selenium automatically uses the system Chrome or Edge browser installed on your machine.
- **PowerShell Execution Policy:**
  If script execution is disabled when activating the virtual environment, run:
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
