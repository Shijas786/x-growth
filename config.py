import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
    X_USERNAME = os.getenv("X_USERNAME")
    X_PASSWORD = os.getenv("X_PASSWORD")
    X_EMAIL = os.getenv("X_EMAIL")
    BROWSER_PROFILE_PATH = os.getenv("BROWSER_PROFILE_PATH", "./profile")
    
    # Supabase (for persistent state on free-tier hosting)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Target Influencers
    TARGET_INFLUENCERS = [
        "defiunknownking",
        "MedusaOnchain"
    ]
    
    # Daily limits
    DAILY_REPLY_LIMIT = 20
    MIN_WAIT_BETWEEN_REPLIES = 300  # 5 minutes
    MAX_WAIT_BETWEEN_REPLIES = 900  # 15 minutes
