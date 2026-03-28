# Spotify Listening Analytics Pipeline

Serverless Spotify listening analytics pipeline feeding a live Streamlit dashboard.

## Quick Links

- Live Demo: [Spotify Listening Analytics](https://spotify-listening-analytics.streamlit.app/)
- Source Code: [Spotify Listening Analytics Pipeline](https://github.com/darrenseahjb/spotify)
- Dashboard Repo: [spotify-streamlit-dashboard](https://github.com/darrenseahjb/spotify-streamlit-dashboard)

## Overview

This is the backend repo.

It refreshes Spotify tokens, ingests recently played tracks, writes deduplicated history into PostgreSQL on Amazon RDS, and powers the live dashboard.

## Architecture

1. Spotify Web API provides recently played track data.
2. AWS Lambda refreshes the access token and pulls the newest listens.
3. The Lambda writes new rows into `spotify_history` in PostgreSQL on Amazon RDS.
4. EventBridge runs the ingestion job on a schedule.
5. A separate Streamlit app reads from the database and presents the data publicly.

## Stack

- Python
- Spotify Web API
- AWS Lambda
- Amazon EventBridge
- Amazon RDS for PostgreSQL
- PostgreSQL
- Streamlit

## Repository Guide

- `lambda_package/lambda_function.py`
  Lambda entrypoint for token refresh, API calls, deduplication, and inserts.
- `get_refresh_token.py`
  One-time helper to exchange a Spotify authorization code for a refresh token.
- `spotify-etl-original.py`
  Local smoke-test script for recently played retrieval.
- `spotify_dashboard/app.py`
  Local dashboard version connected to the same `spotify_history` table.
- `schema.sql`
  PostgreSQL schema for the target table.
- `.env.example`
  Environment variable template for local setup.

## Core Behaviors

- incremental ingestion from Spotify recently played
- duplicate-safe inserts into `spotify_history`
- persistent storage in PostgreSQL
- scheduled refreshes through EventBridge
- shared dataset for local and public dashboards

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

5. Run the local ingestion smoke test or local dashboard.

```powershell
python .\spotify-etl-original.py --limit 20
streamlit run .\spotify_dashboard\app.py
```

## Deployment Notes

- package the Lambda from `lambda_package`
- configure Lambda environment variables from `.env.example`
- schedule the function with EventBridge
- configure Streamlit secrets separately for the dashboard deployment

## Related Repository

- [Spotify Listening Analytics Dashboard](https://github.com/darrenseahjb/spotify-streamlit-dashboard)
