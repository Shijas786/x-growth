import asyncio
import os
import json
from scraper import XScraper
from ai_logic import AIEngine
from config import Config
from humanizer import Humanizer

async def setup_persona():
    """Fetch replies and create style portraits for influencers."""
    scraper = XScraper()
    ai = AIEngine()
    
    portraits = {}
    
    for influencer in Config.TARGET_INFLUENCERS:
        portrait_file = f"data/{influencer}_portrait.txt"
        
        if os.path.exists(portrait_file):
            print(f"Loading existing portrait for @{influencer}...")
            with open(portrait_file, "r") as f:
                portraits[influencer] = f.read()
            continue

        print(f"Fetching 100 replies for @{influencer}...")
        replies = await scraper.fetch_replies(influencer, limit=100)
        
        if not replies:
            print(f"No replies found for @{influencer}. Check if the profile is public.")
            continue
            
        print(f"Analyzing style for @{influencer}...")
        portrait = await ai.analyze_style(influencer, replies)
        
        with open(portrait_file, "w") as f:
            f.write(portrait)
        
        portraits[influencer] = portrait
        print(f"Style portrait created for @{influencer}.")
        
    return portraits

async def main():
    # 1. Initialize
    if not os.path.exists("data"):
        os.makedirs("data")
    
    scraper = XScraper()
    
    # 2. Login Flow (Interactive if first time)
    print("Initializing X Login...")
    await scraper.login()
    
    # 3. Setup Persona
    portraits = await setup_persona()
    
    if not portraits:
        print("No personas could be trained. Exiting.")
        return

    print("\n--- Setup Complete ---")
    print("Personas trained:", list(portraits.keys()))
    print("Automation loop ready. In a real scenario, we would now scan for trending posts and reply.")
    print("For now, the system is ready for testing.")

if __name__ == "__main__":
    asyncio.run(main())
