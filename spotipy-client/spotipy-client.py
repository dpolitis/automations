from flask import Flask, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Flask app initialization
app = Flask(__name__)

# Set your app credentials and redirect URI
CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT_URI = "http://127.0.0.1:5000/callback"

# Define the required scope
SCOPE = "user-read-playback-state"

# Initialize SpotifyOAuth for authentication
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
)

# Retrieve and refresh the token
def get_spotify_client():
    token_info = sp_oauth.get_cached_token()  # Retrieves the token from cache
    if not token_info or sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return spotipy.Spotify(auth=token_info['access_token'])

# Route to fetch the currently playing track
@app.route('/current-track', methods=['GET'])

def get_current_track():
    try:
        spotify = get_spotify_client()
        current_playback = spotify.current_playback()

        if current_playback and current_playback.get('is_playing'):
            if not current_playback.get('context'):
                return jsonify({"track": "podcast", "artist": "podcast"})

            track_name = current_playback['item']['name']
            artist_name = ", ".join([artist['name'] for artist in current_playback['item']['artists']])
            return jsonify({"track": track_name, "artist": artist_name})
 
        # Default response if no track is playing
        return jsonify({"track": "no_playback", "artist": "no_playback"})

    except Exception as e:
        print(f"Unexpected Error: {e}")

    # Fallback response for any error
    return jsonify({"track": None, "artist": None})

# Main function to run the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
