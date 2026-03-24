import os
import requests # type: ignore
import base64
import json
from dotenv import load_dotenv  # type: ignore

load_dotenv()

def generate_audio(text, output_filename="voiceover.mp3"):
    """Converts text to speech using ElevenLabs API and saves as MP3."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is missing from .env")
        
    # Popular male voice ID (Adam). Change this if you want a different voice.
    voice_id = "pNInz6obpgDQGcFmaJgB" 
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.75
        }
    }
    
    print("Generating audio via ElevenLabs...")
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        response_json = response.json()
        audio_bytes = base64.b64decode(response_json["audio_base64"])
        
        with open(output_filename, 'wb') as f:
            f.write(audio_bytes)
            
        # Parse characters into words
        alignment = response_json.get('alignment', {})
        chars = alignment.get('characters', [])
        starts = alignment.get('character_start_times_seconds', [])
        ends = alignment.get('character_end_times_seconds', [])
        
        words = []
        current_word = ""
        current_start = -1
        
        for i, char in enumerate(chars):
            if char == ' ':
                if current_word:
                    words.append({"word": current_word, "start": current_start, "end": ends[i-1]})
                    current_word = ""
                    current_start = -1
            else:
                if current_start == -1:
                    current_start = starts[i] if len(starts) > i else 0
                current_word += char
                
        # Append the last word if exists
        if current_word and chars:
             words.append({"word": current_word, "start": current_start, "end": ends[-1]})
             
        # Save words timeline to a json file
        json_file = output_filename.replace('.mp3', '.json')
        with open(json_file, 'w') as f:
             json.dump(words, f)
             
        print(f"Audio saved to {output_filename}")
        print(f"Timestamps saved to {json_file}")
        return output_filename, json_file
    else:
        print(f"Error from ElevenLabs: {response.text}")
        return None, None

if __name__ == "__main__":
    print("Testing Audio Generator...")
    generate_audio("Welcome to the first automated finance video. Let's make some money.")
