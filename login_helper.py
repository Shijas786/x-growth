import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from config import Config

async def main():
    profile_path = os.path.abspath(Config.BROWSER_PROFILE_PATH)
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
    
    print(f"Opening browser using profile: {profile_path}")
    print("Please log in manually in the browser window.")
    
    async with async_playwright() as p:
        # Use 'chrome' channel to use the actual Chrome browser which has higher trust
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                headless=False,
                channel="chrome",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        except Exception as e:
            print(f"Could not launch Chrome channel: {e}. Falling back to default chromium.")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                headless=False,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
        page = await context.new_page()
        # Removing stealth and extra args to see if a cleaner launch avoids 'bot' detection
        
        await page.goto("https://x.com")
        
        print("\n--- INSTRUCTIONS ---")
        print("1. Log in to X manually.")
        print("2. Once you are on the home page and logged in, come back here.")
        print("3. Keep this terminal open until you are done.")
        print("4. Close the browser window once you are logged in to save the session.")
        
        # Wait for the browser to close or for the user to signal completion
        while True:
            await asyncio.sleep(1)
            if page.is_closed():
                break
        
        await context.close()
        print("\nSession saved. You can now run the automation script.")

if __name__ == "__main__":
    asyncio.run(main())
