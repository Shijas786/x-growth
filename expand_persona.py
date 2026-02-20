import asyncio
import os
from scraper import XScraper
from ai_logic import AIEngine
from config import Config

async def expand_persona(username: str, extra_limit: int = 100):
    scraper = XScraper()
    ai = AIEngine()
    
    print(f"Fetching {extra_limit} additional replies for @{username}...")
    # Increase the limit to get more depth
    replies = await scraper.fetch_replies(username, limit=100 + extra_limit)
    
    if not replies:
        print(f"No replies found for @{username}.")
        return

    print(f"Saving raw replies to data/{username}_raw_replies.txt...")
    raw_file = f"data/{username}_raw_replies.txt"
    with open(raw_file, "w") as f:
        for r in replies:
            f.write(r.replace("\n", " ") + "\n---\n")

    print(f"Re-analyzing style for @{username} with {len(replies)} total samples...")
    portrait = await ai.analyze_style(username, replies)
    
    portrait_file = f"data/{username}_portrait.txt"
    with open(portrait_file, "w") as f:
        f.write(portrait)
    
    print(f"Style portrait updated for @{username}.")
    return portrait

async def main():
    # Fetch 500 total replies for Medusa
    await expand_persona("MedusaOnchain", extra_limit=400)

if __name__ == "__main__":
    asyncio.run(main())
