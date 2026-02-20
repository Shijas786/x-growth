import asyncio
import os
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from config import Config
from humanizer import Humanizer

class XScraper:
    def __init__(self):
        self.browser_context = None

    async def get_context(self, playwright, headless=False):
        """Get or create a persistent browser context."""
        profile_path = os.path.abspath(Config.BROWSER_PROFILE_PATH)
        if not os.path.exists(profile_path):
            os.makedirs(profile_path)
            
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=headless,
            # Removed channel="chrome" to allow default chromium in Docker/Koyeb
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--disable-blink-features=AutomationControlled"]
        )
        return context

    async def apply_stealth(self, page):
        """Apply stealth to the page."""
        stealth = Stealth()
        # The error suggested apply_stealth_sync, but since we are async, let's see if there is an async one.
        # If not, sync might work if it just adds scripts.
        await stealth.apply_stealth_async(page)

    async def login(self):
        """Navigate to X and wait for the user to be logged in, or inject token."""
        async with async_playwright() as p:
            context = await self.get_context(p, headless=False)
            
            # Inject auth_token if available to bypass login
            if Config.X_AUTH_TOKEN:
                print("Injecting auth_token cookie...")
                await context.add_cookies([{
                    "name": "auth_token",
                    "value": Config.X_AUTH_TOKEN,
                    "domain": ".x.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                    "sameSite": "None"
                }])
            
            page = await context.new_page()
            await self.apply_stealth(page)
            
            await page.goto("https://x.com/home")
            
            # Check if we are already logged in
            try:
                # Wait for any of these selectors that indicate a logged-in state
                await page.wait_for_selector('[data-testid="SideNav_AccountSwitcher_Button"], [data-testid="AppTabBar_Home_Link"]', timeout=10000)
                print("Successfully detected logged-in session.")
            except:
                print("Session not detected.")
                if not Config.X_AUTH_TOKEN:
                    print("No auth_token provided. Please add it to your .env file.")
                else:
                    print("The provided auth_token might be expired or invalid.")
            
            await context.close()

    async def fetch_replies(self, username: str, limit: int = 100):
        """Fetch 'limit' number of replies from a specific user profile."""
        replies = []
        async with async_playwright() as p:
            # Running in headful mode to debug session issues
            context = await self.get_context(p, headless=False)
            
            # Inject auth_token if available
            if Config.X_AUTH_TOKEN:
                await context.add_cookies([{
                    "name": "auth_token",
                    "value": Config.X_AUTH_TOKEN,
                    "domain": ".x.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                    "sameSite": "None"
                }])
            
            page = await context.new_page()
            await self.apply_stealth(page)
            
            url = f"https://x.com/{username}/with_replies"
            print(f"Navigating to {url}...")
            await page.goto(url)
            await Humanizer.wait(2, 4) # Reduced from 5, 7
            
            while len(replies) < limit:
                # Extract tweet containers to verify author
                tweets = await page.query_selector_all('[data-testid="tweet"]')
                before_count = len(replies)
                
                for tweet in tweets:
                    try:
                        # Check if the tweet is by the target user
                        # The user handle is usually in a link or span within the tweet header
                        handle_element = await tweet.query_selector('[data-testid="User-Name"]')
                        if handle_element:
                            handle_text = await handle_element.inner_text()
                            if f"@{username}" in handle_text:
                                snippet = await tweet.query_selector('[data-testid="tweetText"]')
                                if snippet:
                                    text = await snippet.inner_text()
                                    if text not in replies and len(replies) < limit:
                                        if len(text.strip()) > 3:
                                            replies.append(text)
                    except Exception:
                        continue
                
                if len(replies) > before_count:
                    print(f"Collected {len(replies)}/{limit} replies...")

                if len(replies) >= limit:
                    break
                
                # Scroll down
                await Humanizer.natural_scroll(page)
                await Humanizer.wait(0.3, 0.8) # Even faster waits
                
                # Check for blocks
                content = await page.content()
                if "Could not log you in now" in content or "Try again later" in content:
                    print("X blocked the session. Please check the browser window.")
                    break
            
    async def fetch_mirrored_targets(self, target_username: str, limit: int = 5):
        """Find the root tweets that the target influencer has recently replied to."""
        # Force headless=True for production environments where no display is available
        is_headless = os.getenv("HEADLESS", "true").lower() == "true"
        targets = []
        async with async_playwright() as p:
            context = await self.get_context(p, headless=is_headless)
            if Config.X_AUTH_TOKEN:
                await context.add_cookies([{
                    "name": "auth_token",
                    "value": Config.X_AUTH_TOKEN,
                    "domain": ".x.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                    "sameSite": "None"
                }])
            
            page = await context.new_page()
            await self.apply_stealth(page)
            
            url = f"https://x.com/{target_username}/with_replies"
            print(f"Mirroring: Checking @{target_username}'s recent engagement at {url}...")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await Humanizer.wait(5, 8) # Longer wait for cloud
            except Exception as e:
                print(f"Navigation Error: {e}")
                await context.close()
                return targets

            # Check for common "Blocked" or "Login Required" states
            try:
                page_text = await page.inner_text("body", timeout=15000)
            except:
                page_text = ""
                
            has_login_clue = "Log in" in page_text or "Something went wrong" in page_text
            has_home_clue = await page.query_selector('[data-testid="AppTabBar_Home_Link"]')
            
            if not has_home_clue and has_login_clue:
                print("❌ BLOCK DETECTED: X is requesting login or showing an error page.")
                print("Diagnostics: Session cookie might be expired or restricted.")
                await context.close()
                return targets
            
            if not has_home_clue and not tweets_on_start: # Fallback if home link is buried
                # Check for other logged in markers like the tweet button
                if await page.query_selector('[data-testid="SideNav_NewTweet_Button"]'):
                    print("✅ LOGGED IN: Tweet button detected.")
                else:
                    print("⚠️ WARNING: Logged-in state not confirmed. X might be loading or blocked.")
            else:
                print("✅ LOGGED IN: Home navigation detected.")
            
            # We look for conversations where Medusa is the second participant
            # This is complex in X's DOM, so we look for "Replying to @..." text
            # Coverage Optimization: We scan up to 50 tweets to find every new engagement we missed
            found_count = 0
            while len(targets) < limit and found_count < 50: 
                tweets = await page.query_selector_all('[data-testid="tweet"]')
                print(f"Sweep Details: Found {len(tweets)} tweets on page. (Scanned: {found_count})")
                
                if not tweets:
                    print(f"No tweets found. Page Title: '{await page.title()}'")
                    print("Scrolling to load or trigger hydration...")
                    await Humanizer.natural_scroll(page)
                    await Humanizer.wait(3, 6)
                    found_count += 5 
                    continue

                for i, tweet in enumerate(tweets):
                    try:
                        handle_el = await tweet.query_selector('[data-testid="User-Name"]')
                        if handle_el:
                            handle_text = await handle_el.inner_text()
                            print(f"[{i}] Checking tweet by: {handle_text[:40]}...")
                            
                            # If this is Medusa's tweet
                            if f"@{target_username}" in handle_text:
                                # We check if it's a reply by looking for "Replying to" labels
                                # Using a broader inner_text check with timeout protection
                                try:
                                    tweet_raw = await tweet.inner_text(timeout=5000)
                                except:
                                    tweet_raw = ""

                                is_reply = "Replying to @" in tweet_raw
                                    
                                if is_reply:
                                    print(f"-> Detected Medusa Reply. Searching for parent tweet...")
                                    # ROBUST SEARCH: Look backwards from current index for the first NON-MEDUSA tweet
                                    parent_tweet = None
                                    for j in range(i - 1, -1, -1):
                                        potential_parent = tweets[j]
                                        p_handle_el = await potential_parent.query_selector('[data-testid="User-Name"]')
                                        if p_handle_el:
                                            p_handle_text = await p_handle_el.inner_text()
                                            if f"@{target_username}" not in p_handle_text:
                                                parent_tweet = potential_parent
                                                break
                                    
                                    if parent_tweet:
                                        p_handle_text = await (await parent_tweet.query_selector('[data-testid="User-Name"]')).inner_text()
                                        print(f"-> Found potential parent by: {p_handle_text[:30]}")
                                        
                                        # Check if parent is a reply itself
                                        try:
                                            p_raw = await parent_tweet.inner_text(timeout=5000)
                                        except:
                                            p_raw = ""
                                        is_parent_reply = "Replying to @" in p_raw
                                            
                                        # CRITERIA:
                                        # 1. Parent is NOT Medusa
                                        # 2. Parent is NOT a reply/comment (it is a ROOT tweet)
                                        if "@MedusaOnchain" not in p_handle_text and not is_parent_reply:
                                            print(f"SUCCESS: Root target found from @{p_handle_text.split()[-1]}")
                                            parent_author = p_handle_text.split("@")[1].split()[0]
                                            parent_display = p_handle_text.split("@")[0].strip()
                                            
                                            content_el = await parent_tweet.query_selector('[data-testid="tweetText"]')
                                            if content_el:
                                                content = await content_el.inner_text()
                                                
                                                # Extract Tweet URL/ID for targeting and persistence
                                                # We look for the link containing '/status/'
                                                link_el = await parent_tweet.query_selector('a[href*="/status/"]')
                                                tweet_url = ""
                                                if link_el:
                                                    tweet_url = await page.evaluate('(el) => el.href', link_el)
                                                
                                                # Extract Image URL if present
                                                image_el = await parent_tweet.query_selector('[data-testid="tweetPhoto"] img')
                                                image_url = ""
                                                if image_el:
                                                    image_url = await page.evaluate('(el) => el.src', image_el)

                                                # Extract Medusa's actual reply text to "alter" it
                                                medusa_reply_el = await tweet.query_selector('[data-testid="tweetText"]')
                                                medusa_reply = ""
                                                if medusa_reply_el:
                                                    medusa_reply = await medusa_reply_el.inner_text()
                                                
                                                target_data = {
                                                    "author": parent_author,
                                                    "display_name": parent_display,
                                                    "content": content,
                                                    "url": tweet_url,
                                                    "image_url": image_url,
                                                    "medusa_reply": medusa_reply
                                                }
                                                
                                                if target_data["url"] not in [t["url"] for t in targets]:
                                                    targets.append(target_data)
                                                    print(f"MIRROR SUCCESS: Captured @{parent_author} (Medusa said: '{medusa_reply}')")
                                                    if len(targets) >= limit: break
                                            else:
                                                print(f"MIRROR SKIP: @{parent_author}'s post is a sub-comment/thread.")
                    except Exception:
                        continue
                    found_count += 1
                
                if len(targets) >= limit: break
                await Humanizer.natural_scroll(page)
                await Humanizer.wait(1, 2)
                
            await context.close()
        return targets

    async def post_reply(self, tweet_url: str, reply_content: str):
        """Automate the actual posting of a reply using Playwright."""
        # Force headless=True for production
        is_headless = os.getenv("HEADLESS", "true").lower() == "true"
        async with async_playwright() as p:
            context = await self.get_context(p, headless=is_headless)
            if Config.X_AUTH_TOKEN:
                await context.add_cookies([{
                    "name": "auth_token",
                    "value": Config.X_AUTH_TOKEN,
                    "domain": ".x.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                    "sameSite": "None"
                }])
            
            page = await context.new_page()
            await self.apply_stealth(page)
            
            print(f"Navigating to tweet: {tweet_url}")
            await page.goto(tweet_url)
            await Humanizer.wait(3, 5)
            
            # 1. Click the reply box
            print("Clicking reply box...")
            reply_box = await page.query_selector('[data-testid="tweetTextarea_0"]')
            if not reply_box:
                # Some tweets might require clicking the "Reply" indicator first
                indicator = await page.query_selector('[data-testid="reply"]')
                if indicator:
                    await indicator.click()
                    await Humanizer.wait(1, 2)
                    reply_box = await page.query_selector('[data-testid="tweetTextarea_0"]')
            
            if reply_box:
                # 2. Type content human-like
                print(f"Typing reply: {reply_content[:50]}...")
                for char in reply_content:
                    await reply_box.type(char, delay=random.randint(50, 150))
                
                await Humanizer.wait(1, 2)
                
                # 3. Click Post
                post_btn = await page.query_selector('[data-testid="tweetButtonInline"]')
                if post_btn:
                    print("Sending tweet...")
                    await post_btn.click() # LIVE: Now enabled
                    await Humanizer.wait(2, 4)
                else:
                    print("Could not find Post button.")
            else:
                print("Could not find reply box.")
                
            await context.close()
        return True
