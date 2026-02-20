import asyncio
import random
import time

class Humanizer:
    @staticmethod
    async def wait(min_seconds: float, max_seconds: float):
        """Wait for a random amount of time between min and max."""
        wait_time = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(wait_time)

    @staticmethod
    async def type_human_like(element, text: str):
        """Type text into an element with variable speeds and occasional mistakes."""
        for char in text:
            await element.type(char, delay=random.randint(50, 150))
            if random.random() < 0.05:  # 5% chance of a slight additional delay
                await asyncio.sleep(random.uniform(0.1, 0.3))

    @staticmethod
    async def natural_scroll(page):
        """Perform a natural-looking scroll on the page."""
        scroll_amount = random.randint(300, 700)
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(random.uniform(0.5, 1.5))

    @staticmethod
    def jitter_time(seconds: float, percentage: float = 0.1):
        """Add jitter to a fixed time value."""
        jitter = seconds * percentage
        return seconds + random.uniform(-jitter, jitter)
