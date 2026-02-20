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
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] --- New Sweep Started ---")
        # 1. Mirror Medusa's lead (follow who she is replying to)
        print(f"Mirroring: Checking @MedusaOnchain's recent engagement...")
        try:
            targets = await scraper.fetch_mirrored_targets("MedusaOnchain", limit=15)
            
            if not targets:
                print("No new mirrored targets found in the last 50 tweets. Sleeping for 10m...")
                await asyncio.sleep(600)
                continue
            
            print(f"Found {len(targets)} potential targets. Filtering against Supabase...")
            
            for target in targets:
                tweet_url = target.get("url")
                if not tweet_url or tweet_url in processed_ids:
                    continue

                # Pick a persona (King or Medusa)
                persona = random.choice(personas)
                
                print(f"\n>>> Engaging with @{target['author']} <<<")
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
                print(f"Stealth delay: {delay:.1f}s...")
                await asyncio.sleep(delay)

        except Exception as e:
            print(f"SWEEP ERROR: {e}")
            await asyncio.sleep(300)

        # LONG DELAY: Human Phone Pacing
        dice = random.random()
        if dice < 0.70:
            sweep_delay = random.uniform(600, 1500)
            tag = "STANDARD_CHECK"
        elif dice < 0.90:
            sweep_delay = random.uniform(3600, 10800)
            tag = "LIFE_BREAK"
        else:
            sweep_delay = random.uniform(120, 300)
            tag = "BURST_CHECK"
            
        print(f"[{tag}] Next 'phone check' in {sweep_delay/60:.1f} minutes...")
        await asyncio.sleep(sweep_delay)

if __name__ == "__main__":
    asyncio.run(auto_reply_loop())
