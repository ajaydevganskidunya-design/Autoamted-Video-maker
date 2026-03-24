import os
import json
import numpy as np # type: ignore
import random
from PIL import Image, ImageDraw, ImageFont # type: ignore
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ImageClip, vfx # type: ignore

def create_subtitle_clip(text, start, duration, video_size=(1080, 1920)):
    """Creates a transparent ImageClip with yellow text and black stroke."""
    # Create transparent PIL Image
    img = Image.new('RGBA', video_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a thick font for subtitles
        font = ImageFont.truetype("arialbd.ttf", 100)
    except IOError:
        font = ImageFont.load_default(100) if hasattr(ImageFont, "load_default") else ImageFont.load_default()
        
    # Measure text size
    try:
        bbox = draw.textbbox((0,0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older Pillow
        text_w, text_h = draw.textsize(text, font=font)
        
    # Position (Dead center vertically & horizontally)
    x = (video_size[0] - text_w) / 2
    y = video_size[1] * 0.45 
    
    # Draw black stroke (thicker)
    stroke_color = "black"
    stroke_width = 5
    for dx in range(0 - stroke_width, stroke_width+1, 2):
        for dy in range(0 - stroke_width, stroke_width+1, 2):
             draw.text((x+dx, y+dy), text, font=font, fill=stroke_color)
             
    # Draw text (alternating colors or default yellow)
    # Highlight extremely short words or punctuation ends differently
    fill_color = "yellow" if len(text) > 4 else "white"
    draw.text((x, y), text, font=font, fill=fill_color)
    
    # Convert PIL Image to numpy array
    img_array = np.array(img)
    
    # Create ImageClip
    clip = ImageClip(img_array).with_start(start).with_duration(duration)
    return clip

def render_final_video(scene_videos, audio_path, timings_path, output_path="final_video.mp4"):
    """Combines background videos, TTS audio, and subtitles synchronously."""
    try:
        print(f"Loading assets: {len(scene_videos)} videos, Audio={audio_path}")
        audio = AudioFileClip(audio_path)
        
        clips = []
        for sv in scene_videos:
            vp = sv["path"]
            required_duration = sv["duration"]
            
            # Resize all videos to portrait 1080x1920 and mute them
            c = VideoFileClip(vp).without_audio().with_effects([vfx.Resize(new_size=(1080, 1920))])
            
            # Subcut or loop to match exact scene duration
            if c.duration < required_duration:
                c = c.with_effects([vfx.Loop(duration=required_duration)])
            else:
                c = c.subclipped(0, required_duration)
                
            clips.append(c)
            
        print("Stitching multiple background clips together...")
        bg_video = concatenate_videoclips(clips, method="compose")
        
        # Handle duration mismatch
        if bg_video.duration < audio.duration:
            print("Combined video is shorter than audio. Looping to fit...")
            bg_video = bg_video.with_effects([vfx.Loop(duration=audio.duration)])
        else:
            print("Combined video is longer than audio. Trimming to fit...")
            bg_video = bg_video.subclipped(0, int(audio.duration) + 1)
            
        print("Adding Background Music (if available in 'bgm' folder)...")
        if os.path.exists("bgm") and len(os.listdir("bgm")) > 0:
            bgm_files = [f for f in os.listdir("bgm") if f.endswith(('.mp3', '.wav'))]
            if bgm_files:
                import moviepy.audio.fx.all as afx # type: ignore
                bgm_path = os.path.join("bgm", random.choice(bgm_files))
                bgm = AudioFileClip(bgm_path).with_effects([vfx.Loop(duration=audio.duration), afx.MultiplyVolume(0.1)])
                # Mix voiceover with bgm
                from moviepy.audio.AudioClip import CompositeAudioClip # type: ignore
                final_audio = CompositeAudioClip([audio, bgm])
            else:
                final_audio = audio
        else:
            final_audio = audio
            
        # Set final combined audio
        bg_video = bg_video.with_audio(final_audio)
        
        print("Generating Subtitles from timestamps...")
        subtitle_clips = []
        with open(timings_path, 'r') as f:
            words = json.load(f)
            
        # Group chunks of 2-3 words for readability
        chunk_text = ""
        chunk_start = -1
        chunk_end = -1
        
        for idx, word in enumerate(words):
            if chunk_start == -1:
                chunk_start = word['start']
            
            chunk_text += word['word'] + " "
            chunk_end = word['end']
            
            # Flush chunk if it hits 2 words or ends with punctuation, or is the last word for fast Hormozi style
            if len(chunk_text.split()) >= 2 or word['word'][-1] in ['.', ',', '!', '?'] or idx == len(words) - 1:
                # Add tiny padding to duration to prevent flashing gaps, but ensure it doesn't overlap inappropriately
                duration = chunk_end - chunk_start
                if duration > 0:
                    # Make uppercase for popping style
                    display_text = chunk_text.strip().upper()
                    sub_clip = create_subtitle_clip(display_text, chunk_start, duration)
                    subtitle_clips.append(sub_clip)
                chunk_text = ""
                chunk_start = -1
                
        if subtitle_clips:
            print("Compositing subtitles naturally over video...")
            final_video = CompositeVideoClip([bg_video] + subtitle_clips)
        else:
            final_video = bg_video
            
        print("Rendering final video. This may take a few minutes...")
        final_video.write_videofile(
            output_path, 
            fps=30, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast", # Faster for MVP
            threads=4
        )
        print(f"🎉 Final video rendered successfully at: {output_path}")
        
        # Clean up memory
        for c in clips:
            c.close()
        bg_video.close()
        audio.close()
        final_video.close()
        
        return output_path
    except Exception as e:
        print(f"Error rendering video: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Testing Video Renderer...")
