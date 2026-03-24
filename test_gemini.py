import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

prompt = """
Write a short YouTube script about 3 Money traps.
Return raw JSON with keys "script" and "keywords" (a list of 4 nouns).
"""

response = client.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[{"role": "user", "content": prompt}]
)
print("RAW CONTENT:")
print(repr(response.choices[0].message.content))
