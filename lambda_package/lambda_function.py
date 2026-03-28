import base64
import json
import logging
import os

import psycopg2
import requests
import spotipy
from psycopg2.extras import execute_values


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def get_required_env(name):
    value = os.getenv(name)
    if value and value.strip():
        return value
    raise RuntimeError(f"Missing required environment variable: {name}")


def get_recent_limit():
    raw_value = os.getenv("SPOTIFY_RECENT_LIMIT", "25")
    try:
        limit = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("SPOTIFY_RECENT_LIMIT must be an integer.") from exc
    return max(1, min(limit, 50))


def refresh_access_token():
    refresh_token = get_required_env("SPOTIFY_REFRESH_TOKEN")
    client_id = get_required_env("SPOTIFY_CLIENT_ID")
    client_secret = get_required_env("SPOTIFY_CLIENT_SECRET")

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": "Basic "
            + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise RuntimeError("Spotify token response did not include access_token.")
    return access_token


def fetch_recently_played(limit):
    spotify_client = spotipy.Spotify(auth=refresh_access_token())
    response = spotify_client.current_user_recently_played(limit=limit)
    items = response.get("items", [])

    records = []
    for item in items:
        track = item.get("track") or {}
        artists = track.get("artists") or []
        album = track.get("album") or {}
        track_id = track.get("id")
        played_at = item.get("played_at")

        if not track_id or not played_at:
            LOGGER.warning("Skipping malformed Spotify record: %s", item)
            continue

        records.append(
            (
                track_id,
                track.get("name") or "Unknown track",
                artists[0].get("name") if artists else "Unknown artist",
                album.get("name") or "Unknown album",
                played_at,
                track.get("duration_ms") or 0,
            )
        )

    return records


def insert_history(records):
    if not records:
        return 0

    connection = psycopg2.connect(
        host=get_required_env("DB_HOST"),
        dbname=get_required_env("DB_NAME"),
        user=get_required_env("DB_USER"),
        password=get_required_env("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
    )

    try:
        with connection:
            with connection.cursor() as cursor:
                execute_values(
                    cursor,
                    """
                    INSERT INTO spotify_history (
                        track_id,
                        track_name,
                        artist,
                        album,
                        played_at,
                        duration_ms
                    )
                    VALUES %s
                    ON CONFLICT (track_id, played_at) DO NOTHING
                    RETURNING 1;
                    """,
                    records,
                )
                return len(cursor.fetchall())
    finally:
        connection.close()


def lambda_handler(event, context):
    try:
        limit = get_recent_limit()
        records = fetch_recently_played(limit)
        inserted_count = insert_history(records)

        LOGGER.info(
            "Spotify ETL completed. fetched=%s inserted=%s",
            len(records),
            inserted_count,
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Spotify ETL completed successfully.",
                    "fetched_count": len(records),
                    "inserted_count": inserted_count,
                }
            ),
        }
    except Exception as exc:
        LOGGER.exception("Spotify ETL failed.")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "Spotify ETL failed.",
                    "error": str(exc),
                }
            ),
        }
