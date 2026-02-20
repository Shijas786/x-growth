import os
import json
from openai import OpenAI
from config import Config

class AIEngine:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    async def analyze_style(self, influencer_name: str, replies: list):
        """Analyze a list of replies to create a deep Style Portrait."""
        # Use more samples for deeper analysis
        selected_replies = replies[:200] 
        replies_text = "\n---\n".join(selected_replies)

        prompt = f"""
        TASK: DEEP STYLE EXTRACTION
        Target User: @{influencer_name}
        
        Analyze the provided 200+ replies to build a "DNA-level" copycat profile. 
        Focus intensely on:
        
        1. ENGLISH SLANG & VERNACULAR: 
           - List specific slang they use (e.g., 'gm', 'vibe coding', 'tho', 'fr').
           - Note their unique words for common things (e.g., calling tweets 'xeets').
        
        2. SENTENCE RHYTHM & FLOW:
           - Is it staccato? Deeply conversational? 
           - Do they use lists? (Notice if they use '+' or '>' symbols).
           - Do they start sentences with lowercase?
        
        3. EMOTIONAL VIBE:
           - Are they supportive ("gm frens"), skeptical, or "insider" focused?
        
        4. COPYCAT INSTRUCTIONS:
           - Provide 3 strict rules a ghostwriter must follow to pass as this person.
        
        DATA:
        {replies_text}
        
        Return the result as a structured 'Persona Manual'.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a master psychological profile builder and expert linguistic ghostwriter."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    async def generate_reply(self, style_portrait: str, post_content: str, recipient_name: str = None, image_url: str = None):
        """Generate a signature reply based on the persona manual. Supports Vision."""
        mention_instruction = f"If appropriate, address them by their name/handle: {recipient_name}." if recipient_name else ""
        vision_instruction = "The user has attached an image." if image_url else ""
        mirror_instruction = f"MEDUSA SAID: '{post_content}' - YOUR JOB IS TO ALTER THIS SLIGHTLY BUT KEEP THE SAME VIBE." if post_content else ""

        prompt = f"""
        ACT AS THE PERSON DESCRIBED IN THIS PERSONA MANUAL.
        
        PERSONA MANUAL:
        {style_portrait}
        
        {mirror_instruction}
        
        {mention_instruction}
        {vision_instruction}
        
        STRICT EXECUTION RULES:
        1. SHADOW MIRRORING: If MEDUSA SAID is provided, alter it slightly (synonyms, different slang).
        2. EXTREME BREVITY: STRICTLY 2-5 WORDS. 
        3. LAZY VIBE: Lowercase only. No punctuation.
        4. MIMIC SLANG: Use 'noice', 'frens', 'xeet', 'gm', 'moni'.
        
        GENERATE 2-5 WORD REACTION:
        """
        
        # Prepare messages for GPT-4o (Vision ready)
        content_payload = [{"type": "text", "text": prompt}]
        if image_url:
            content_payload.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are now a precise persona mimic with vision capabilities. You do not just reply; you BECOME the person."},
                {"role": "user", "content": content_payload}
            ]
        )
        return response.choices[0].message.content.strip().replace('"', '')

    async def evaluate_target(self, post_content: str, author_handle: str):
        """Use AI to decide if a target is high-quality for engagement and is a person."""
        prompt = f"""
        TASK: EVALUATE TARGET QUALITY & IDENTITY
        Evaluate if this is a high-quality engagement lead and if the author is a PERSON.
        
        CRITERIA:
        1. IDENTITY: Is the author a human/person/influencer? (Reject brands, products, companies, or bots).
        2. RELEVANCE: Is the post content about Crypto, AI, Tech, or Growth? (High priority)
        3. NOISE: Is it a bot-heavy spam thread or a low-value 'gm' post? (Reject noise)
        4. ENGAGEMENT: Does the post look like it has room for professional insight?
        
        POST CONTENT (from @{author_handle}):
        "{post_content}"
        
        RETURN JSON ONLY:
        {{
            "score": 0.0 to 1.0 (float),
            "is_person": true/false,
            "decision": "ACCEPT" or "REJECT",
            "reason": "short reason"
        }}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a social media strategist analyzing high-value engagement leads. You target humans, not brands."},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content)
