# Hijack-Feed 

A Slack integration that gets YouTube videos with the hashtag #hijackhackclub and posts them to the #hijack-feed channel in the Hack Club Slack. Made for [Hijack](https://hijack.hackclub.com/), a Hack Club YSWS.

## How to use with your own hashtag?

1. Fork this repo.
2. Create a `.env` file in the root directory with the following variables:

```
YT_API_KEY=YOUR_YOUTUBE_API_KEY
SLACK_WEBHOOK_URL=YOUR_SLACK_WEBHOOK_URL
DB_PATH=YOUR_DATABASE_PATH
```
3. Change the `HASHTAG` variable in `main.py` to your desired hashtag. Make sure to include the `#` symbol.
4. Deploy the code to a server or a cloud function that can run Python scripts.
5. Set up a cron job or a scheduled task to run the script periodically (e.g., every hour). Keep in mind that the YouTube Data API has usage limits, so choose a frequency that works for you.

## Requirements
- Python 3.7+
- `requests` library
- `logging` library
- `dotenv` library

*NOTE: `os`, `sqlite3` and `datetime` are part of the Python standard library.*
