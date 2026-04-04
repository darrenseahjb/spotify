# Spotify Listening Analytics Pipeline

Scheduled Spotify ingestion pipeline on AWS, storing recently played history in PostgreSQL and feeding a live Streamlit dashboard.

## Quick Links

- Live Demo: [Spotify Listening Analytics](https://spotify-listening-analytics.streamlit.app/)
- Source Code: [Spotify Listening Analytics Pipeline](https://github.com/darrenseahjb/spotify)
- Dashboard Repo: [spotify-streamlit-dashboard](https://github.com/darrenseahjb/spotify-streamlit-dashboard)

## What This Repo Is

This is the backend repo.

It does four things:
- refreshes a Spotify access token from a stored refresh token
- pulls recently played tracks from the Spotify Web API on a schedule
- writes deduplicated listening history into PostgreSQL on Amazon RDS
- provides the same underlying dataset that the public dashboard reads from

This is a personal analytics pipeline, not a production SaaS system.

## Repo Split

This project originally lived in one repo.

It is now split on purpose:
- this repo keeps the ingestion path, schema, and AWS-side pipeline
- the public Streamlit dashboard lives in a separate repo and deploys independently

That split keeps the backend repo focused on data collection and storage, while the dashboard repo can iterate faster on presentation and deployment.

## Architecture

1. Spotify Web API exposes recently played track data.
2. AWS Lambda refreshes the token and requests the latest listens.
3. The Lambda inserts new rows into `spotify_history` on Amazon RDS for PostgreSQL.
4. EventBridge runs the ingestion job on a fixed schedule.
5. A separate Streamlit app reads from the database and renders the dashboard.

## Why This Design

- Lambda + EventBridge keeps the ingestion path small and cheap for a personal project.
- RDS provides persistent storage instead of keeping everything in local files.
- `(track_id, played_at)` is used as the deduplication key so repeated scheduled pulls do not create duplicate rows.
- The dashboard is split into a separate public repo because the presentation layer now evolves independently from the ingestion layer.

## Stack

- Python
- Spotify Web API
- AWS Lambda
- Amazon EventBridge
- Amazon RDS for PostgreSQL
- PostgreSQL

## Repository Guide

- `lambda_package/lambda_function.py`
  Lambda entrypoint for token refresh, Spotify API retrieval, deduplicated inserts, and structured success/failure responses.
- `get_refresh_token.py`
  One-time helper to exchange a Spotify authorization code for a refresh token.
- `schema.sql`
  PostgreSQL schema for the target table.
- `.env.example`
  Environment variable template for local setup.

## Core Behaviors

- scheduled polling instead of long-running ingestion
- duplicate-safe inserts into `spotify_history`
- persistent storage in PostgreSQL
- shared dataset for the public dashboard and any local analysis

## Tradeoffs and Limitations

- This pipeline is scheduled polling, not real-time streaming.
- It depends on Spotify's recently played endpoint, so historical coverage is limited by what the API exposes unless a separate backfill is done.
- Reliability is basic: deduplication and env validation are implemented, but retries, alerting, and formal monitoring are not.
- The Lambda is intentionally simple and single-purpose; infrastructure is configured manually rather than through IaC.

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

3. Exchange an auth code for a refresh token if needed.

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

5. Dashboard development and local Streamlit runs now live in the separate dashboard repo.

## Deployment Notes

- package the Lambda from `lambda_package`
- configure Lambda environment variables from `.env.example`
- schedule the function with EventBridge
- configure Streamlit secrets separately for the dashboard deployment

## Related Repository

- [Spotify Listening Analytics Dashboard](https://github.com/darrenseahjb/spotify-streamlit-dashboard)
