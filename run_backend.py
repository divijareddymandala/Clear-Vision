import os
import sys
import uvicorn
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import settings

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("=" * 68)
    print("  [CLEAR VISION] HOSPITALITY SENTIMENT REPAIR AGENT BACKEND")
    print("=" * 68)
    print(f"  * Host:                 {settings.HOST}")
    print(f"  * Port:                 {settings.PORT}")
    print(f"  * REST API Endpoint:    http://localhost:{settings.PORT}/api")
    print(f"  * Interactive API Docs: http://localhost:{settings.PORT}/docs")
    print(f"  * WebSocket Stream:     ws://localhost:{settings.PORT}/ws/live")
    print(f"  * Web App UI:           http://localhost:{settings.PORT}/")
    print(f"  * LLM Engine:           {settings.LLM_PROVIDER} ({settings.LLM_MODEL})")
    print(f"  * Headless Scraper:     Selenium Chrome/Edge (Headless={settings.SELENIUM_HEADLESS})")
    print("=" * 68)
    print("Starting Uvicorn asynchronous server...\n")

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    main()
