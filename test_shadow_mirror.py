
import asyncio
from ai_logic import AIEngine
import os

async def test_mirror():
    ai = AIEngine()
    
    # Mocking the Medusa portrait
    with open("data/MedusaOnchain_portrait.txt", "r") as f:
        portrait = f.read()
    
    test_cases = [
        {"medusa": "one punch monke", "expected": "2-5 words, similar vibe"},
        {"medusa": "noice work fren", "expected": "2-5 words, slang-heavy"},
        {"medusa": "gm moon soon", "expected": "2-5 words, altered gm"},
        {"medusa": "xeet it harder", "expected": "2-5 words, aggressive slang"}
    ]
    
    print("\n--- SHADOW MIRROR TEST ---")
    for case in test_cases:
        reply = await ai.generate_reply(
            portrait, 
            case["medusa"], # We pass her reply here
            recipient_name="Arafat"
        )
        print(f"MEDUSA SAID: {case['medusa']}")
        print(f"BOT ALTERED: {reply}")
        print(f"LENGTH: {len(reply.split())} words\n")

if __name__ == "__main__":
    asyncio.run(test_mirror())
