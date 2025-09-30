import os
import requests 
import sqlite3
import logging 
from datetime import datetime, timedelta, timezone 
from dotenv import load_dotenv

load_dotenv()
YT_API_KEY = os.getenv("YT_API_KEY")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
HASHTAG = "#hijackhackclub"
DB_PATH = os.getenv("DB_PATH")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if not (YT_API_KEY and SLACK_WEBHOOK):
    raise SystemExit("Missing YT_API_KEY or SLACK_WEBHOOK_URL in environment variables.")
    
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS seen (video_id TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, last_run TEXT)")
conn.commit()

def get_last_run():
    cur.execute("SELECT last_run FROM state WHERE id=1")
    row = cur.fetchone()
    if row and row[0]:
        return datetime.fromisoformat(row[0])
    # Look back 1 day by default if no last run recorded
    return datetime.now(timezone.utc) - timedelta(days=1)

def set_last_run(ts: datetime):
    cur.execute("INSERT OR REPLACE INTO state (id, last_run) VALUES (1, ?)", (ts.isoformat(),))
    conn.commit()

def already_seen(video_id: str) -> bool:
    cur.execute("SELECT 1 FROM seen WHERE video_id=?", (video_id,))
    return cur.fetchone() is not None

def mark_seen(video_id: str):
    cur.execute("INSERT OR IGNORE INTO seen (video_id) VALUES (?)", (video_id,))
    conn.commit()

def yt_search_hashtag(hashtag: str, published_after=None, max_results=25):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": hashtag,
        "type": "video",
        "order": "date",
        "maxResults": max_results,
        "key": YT_API_KEY,
    }
    if published_after:
        params["publishedAfter"] = published_after.isoformat()
    
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("items", [])

def post_to_slack(title, channel, published_at, link, thumbnail_url):
    # Format timestamp for better readability
    published_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
    formatted_time = published_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{link}|{title}>*\nby {channel}\nPublished at: {formatted_time}"
                },
                "accessory": {
                    "type": "image",
                    "image_url": thumbnail_url,
                    "alt_text": "thumbnail"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "▶ Watch on YouTube"},
                        "url": link
                    }
                ]
            }
        ]
    }
    response = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
    response.raise_for_status()
    return response

def run_once():
    last_run = get_last_run()
    logging.info(f"Last run was at {last_run.isoformat()}")

    items = yt_search_hashtag(HASHTAG, published_after=last_run)
    logging.info("Fetched %d results", len(items))

    new_count = 0 
    for i in items:
        vid = i["id"]["videoId"]
        if already_seen(vid):
            continue
        title = i["snippet"]["title"]
        channel = i["snippet"]["channelTitle"]
        published_at = i["snippet"]["publishedAt"]
        link = f"https://www.youtube.com/watch?v={vid}"
        thumbnail_url = i["snippet"]["thumbnails"]["high"]["url"]

        try:
            post_to_slack(title, channel, published_at, link, thumbnail_url)
            logging.info(f"Posted new video: {title} {vid}")
            mark_seen(vid)
            new_count += 1
        except Exception as e:
            logging.error(f"Failed to post video {vid} to Slack: {e}")
    
    set_last_run(datetime.now(timezone.utc))
    logging.info(f"Run complete. {new_count} new videos posted.")

if __name__ == "__main__":
    run_once()