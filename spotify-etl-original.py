import argparse
import os

import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_setting(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and (value is None or not str(value).strip()):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch your recently played Spotify tracks locally."
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--timezone",
        default=os.getenv("APP_TIMEZONE", "Asia/Singapore"),
        help="Timezone used when displaying played_at values.",
    )
    return parser.parse_args()


def build_spotify_client():
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=get_setting("SPOTIFY_CLIENT_ID", required=True),
            client_secret=get_setting("SPOTIFY_CLIENT_SECRET", required=True),
            redirect_uri=get_setting("SPOTIFY_REDIRECT_URI", required=True),
            scope="user-read-recently-played",
            cache_path=os.getenv("SPOTIFY_TOKEN_CACHE", ".spotify_token_cache"),
        )
    )


def get_recently_played_tracks(limit=20, timezone_name="Asia/Singapore"):
    spotify_client = build_spotify_client()
    results = spotify_client.current_user_recently_played(limit=max(1, min(limit, 50)))

    records = []
    for item in results.get("items", []):
        track = item.get("track") or {}
        artists = track.get("artists") or []
        records.append(
            {
                "track_name": track.get("name") or "Unknown track",
                "artist": artists[0].get("name") if artists else "Unknown artist",
                "album": (track.get("album") or {}).get("name") or "Unknown album",
                "played_at_raw": item.get("played_at"),
                "track_id": track.get("id"),
            }
        )

    if not records:
        return pd.DataFrame(
            columns=["track_name", "artist", "album", "played_at", "track_id"]
        )

    frame = pd.DataFrame(records)
    frame["played_at"] = (
        pd.to_datetime(frame["played_at_raw"], utc=True, errors="coerce")
        .dt.tz_convert(timezone_name)
        .dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    )
    return frame.drop(columns=["played_at_raw"])


def main():
    args = parse_args()
    frame = get_recently_played_tracks(
        limit=args.limit,
        timezone_name=args.timezone,
    )

    if frame.empty:
        print("No recently played tracks returned.")
        return 0

    print(frame.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
