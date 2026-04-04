# Spotify Listening Analytics Pipeline

Scheduled AWS pipeline that pulls Spotify recently played history into PostgreSQL and feeds a live Streamlit dashboard.

## Quick Links

- Live Demo: [Spotify Insights](https://spotify-listening-analytics.streamlit.app/)
- Source Code: [spotify](https://github.com/darrenseahjb/spotify)
- Dashboard Repo: [spotify-streamlit-dashboard](https://github.com/darrenseahjb/spotify-streamlit-dashboard)

## What This Repo Covers

This is the backend repo.

It:
- refreshes a Spotify access token from a stored refresh token
- pulls recently played tracks from the Spotify Web API on a schedule
- writes deduplicated listening history into PostgreSQL on Amazon RDS
- provides the dataset used by the public dashboard

This is a personal analytics pipeline, not a production service.

## Repo Split

The project originally lived in one repo.

It is now split on purpose:
- this repo owns ingestion, schema, and AWS-side scheduling
- the dashboard repo owns the public Streamlit app and presentation layer

That keeps the backend focused on collection and storage, while the dashboard can evolve independently.

## Architecture

1. Spotify Web API exposes recently played track data.
2. AWS Lambda refreshes the token and fetches the latest listens.
3. Lambda inserts new rows into `spotify_history` on Amazon RDS for PostgreSQL.
4. EventBridge runs the job on a fixed schedule.
5. The public dashboard reads from the same table.

## Why This Design

- Lambda + EventBridge keeps the ingestion path small and cheap.
- RDS gives persistent storage instead of local files.
- `(track_id, played_at)` is used as the deduplication key so repeated pulls do not create duplicate rows.
- The dashboard is split into a separate repo because the presentation layer now changes faster than the ingestion code.

## Stack

- Python
- Spotify Web API
- AWS Lambda
- Amazon EventBridge
- Amazon RDS for PostgreSQL
- PostgreSQL

## Repository Guide

- `lambda_package/lambda_function.py`  
  Lambda entrypoint for token refresh, Spotify API retrieval, deduplicated inserts, and response handling.
- `get_refresh_token.py`  
  One-off helper to exchange a Spotify authorisation code for a refresh token.
- `schema.sql`  
  PostgreSQL schema for `spotify_history`.
- `.env.example`  
  Environment variable template for local setup.

## Core Behaviour

- scheduled polling
- duplicate-safe inserts into `spotify_history`
- persistent storage in PostgreSQL
- shared dataset for the public dashboard and local analysis

## Tradeoffs and Limitations

- This pipeline is scheduled polling, not streaming.
- Historical coverage depends on Spotify's recently played endpoint unless a separate backfill is done.
- Reliability is basic: deduplication and environment validation are implemented, but retries, alerting, and monitoring are not.
- Infrastructure is configured manually rather than through IaC.

## Local Setup

1. Create a virtual environment and install dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Fill in the required settings from `.env.example`.

Required variables:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REDIRECT_URI`
- `SPOTIFY_AUTH_CODE`
- `SPOTIFY_REFRESH_TOKEN`
- `SPOTIFY_RECENT_LIMIT`
- `SPOTIFY_PROFILE_URL`
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_PORT`
- `APP_TIMEZONE`
- `LOG_LEVEL`

3. Exchange an authorisation code for a refresh token if needed.

```powershell
$env:SPOTIFY_CLIENT_ID="..."
$env:SPOTIFY_CLIENT_SECRET="..."
$env:SPOTIFY_REDIRECT_URI="http://127.0.0.1:8888/callback"
$env:SPOTIFY_AUTH_CODE="..."
python .\get_refresh_token.py
```

4. Create the target table.

```powershell
psql -h <host> -U <user> -d <database> -f .\schema.sql
```

Dashboard development and local Streamlit runs now live in the separate dashboard repo.

## Deployment Notes

- package the Lambda from `lambda_package`
- configure Lambda environment variables from `.env.example`
- schedule the function with EventBridge
- configure Streamlit secrets separately for the dashboard deployment

## Related Repository

- [Spotify Listening Analytics Dashboard](https://github.com/darrenseahjb/spotify-streamlit-dashboard)
