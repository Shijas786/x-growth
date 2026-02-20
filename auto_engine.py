import asyncio
import random
from scraper import XScraper
from ai_logic import AIEngine
from supabase import create_client, Client
from config import Config
from datetime import datetime
import time
import os
import threading
import http.server
import socketserver

# Supabase Initialization
supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY) if Config.SUPABASE_URL else None

def run_health_check_server():
    """Starts a dummy server to satisfy Koyeb's TCP health checks."""
    try:
        # Koyeb usually looks for port 8000 or 8080
        port = int(os.getenv("PORT", 8000))
        Handler = http.server.SimpleHTTPRequestHandler
        # Suppress logging to keep the console clean
        class QuietHandler(Handler):
            def log_message(self, format, *args):
                return

        with socketserver.TCPServer(("", port), QuietHandler) as httpd:
            print(f"Health Check Server: Success! Listening on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Health Check Server Error: {e}")

# Start the health check server in a background thread
threading.Thread(target=run_health_check_server, daemon=True).start()

def load_processed_ids():
    """Load IDs from Supabase instead of local file."""
    processed_urls = set()
    if not supabase:
        print("WARNING: Supabase not configured. Using temporary local state.")
        return processed_urls

    try:
        response = supabase.table("processed_ids").select("tweet_url").execute()
        for row in response.data:
            processed_urls.add(row["tweet_url"])
    except Exception as e:
        print(f"Error loading from Supabase: {e}")
    return processed_urls

def save_processed_id(tweet_url):
    """Save ID to Supabase."""
    if not supabase:
        return
    
    try:
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        supabase.table("processed_ids").insert({
            "tweet_url": tweet_url,
            "created_at": today
        }).execute()
    except Exception as e:
        print(f"Error saving to Supabase: {e}")

import gc

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

    print("--- Starting HOME FEED Engagement Strategy ---")
    print("Limit: Max 10 replies per hour. Targeting Persons/Influencers.")

    hourly_replies = [] # Track (timestamp, url) for the last 60 minutes

    while True:
        # 1. Check Hourly Limit
        now = time.time()
        hourly_replies = [r for r in hourly_replies if (now - r[0]) < 3600]
        
        if len(hourly_replies) >= 10:
            wait_time = 3600 - (now - hourly_replies[0][0])
            print(f"Hourly limit (10) reached. Sleeping for {wait_time/60:.1f} minutes...")
            await asyncio.sleep(wait_time)
            continue

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] --- New Feed Sweep Started ---")
        try:
            # 2. Fetch Feed Targets (Reduced limit to save CPU)
            feed_targets = await scraper.fetch_home_feed_targets(limit=10)
            
            if not feed_targets:
                print("No new feed targets found. Waiting 10m...")
                await asyncio.sleep(600)
                continue
            
            for target in feed_targets:
                # Extra check: ensure we haven't hit the limit mid-loop
                if len(hourly_replies) >= 10: break

                tweet_url = target.get("url")
                if not tweet_url or tweet_url in processed_ids:
                    continue

                print(f"\nEvaluating: @{target['author']} | Content: {target['content'][:60]}...")
                
                # 3. AI Evaluation (Identity Check)
                evaluation = await ai.evaluate_target(target['content'], target['author'])
                is_person = evaluation.get("is_person", False)
                
                if not is_person or evaluation['decision'] == "REJECT":
                    print(f"REJECTED: {evaluation['reason']}")
                    continue

                print(f"ACCEPTED: {evaluation['reason']} (Score: {evaluation['score']})")
                
                # 4. Generate & Post Reply
                persona = random.choice(personas)
                reply = await ai.generate_reply(persona['portrait'], target['content'], recipient_name=target['display_name'].split()[0])
                
                print(f">>> Replying as {persona['name']} to @{target['author']} <<<")
                success = await scraper.post_reply(tweet_url, reply)
                
                if success:
                    save_processed_id(tweet_url)
                    processed_ids.add(tweet_url)
                    hourly_replies.append((time.time(), tweet_url))
                    print(f"SUCCESS: Reply posted. ({len(hourly_replies)}/10 this hour)")
                
                # Force cleanup after browser interaction
                gc.collect()

                # Randomized delay between 3-7 minutes (Increased to cool CPU)
                delay = random.uniform(180, 420)
                print(f"Stealth delay: {delay/60:.1f}m...")
                await asyncio.sleep(delay)

        except Exception as e:
            print(f"FEED ERROR: {e}")
            await asyncio.sleep(300)

        # Force final cleanup for the loop
        gc.collect()

        # Randomized sweep interval (Checking every 15-25 mins - Increased for safety)
        sweep_delay = random.uniform(900, 1500)
        print(f"Next 'phone check' in {sweep_delay/60:.1f} minutes...")
        await asyncio.sleep(sweep_delay)

if __name__ == "__main__":
    asyncio.run(auto_reply_loop())
