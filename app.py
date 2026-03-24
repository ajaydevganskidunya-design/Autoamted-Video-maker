import streamlit as st # type: ignore
import os
import time
import re
from moviepy import AudioFileClip # type: ignore

try:
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    if "ELEVENLABS_API_KEY" in st.secrets:
        os.environ["ELEVENLABS_API_KEY"] = st.secrets["ELEVENLABS_API_KEY"]
    if "PEXELS_API_KEY" in st.secrets:
        os.environ["PEXELS_API_KEY"] = st.secrets["PEXELS_API_KEY"]
except Exception:
    pass # Not running on Streamlit Cloud

# Import our custom YouTube Automation modules
from script_generator import generate_script_and_prompts # type: ignore
from audio_generator import generate_audio # type: ignore
from video_sourcer import get_stock_video # type: ignore
from video_renderer import render_final_video # type: ignore
from youtube_uploader import upload_video # type: ignore

# Config Page
st.set_page_config(page_title="YouTube Automation", page_icon="🤖", layout="centered")

# Modern UI Header
st.title("🤖 Faceless YouTube Studio")
st.markdown("Generate and upload high-retention TikToks and Shorts in **seconds**.")

# Input Section
topic = st.text_input("What is your video about?", placeholder="e.g. Why Drop Shipping is Dead")

# Debug Toggle
debug_mode = st.expander("🛠️ Advanced Settings / Debug")
with debug_mode:
    show_logs = st.checkbox("Show internal logs on failure", value=True)
    if st.button("Test API Connectivity"):
        with st.spinner("Checking API..."):
            test_key = os.getenv("OPENAI_API_KEY")
            if test_key and isinstance(test_key, str):
                st.write(f"Key found (starts with: {test_key[:5]}...)")
            elif test_key:
                st.write("Key found but is not a string.")
            else:
                st.error("No API key found in secrets!")

generate_btn = st.button("Generate Video", type="primary")

# Persist output file across interactions
if "final_video" not in st.session_state:
    st.session_state["final_video"] = None

if generate_btn:
    if not topic.strip():
        st.error("Please enter a topic.")
    else:
        st.session_state["topic"] = topic
        
        # 1. Scripts
        with st.status("📝 Step 1: Crafting Viral Script & Scenes...", expanded=True) as status:
            try:
                scenes = generate_script_and_prompts(topic)
                if not scenes:
                    status.update(label="Failed to generate script (No response).", state="error")
                    st.error("The AI failed to return a script. Check your API key or model availability.")
                    st.stop()
            except Exception as e:
                status.update(label=f"Script Error: {type(e).__name__}", state="error")
                st.error(f"Error during script generation: {str(e)}")
                if show_logs:
                    st.exception(e)
                st.stop()
            
            script = " ".join([scene["text"] for scene in scenes])
            st.write(f"✅ Generated {len(scenes)} distinct scenes ({len(script)} characters).")
            # Show script preview
            for i, scene in enumerate(scenes):
                st.caption(f"**Scene {i+1}** (Visual: {scene['keyword']}): {scene['text']}")
                
            status.update(label="Script Generated!", state="complete")
            
        # 2. Voiceover
        with st.status("🎙️ Step 2: Generating ElevenLabs AI Voice...", expanded=True) as status:
            audio_path, timings_path = generate_audio(script, output_filename="temp_voiceover.mp3")
            if not audio_path:
                status.update(label="Failed to generate audio.", state="error")
                st.stop()
            st.audio(audio_path)
            status.update(label="Voiceover Downloaded!", state="complete")
            
        # 3. Video Assets
        with st.status(f"🎥 Step 3: Sourcing {len(scenes)} Pexels Stock Videos...", expanded=True) as status:
            audio = AudioFileClip(audio_path)
            total_duration = audio.duration
            audio.close()
            
            total_chars = len(script)
            scene_videos = []
            
            progress_bar = st.progress(0)
            for i, scene in enumerate(scenes):
                scene_ratio = len(scene["text"]) / max(1, total_chars)
                scene_duration = scene_ratio * total_duration
                
                kw = scene["keyword"]
                st.write(f"🔍 Fetching scene {i+1} background: '{kw}'")
                vp = get_stock_video(kw, output_filename=f"temp_bg_{i}.mp4")
                if vp:
                    scene_videos.append({"path": vp, "duration": scene_duration})
                progress_bar.progress((i + 1) / len(scenes))
                
            if not scene_videos:
                status.update(label="Failed to source Pexels videos.", state="error")
                st.stop()
            status.update(label="All Assets Sourced!", state="complete")
            
        # 4. Rendering Pipeline
        with st.status("⚙️ Step 4: Composing & Rendering Video...", expanded=True) as status:
            st.write("Adding dynamic subtitles, background music, and compositing clips...")
            st.warning("This process takes a few minutes depending on hardware limitations.")
            
            safe_topic = re.sub(r'[^a-zA-Z0-9_\-]', '', topic.replace(' ', '_').lower()[:30])
            output_filename = f"final_youtube_short_{safe_topic}.mp4"
            final_path = render_final_video(scene_videos, audio_path, timings_path, output_filename)
            
            if final_path:
                status.update(label="Video Rendered Successfully! 🎉", state="complete")
                
                # Cleanup temp files gracefully
                time.sleep(1)
                try:
                    if os.path.exists("temp_voiceover.mp3"): os.remove("temp_voiceover.mp3")
                    if os.path.exists("temp_voiceover.json"): os.remove("temp_voiceover.json")
                    for i in range(15):
                        if os.path.exists(f"temp_bg_{i}.mp4"): os.remove(f"temp_bg_{i}.mp4")
                except Exception as e:
                    pass
                
                st.session_state["final_video"] = final_path
            else:
                status.update(label="MoviePy render failed.", state="error")
                st.stop()
                
# Upload Section if video exists
if st.session_state.get("final_video"):
    st.divider()
    st.subheader("🎉 Your Video is Ready!")
    st.video(st.session_state["final_video"])
    
    st.markdown("### Upload it into the World")
    
    if st.button("🚀 Auto-Upload to YouTube", use_container_width=True):
        with st.spinner("Authenticating with Google and uploading as Private Short..."):
            desc = f"{st.session_state['topic']}\n\nGenerated efficiently via Python AI Pipeline."
            video_id = upload_video(
                st.session_state["final_video"], 
                title=st.session_state["topic"], 
                description=desc
            )
            
            if video_id:
                st.success(f"Successfully live on YouTube! Watch here: https://youtu.be/{video_id}")
                st.balloons()
            else:
                st.error("Upload failed. Check terminal for error logs.")
