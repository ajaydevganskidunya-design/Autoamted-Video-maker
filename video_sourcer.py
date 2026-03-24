import os
import requests
import random
from dotenv import load_dotenv

load_dotenv()

def get_stock_video(keyword, output_filename):
    """Searches Pexels for a keyword and downloads a random HD portrait video."""
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise ValueError("PEXELS_API_KEY is missing from .env")
        
    # Search for portrait HD videos
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=10&orientation=portrait"
    
    headers = {
        "Authorization": api_key
    }
    
    print(f"Searching Pexels for '{keyword}'...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Pexels API Error: {response.text}")
        return None
        
    data = response.json()
    videos = data.get("videos", [])
    
    if not videos:
        print(f"No videos found for keyword '{keyword}'. Trying fallback 'city' or 'business'")
        if keyword not in ["city", "business", "abstract"]:
            return get_stock_video("business", output_filename)
        return None
        
    # Pick a random video from top results
    video = random.choice(videos)
    video_files = video.get("video_files", [])
    
    # Prioritize 1080x1920 (TikTok/Shorts size) or close to it
    files_sorted_by_height = sorted(video_files, key=lambda x: x.get("height", 0), reverse=True)
    
    if not files_sorted_by_height:
        print("No playable files found for video.")
        return None
        
    download_url = files_sorted_by_height[0]["link"]
    
    print(f"Downloading video '{keyword}' from Pexels...")
    vid_response = requests.get(download_url, stream=True)
    if vid_response.status_code == 200:
        with open(output_filename, 'wb') as f:
            for chunk in vid_response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
        return output_filename
    else:
        print("Failed to download video file.")
        return None

if __name__ == "__main__":
    print("Testing Video Sourcer...")
    get_stock_video("money", "test_stock.mp4")
