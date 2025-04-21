# Simple MVP: LocalPod Hosting Platform Backend (FastAPI + Play.ht integration)

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uuid
from datetime import datetime
import os

app = FastAPI()

# CORS (adjust origin in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory episode store (use a DB in production)
episodes = []

# --- Models ---
class Episode(BaseModel):
    id: str
    title: str
    script: str
    audio_url: str
    pub_date: str

# --- Config ---
PLAYHT_API_KEY = os.getenv("PLAYHT_API_KEY")
PLAYHT_USER_ID = os.getenv("PLAYHT_USER_ID")

# --- Routes ---
@app.post("/generate")
async def generate_episode(
    title: str = Form(...),
    script: str = Form(...)
):
    episode_id = str(uuid.uuid4())
    pub_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    # Step 1: Send to Play.ht
    headers = {
        "Authorization": f"Bearer {PLAYHT_API_KEY}",
        "X-User-Id": PLAYHT_USER_ID,
        "Content-Type": "application/json"
    }
    body = {
        "voice": "en-US-JennyNeural",
        "content": script,
        "title": title,
    }
    playht_response = requests.post("https://api.play.ht/api/v2/tts", json=body, headers=headers)
    playht_data = playht_response.json()
    audio_url = playht_data.get("audioUrl") or playht_data.get("url")  # fallback key name

    # Step 2: Store episode
    episode = Episode(id=episode_id, title=title, script=script, audio_url=audio_url, pub_date=pub_date)
    episodes.append(episode)
    return {"id": episode_id, "audio_url": audio_url}

# --- RSS Feed ---
@app.get("/feed.xml")
def rss_feed():
    feed_items = ""
    for ep in episodes:
        feed_items += f"""
        <item>
            <title>{ep.title}</title>
            <pubDate>{ep.pub_date}</pubDate>
            <enclosure url=\"{ep.audio_url}\" type=\"audio/mpeg\" />
            <guid>{ep.id}</guid>
        </item>"""

    rss = f"""
    <rss version=\"2.0\">
      <channel>
        <title>LocalPod Publisher Feed</title>
        <link>https://yourdomain.com</link>
        <description>Auto-generated podcast feed</description>
        {feed_items}
      </channel>
    </rss>"""

    return Response(content=rss.strip(), media_type="application/xml")
