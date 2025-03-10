from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from datetime import datetime
import os

app = Flask(__name__)

# Initialize the client with environment variable
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# Spotify credentials from environment variables
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

# Initialize Spotify client with necessary scopes
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-modify-playback-state,user-read-playback-state"
))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['message']
    
    # Check for predefined commands
    if user_input.lower() == 'time':
        response_text = "The current time is " + datetime.now().strftime("%H:%M:%S")
    elif user_input.lower() == 'date':
        response_text = "Today's date is " + datetime.now().strftime("%Y-%m-%d")
    elif user_input.lower() == 'weather':
        # You can integrate a weather API here
        response_text = "The weather is sunny with a chance of rain."
    elif 'play' in user_input.lower() and 'on spotify' in user_input.lower():
        # Extract song name by removing the command keywords
        song_name = user_input.lower().replace('play', '').replace('on spotify', '').strip()
        try:
            # Search for the song on Spotify
            results = sp.search(q=song_name, limit=1)
            if results['tracks']['items']:
                track_uri = results['tracks']['items'][0]['uri']
                
                # Get active device id
                devices = sp.devices()
                if devices['devices']:
                    device_id = devices['devices'][0]['id']  # Using the first available device
                    sp.start_playback(device_id=device_id, uris=[track_uri])
                    response_text = f"Playing {song_name} on Spotify."
                else:
                    response_text = "No active Spotify device found. Please open Spotify and play something first."
            else:
                response_text = f"Could not find {song_name} on Spotify."
        except Exception as e:
            logging.error(f"Error playing song on Spotify: {e}")
            response_text = "I can't directly control Spotify to play a song for you. Please make sure Spotify is open and you are logged in."
    else:
        # Generate response using Gemini model
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_input],
            config=types.GenerateContentConfig(
                max_output_tokens=500,
                temperature=0.7  # Adjust temperature for more human-like responses
            )
        )
        response_text = response.text
    
    return jsonify({'response': response_text})

if __name__ == '__main__':
    app.run(debug=True)
