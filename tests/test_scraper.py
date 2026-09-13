import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.scrapers.selenium_scraper import selenium_scraper

async def test_scraper():
    print("[TEST] Running Selenium Scraper test...")
    
    logs_received = []
    async def log_callback(job_id, msg, level, progress):
        print(f"[{progress}%] [{level.upper()}] {msg}")
        logs_received.append(msg)

    reviews = await selenium_scraper.scrape_reviews_live(
        target_url=None,
        hotel_name="The Grand ClearVision",
        platform="Google",
        max_reviews=3,
        progress_callback=log_callback
    )

    print(f"[TEST] Extracted {len(reviews)} reviews:")
    for r in reviews:
        print(f" - [{r['rating']}*] {r['name']} ({r['platform']}): {r['text'][:60]}...")

    assert len(reviews) == 3, f"Expected 3 reviews, got {len(reviews)}"
    assert len(logs_received) >= 4, "Expected progress logs"
    print("\n[SUCCESS] SELENIUM SCRAPER TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_scraper())
