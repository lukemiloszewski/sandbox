import os
from typing import List

import dotenv
import spotipy
from rich.pretty import pprint
from spotipy.oauth2 import SpotifyOAuth

dotenv.load_dotenv()


SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", None)
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", None)
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", None)


def fetch_saved_tracks(session: spotipy.Spotify, no_of_records: int = 100) -> List[dict]:
    results = []
    offset = 0
    while no_of_records > 0:
        limit = min(no_of_records, 50)
        response = session.current_user_saved_tracks(limit=limit, offset=offset)
        for item in response["items"]:
            track = item["track"]
            results.append({"artist": track["artists"][0]["name"], "name": track["name"]})
        no_of_records -= limit
        offset += limit
    return results


if __name__ == "__main__":
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-library-read",
        )
    )

    tracks = fetch_saved_tracks(sp, 20)
    pprint(tracks)
