from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
import os, spotipy, json
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path

# --- Config ---
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = "user-read-playback-state"
TOKEN_FILE = Path("spotify_token.json")

# --- FastAPI app ---
app = FastAPI()

# --- Spotify OAuth ---
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE)


def load_token():
  if TOKEN_FILE.exists():
    return json.loads(TOKEN_FILE.read_text())
  return None


def save_token(token_info):
  TOKEN_FILE.write_text(json.dumps(token_info))


def get_spotify_client():
  token_info = load_token()
  if not token_info:
    raise Exception("No token found. Authenticate first.")
  if sp_oauth.is_token_expired(token_info):
    token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    save_token(token_info)
  return spotipy.Spotify(auth=token_info['access_token'])


# --- Routes ---
@app.get("/login")
async def login():
  url = sp_oauth.get_authorize_url()
  return RedirectResponse(url)


@app.get("/callback")
async def callback(request: Request):
  code = request.query_params.get("code")
  if not code:
    return JSONResponse({"error": "No code provided"})
  try:
    token_info = sp_oauth.get_access_token(code)
    save_token(token_info)
    return JSONResponse({"status": "success", "token": token_info})
  except Exception as e:
    return JSONResponse({"error": str(e)})


@app.get("/current-track")
async def get_current_track():
  try:
    spotify = get_spotify_client()
    current_playback = spotify.current_playback()

    if current_playback and current_playback.get('is_playing'):
      if not current_playback.get('context'):
        return {"track": "podcast", "artist": "podcast"}
      track_name = current_playback['item']['name']
      artist_name = ", ".join(
          [artist['name'] for artist in current_playback['item']['artists']])
      return {"track": track_name, "artist": artist_name}

    return {"track": "no_playback", "artist": "no_playback"}

  except Exception as e:
    print(f"Unexpected Error: {e}")
    return {"track": None, "artist": None}
