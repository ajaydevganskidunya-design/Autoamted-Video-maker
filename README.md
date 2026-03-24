# 🤖 YouTube Automation System

A fully automated AI-driven system to generate and upload YouTube Shorts.

## 🌟 Features
- **AI Scripting**: Generates high-retention scripts using OpenAI GPT-4o or Google Gemini.
- **Voiceover Generation**: High-quality TTS via ElevenLabs with word-level timestamps.
- **Stock Footage Sourcing**: Automatically finds and downloads relevant portrait videos from Pexels.
- **Dynamic Rendering**: Syncs background clips, voiceovers, and animated subtitles.
- **Auto-Upload**: Uploads the final video directly to YouTube as a Private Short.

## 🛠️ Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd YT
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the `YT` directory:
   ```env
   OPENAI_API_KEY=your_openai_or_gemini_key
   ELEVENLABS_API_KEY=your_elevenlabs_key
   PEXELS_API_KEY=your_pexels_key
   ```

4. **YouTube API**:
   - Place your `client_secrets.json` in the `YT` folder.
   - The first run will prompt you to authenticate via browser.

## 🚀 Usage

Run the main automation script:
```bash
python main.py "Your Video Topic"
```

## 📂 Project Structure
- `main.py`: Entry point for the automation flow.
- `script_generator.py`: LLM logic for scripts and keywords.
- `audio_generator.py`: ElevenLabs TTS integration.
- `video_sourcer.py`: Pexels API video fetching.
- `video_renderer.py`: MoviePy assembly and subtitle rendering.
- `youtube_uploader.py`: OAuth2 YouTube upload logic.
- `bgm/`: Folder for background music (optional).
