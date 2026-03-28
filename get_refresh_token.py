import argparse
import base64
import os

import requests


def get_setting(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and (value is None or not str(value).strip()):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description="Exchange a Spotify authorization code for a refresh token."
    )
    parser.add_argument(
        "--code",
        help="Authorization code from the Spotify callback URL. Falls back to SPOTIFY_AUTH_CODE.",
    )
    parser.add_argument(
        "--redirect-uri",
        help="Override the redirect URI configured for the Spotify app.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    client_id = get_setting("SPOTIFY_CLIENT_ID", required=True)
    client_secret = get_setting("SPOTIFY_CLIENT_SECRET", required=True)
    redirect_uri = args.redirect_uri or get_setting(
        "SPOTIFY_REDIRECT_URI", required=True
    )
    auth_code = args.code or get_setting("SPOTIFY_AUTH_CODE", required=True)

    encoded_credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri,
        },
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise RuntimeError(
            "Spotify did not return a refresh token. Make sure the authorization "
            "code is unused and the redirect URI matches the Spotify app settings."
        )

    print("Refresh token:")
    print(refresh_token)

    expires_in = payload.get("expires_in")
    if expires_in:
        print(f"\nAccess token lifetime: {expires_in} seconds")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
