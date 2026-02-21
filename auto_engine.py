import asyncio
import random
from scraper import XScraper
from playwright.async_api import async_playwright
from ai_logic import AIEngine
from supabase import create_client, Client
from config import Config
from datetime import datetime
import time
import os
import threading
import http.server
import socketserver
import gc

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

    print("--- Starting SINGLE-SESSION Feed Engagement ---")
    print("Limit: Max 10 replies per hour. 512MB RAM Optimization Active.")

    hourly_replies = []

    while True:
        # 1. Check Hourly Limit
        now = time.time()
        hourly_replies = [r for r in hourly_replies if (now - r[0]) < 3600]
        
        if len(hourly_replies) >= 10:
            wait_time = 3600 - (now - hourly_replies[0][0])
            print(f"Hourly limit (10) reached. Sleeping for {wait_time/60:.1f} minutes...")
            await asyncio.sleep(wait_time)
            continue

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] --- New Single-Session Sweep Started ---")
        
        # 2. Launch Browser ONCE for the whole sweep
        async with async_playwright() as p:
            is_headless = os.getenv("HEADLESS", "true").lower() == "true"
            context = await scraper.get_context(p, headless=is_headless)
            
            if Config.X_AUTH_TOKEN:
                await context.add_cookies([{
                    "name": "auth_token", "value": Config.X_AUTH_TOKEN,
                    "domain": ".x.com", "path": "/", "secure": True,
                    "httpOnly": True, "sameSite": "None"
                }])
            
            page = await context.new_page()
            await scraper.apply_stealth(page)

            try:
                # 3. Fetch Feed Targets using the SHARED page
                feed_targets = await scraper.fetch_home_feed_targets(limit=10, page=page)
                
                if not feed_targets:
                    print("No targets found in this session.")
                else:
                    for target in feed_targets:
                        # Safety checks
                        if len(hourly_replies) >= 10: break
                        tweet_url = target.get("url")
                        if not tweet_url or tweet_url in processed_ids: continue

                        print(f"\nEvaluating: @{target['author']}...")
                        evaluation = await ai.evaluate_target(target['content'], target['author'])
                        
                        if evaluation.get("is_person", False) and evaluation['decision'] == "ACCEPT":
                            print(f"ACCEPTED: {evaluation['reason']}")
                            
                            persona = random.choice(personas)
                            reply = await ai.generate_reply(persona['portrait'], target['content'], recipient_name=target['display_name'].split()[0])
                            
                            print(f">>> Replying as {persona['name']} to @{target['author']} <<<")
                            # 4. Post Reply using the SAME shared page
                            success = await scraper.post_reply(tweet_url, reply, page=page)
                            
                            if success:
                                save_processed_id(tweet_url)
                                processed_ids.add(tweet_url)
                                hourly_replies.append((time.time(), tweet_url))
                                print(f"SUCCESS: Reply posted. ({len(hourly_replies)}/10 this hour)")
                            
                            # Small delay between posts in the same session
                            await Humanizer.wait(30, 60)
                        else:
                            print(f"REJECTED: {evaluation.get('reason', 'Not a person/low quality')}")

            except Exception as e:
                print(f"SESSION ERROR: {e}")
            finally:
                print("Closing browser session to reclaim RAM...")
                await context.close()

        # Final cleanup and long rest
        gc.collect()
        sweep_delay = random.uniform(900, 1800)
        print(f"Resting CPU/RAM. Next check in {sweep_delay/60:.1f} minutes...")
        await asyncio.sleep(sweep_delay)

if __name__ == "__main__":
    asyncio.run(auto_reply_loop())
