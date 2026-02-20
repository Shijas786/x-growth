import asyncio
import random
from scraper import XScraper
from ai_logic import AIEngine
from config import Config
from datetime import datetime
import time
import os

def load_processed_ids():
    processed_urls = set()
    if os.path.exists("data/processed_ids.txt"):
        with open("data/processed_ids.txt", "r") as f:
            for line in f:
                parts = line.strip().split(" | ", 1)
                if len(parts) == 2:
                    processed_urls.add(parts[1])
                else:
                    processed_urls.add(parts[0])
    return processed_urls

def save_processed_id(tweet_url):
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("data/processed_ids.txt", "a") as f:
        f.write(f"{today} | {tweet_url}\n")

async def auto_reply_loop():
    scraper = XScraper()
    ai = AIEngine()
    processed_ids = load_processed_ids()
    
    # Load personas
    try:
        with open("data/MedusaOnchain_portrait.txt", "r") as f:
            medusa_persona = f.read()
        with open("data/defiunknownking_portrait.txt", "r") as f:
            king_persona = f.read()
    except FileNotFoundError:
        print("Persona files not found. Please run training first.")
        return

    personas = [
        {"name": "MedusaOnchain", "portrait": medusa_persona},
        {"name": "defiunknownking", "portrait": king_persona}
    ]

    print("Starting Target-Mirroring Automation Loop...")
    
    while True:
        # 1. Mirror Medusa's lead (follow who she is replying to)
        # We increase the limit to 15 to catch up on everything she did while we were away
        targets = await scraper.fetch_mirrored_targets("MedusaOnchain", limit=15)
        
        if not targets:
            print("No mirrored targets found. Sleeping...")
            await asyncio.sleep(600)
            continue
        
        for target in targets:
            tweet_url = target.get("url")
            if not tweet_url or tweet_url in processed_ids:
                continue

            # Pick a persona (King or Medusa)
            persona = random.choice(personas)
            
            print(f"\n--- Engaging with @{target['author']} ---")
            print(f"Post: {target['content'][:100]}...")
            
            # 2. Generate reply by "altering" Medusa's original response
            reply = await ai.generate_reply(
                persona['portrait'], 
                target.get('medusa_reply'), # Pass her reply to be altered
                recipient_name=target['display_name'].split()[0],
                image_url=target.get("image_url")
            )
            
            # 3. Execute Reply
            success = await scraper.post_reply(tweet_url, reply)
            if success:
                save_processed_id(tweet_url)
                processed_ids.add(tweet_url)
            
            # Humanized delay between interactions in the same run
            delay = random.uniform(30, 90)
            print(f"Waiting {delay:.1f}s for stealth...")
            await asyncio.sleep(delay)

        # LONG DELAY: Human Phone Pacing
        # We don't check every 10 mins like a robot. 
        # We simulate "checking your phone" at irregular intervals.
        
        dice = random.random()
        if dice < 0.70:
            # 70% chance: Standard check (10-25 mins)
            sweep_delay = random.uniform(600, 1500)
            tag = "STANDARD_CHECK"
        elif dice < 0.90:
            # 20% chance: Life happens (1-3 hours break)
            sweep_delay = random.uniform(3600, 10800)
            tag = "LIFE_BREAK"
        else:
            # 10% chance: Doomscrolling/Hooked (2-5 mins)
            sweep_delay = random.uniform(120, 300)
            tag = "BURST_CHECK"
            
        print(f"[{tag}] Check complete. Next 'phone check' in {sweep_delay/60:.1f} minutes...")
        await asyncio.sleep(sweep_delay)

if __name__ == "__main__":
    asyncio.run(auto_reply_loop())
