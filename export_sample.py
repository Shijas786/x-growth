import asyncio
from scraper import XScraper
from config import Config

async def export_replies(username: str, limit: int = 100):
    scraper = XScraper()
    print(f"Fetching {limit} replies for display...")
    replies = await scraper.fetch_replies(username, limit=limit)
    
    with open(f"data/{username}_sample_replies.txt", "w") as f:
        for i, r in enumerate(replies, 1):
            f.write(f"{i}. {r}\n---\n")
    print("Done.")

if __name__ == "__main__":
    asyncio.run(export_replies("defiunknownking", 100))
