import os

import pandas as pd
import pg8000
import streamlit as st


st.set_page_config(page_title="Spotify Listening Insights", layout="wide")


def get_setting(name, default=None, required=False):
    value = os.getenv(name)
    if value is None:
        try:
            value = st.secrets.get(name)
        except Exception:
            value = None

    if value is None or str(value).strip() == "":
        value = default

    if required and (value is None or str(value).strip() == ""):
        raise RuntimeError(f"Missing required setting: {name}")

    return value


def get_db_config():
    return {
        "host": get_setting("DB_HOST", required=True),
        "database": get_setting("DB_NAME", required=True),
        "user": get_setting("DB_USER", required=True),
        "password": get_setting("DB_PASSWORD", required=True),
        "port": int(get_setting("DB_PORT", default="5432")),
    }


@st.cache_data(ttl=300, show_spinner=False)
def load_history(timezone_name):
    with pg8000.connect(**get_db_config()) as connection:
        history = pd.read_sql_query(
            """
            SELECT track_name, artist, album, played_at, duration_ms
            FROM spotify_history
            ORDER BY played_at DESC;
            """,
            connection,
        )

    if history.empty:
        return history

    history = history.copy()
    history["track_name"] = history["track_name"].fillna("Unknown track")
    history["artist"] = history["artist"].fillna("Unknown artist")
    history["album"] = history["album"].fillna("Unknown album")
    history["duration_ms"] = (
        pd.to_numeric(history["duration_ms"], errors="coerce").fillna(0).astype(int)
    )
    history["played_at_utc"] = pd.to_datetime(
        history["played_at"], utc=True, errors="coerce"
    )
    history = history.dropna(subset=["played_at_utc"]).copy()
    history["played_at_local"] = history["played_at_utc"].dt.tz_convert(timezone_name)
    history["played_date"] = history["played_at_local"].dt.floor("D").dt.tz_localize(
        None
    )
    return history.sort_values("played_at_utc", ascending=False).reset_index(drop=True)


def format_duration(total_duration_ms):
    total_minutes = total_duration_ms // 60000
    hours, minutes = divmod(total_minutes, 60)

    if hours and minutes:
        return f"{hours} hr {minutes} min"
    if hours:
        return f"{hours} hr"
    return f"{minutes} min"


def build_weekly_trend(history, timezone_name, days=7):
    end_date = pd.Timestamp.now(tz=timezone_name).floor("D").tz_localize(None)
    date_index = pd.date_range(end=end_date, periods=days, freq="D")
    daily_duration = (
        history.groupby("played_date")["duration_ms"].sum().reindex(date_index, fill_value=0)
    )
    trend = daily_duration.to_frame(name="total_duration_ms")
    trend["hours"] = (trend["total_duration_ms"] / 3600000).round(2)
    trend.index.name = "date"
    return trend.reset_index()


timezone_name = get_setting("APP_TIMEZONE", default="Asia/Singapore")
spotify_profile_url = get_setting("SPOTIFY_PROFILE_URL")

st.title("Spotify Listening Insights")
st.caption("Revived dashboard for the Spotify recently-played ETL pipeline.")

if st.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

try:
    history = load_history(timezone_name)
except Exception as exc:
    st.error(f"Could not load dashboard data: {exc}")
    st.info(
        "Set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT, and APP_TIMEZONE "
        "through environment variables or Streamlit secrets."
    )
    st.stop()

if history.empty:
    st.warning("The spotify_history table is empty.")
    st.stop()

today_local = pd.Timestamp.now(tz=timezone_name).date()
history_today = history[history["played_at_local"].dt.date == today_local]
total_duration_today = int(history_today["duration_ms"].sum())

latest_track = history.iloc[0]
top_album = (
    history.groupby("album")
    .size()
    .reset_index(name="play_count")
    .sort_values(["play_count", "album"], ascending=[False, True])
    .iloc[0]
)
top_artists = (
    history.groupby("artist")
    .size()
    .reset_index(name="play_count")
    .sort_values(["play_count", "artist"], ascending=[False, True])
    .head(5)
    .reset_index(drop=True)
)
top_artists.insert(0, "rank", range(1, len(top_artists) + 1))
weekly_trend = build_weekly_trend(history, timezone_name)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Total Time Today")
    st.write(format_duration(total_duration_today))
    st.caption(f"Timezone: {timezone_name}")

with col2:
    st.subheader("Latest Track")
    st.write(latest_track["track_name"])
    st.caption(
        f"{latest_track['artist']} | "
        f"{latest_track['played_at_local'].strftime('%Y-%m-%d %H:%M')}"
    )

with col3:
    st.subheader("Most Played Album")
    st.write(top_album["album"])
    st.caption(f"{int(top_album['play_count'])} plays")

left, right = st.columns(2)

with left:
    st.subheader("Top 5 Artists (All Time)")
    st.dataframe(top_artists, hide_index=True, use_container_width=True)

with right:
    st.subheader("Weekly Listening Trend")
    st.line_chart(weekly_trend.set_index("date")["hours"], use_container_width=True)

with st.expander("Recent listens", expanded=False):
    recent_listens = history[
        ["played_at_local", "track_name", "artist", "album"]
    ].head(20).copy()
    recent_listens["played_at_local"] = recent_listens["played_at_local"].dt.strftime(
        "%Y-%m-%d %H:%M"
    )
    recent_listens = recent_listens.rename(columns={"played_at_local": "played_at"})
    st.dataframe(recent_listens, hide_index=True, use_container_width=True)

if spotify_profile_url:
    st.markdown(f"[Open Spotify profile]({spotify_profile_url})")
