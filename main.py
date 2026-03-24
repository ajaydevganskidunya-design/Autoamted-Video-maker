import os
import sys
from script_generator import generate_script_and_prompts # type: ignore
from audio_generator import generate_audio # type: ignore
from video_sourcer import get_stock_video # type: ignore
from video_renderer import render_final_video # type: ignore

def main():
    # Force utf-8 encoding for Windows console resolving emoji print errors
    sys.stdout.reconfigure(encoding='utf-8') # type: ignore
    
    print("====================================")
    print("🤖 YOUTUBE AUTOMATION SYSTEM v1.0")
    print("====================================\n")
    
    # 1. Get Topic
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:]) # type: ignore
        print(f"Using topic from arguments: {topic}")
    else:
        topic = input("Enter the topic for your YouTube video: ")
    if not topic.strip():
        print("Topic cannot be empty. Exiting.")
        sys.exit(1)
        
    # 2. Generate Script
    print("\n[STEP 1] Generating Script...")
    scenes = generate_script_and_prompts(topic)
    
    if not scenes:
        print("Failed to generate script. Exiting.")
        sys.exit(1)
        
    script = " ".join([scene["text"] for scene in scenes])
    print(f"\n✅ Script generated ({len(script)} characters, {len(scenes)} scenes).")
    
    # 3. Generate Audio
    print("\n[STEP 2] Generating Voiceover...")
    audio_path, timings_path = generate_audio(script, output_filename="temp_voiceover.mp3")
    if not audio_path:
        print("Failed to generate audio. Exiting.")
        sys.exit(1)
        
    # 4. Source Videos (Multiple)
    print(f"\n[STEP 3] Fetching {len(scenes)} Stock Videos for Scenes...")
    
    from moviepy import AudioFileClip # type: ignore
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    audio.close()
    
    total_chars = len(script)
    scene_videos = []
    
    for i, scene in enumerate(scenes): 
        scene_ratio = len(scene["text"]) / max(1, total_chars)
        scene_duration = scene_ratio * total_duration
        
        kw = scene["keyword"]
        vp = get_stock_video(kw, output_filename=f"temp_bg_{i}.mp4")
        if vp:
            scene_videos.append({"path": vp, "duration": scene_duration})
            
    if not scene_videos:
        print("Failed to download any videos. Exiting.")
        sys.exit(1)
        
    # 5. Render Final File
    print("\n[STEP 4] Assembling Final Video With Scene-Synced Clips...")
    import re
    safe_topic = re.sub(r'[^a-zA-Z0-9_\-]', '', topic.replace(' ', '_').lower()[:30]) # type: ignore
    output_filename = f"final_youtube_short_{safe_topic}.mp4"
    
    final_path = render_final_video(scene_videos, audio_path, timings_path, output_filename)
    
    if final_path:
        print("\n====================================")
        print("✨ AUTOMATION COMPLETE ✨")
        print(f"Your multi-clip video is ready: {final_path}")
        print("====================================")
        
        upload_choice = input("\nDo you want to upload this video to YouTube as a Private Short? (y/n): ").strip().lower()
        if upload_choice == 'y':
            from youtube_uploader import upload_video # type: ignore
            
            # Simple description formatting for Shorts
            desc = f"{topic}\n\nGenerated automatically via Python."
            # Extract common tags from keywords
            tags = [s["keyword"] for s in scenes] + ["shorts", "automation"]
            
            upload_video(final_path, title=topic, description=desc, tags=tags)
            
        # Cleanup temp files gracefully on Windows
        import time
        time.sleep(1) 
        try:
            if os.path.exists("temp_voiceover.mp3"): os.remove("temp_voiceover.mp3")
            if os.path.exists("temp_voiceover.json"): os.remove("temp_voiceover.json")
            for i in range(10):
                if os.path.exists(f"temp_bg_{i}.mp4"): os.remove(f"temp_bg_{i}.mp4")
        except PermissionError:
            pass
    else:
        print("Failed to render final video.")

if __name__ == "__main__":
    main()
