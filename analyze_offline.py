import asyncio
import os
from ai_logic import AIEngine

async def analyze_offline(username: str, filename: str):
    ai = AIEngine()
    
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return

    print(f"Reading replies from {filename}...")
    with open(filename, "r") as f:
        content = f.read()
    
    # Split by the separator used in the export script
    replies = [r.split(". ", 1)[-1].strip() for r in content.split("\n---\n") if r.strip()]
    
    print(f"Analyzing style for @{username} with {len(replies)} samples...")
    portrait = await ai.analyze_style(username, replies)
    
    portrait_file = f"data/{username}_portrait.txt"
    with open(portrait_file, "w") as f:
        f.write(portrait)
    
    print(f"Style portrait updated for @{username}.")
    return portrait

if __name__ == "__main__":
    asyncio.run(analyze_offline("defiunknownking", "data/defiunknownking_sample_replies.txt"))
