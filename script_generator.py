import os
import json
import time
from openai import OpenAI # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()

def generate_script_and_prompts(topic):
    """Generates the script text and visual keywords using an LLM."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing from .env")
        
    # Handle Google Gemini Native API via OpenAI Compatibility
    if api_key.startswith("AIza"):
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        models_to_try = [
            "gemini-1.5-flash", 
            "gemini-2.0-flash"
        ]
        use_json_mode = False # Gemini OpenAI relay often fails with response_format
    # Handle OpenRouter
    elif api_key.startswith("sk-or-v1"):
        base_url = "https://openrouter.ai/api/v1"
        models_to_try = [
            "google/gemini-2.0-flash-lite-preview-02-05:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemma-3-12b-it:free",
            "openrouter/free"
        ]
        use_json_mode = True
    # Handle Native OpenAI
    else:
        base_url = None
        models_to_try = ["gpt-4o-mini"]
        use_json_mode = True

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    prompt = f"""
Write a highly engaging, fast-paced YouTube Shorts script (approx 45-60 seconds, ~130 words) about: {topic}.

MUST FOLLOW THIS FORMULA FOR VIRALITY:
1. Hook (First 3 Seconds): Start with a controversial statement, an impossible question, or a strong emotional trigger to stop the scroll immediately.
2. Story/Value (Next 30 seconds): Deliver fast, punchy value. Use "You" or "Your" to make it personal. No fluff. 
3. Climax/Retention (Last 10 seconds): End with a strong payoff, cliffhanger, or direct call to action (e.g. subscribe).

Return a raw JSON object with ONE key: "scenes".
"scenes" should be a list of objects. Each object represents a fast visual change in the video and must have:
1. "text": The spoken text for this scene (limit to EXACTLY 1 sentence). Do NOT include stage directions.
2. "keyword": ONE highly-searchable, concrete, physical visual noun for stock footage (e.g. "cash", "office desk", "city traffic", "gym weights"). DO NOT use abstract words like "success", "future", "business", or "competition" because stock video search engines fail at those. Must be tangible.

Make sure the entire script is covered sequentially across the scenes (around 6-10 scenes total for extremely fast pacing).
Reply ONLY with valid, parsable JSON. No conversational text.
"""

    for model in models_to_try:
        try:
            print(f"  -> Attempting with AI model: {model}...")
            
            call_kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            if use_json_mode:
                call_kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**call_kwargs)
            
            message = response.choices[0].message
            if not message.content:
                print(f"  -> [Warning] {model} returned empty response. Trying next model...")
                continue
                
            content = message.content.strip()
            
            try:
                # Robustly extract JSON block by finding first '{' and last '}'
                json_start = content.find('{')
                json_end = content.rfind('}')
                
                if json_start != -1 and json_end != -1:
                    content = content[json_start:json_end+1]
                    
                data = json.loads(content)
                
                # Verify scenes key exists
                if "scenes" in data and isinstance(data["scenes"], list):
                    return data["scenes"]
                elif "script" in data:
                    print(f"  -> [Warning] {model} used old format. Recovering...")
                    keyword = data.get("keywords", ["city"])[0] if data.get("keywords") else "city"
                    return [{"text": data["script"], "keyword": keyword}]
                else:
                    print(f"  -> [Warning] {model} missed required JSON keys.")
                    continue
            except Exception as parse_e:
                print(f"  -> [Warning] {model} returned invalid JSON structure: {str(parse_e)}. Trying next...")
                # print(f"Raw output was: {content[:100]}...")
                continue
                
        except Exception as e:
            print(f"  -> [Warning] {model} failed due to API limits/errors. Retrying...")
            time.sleep(1) 
            continue

    print(f"\n[CRITICAL ERROR] All AI models failed. Please check your API key or network connection.")
    return []

if __name__ == "__main__":
    print("Testing Script Generator...")
    scenes = generate_script_and_prompts("3 Money traps to avoid in 2026")
    print("\n[SCENES]:\n", json.dumps(scenes, indent=2))
