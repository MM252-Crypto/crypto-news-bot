import feedparser
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

# Replace these:
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RSS_FEED_URLS = os.getenv('RSS_FEED_URLS').split(',')

def post_latest_news():
    posted_links = set()
    try:
        with open('posted_links.txt', 'r') as f:
            posted_links = set(f.read().splitlines())
    except FileNotFoundError:
        pass

    for url in RSS_FEED_URLS:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Could not fetch {url}: {e}")
            continue

        feed = feedparser.parse(response.content)
        if not feed.entries:
            print(f"No entries found in the RSS feed: {url}")
            continue
        
        for entry in feed.entries:
            link = entry.link
            if link in posted_links:
                continue

            title = entry.title
            summary = entry.summary

            # Get image
            soup = BeautifulSoup(summary, 'html.parser')
            img = soup.find('img')
            image_url = img['src'] if img else None
            
            # Get summary text
            summary_text = soup.get_text().strip()


            caption = f"📰 <b>{title}</b>\n\n{summary_text}\n\n<a href='{link}'>Read more</a>\n\n#Ton #pavel #bitcoin"

            if image_url:
                send_photo(image_url, caption)
            else:
                send_text(f"{title}\n{link}")
            
            posted_links.add(link)
            with open('posted_links.txt', 'a') as f:
                f.write(link + '\n')
            break # Move to the next feed after posting the latest unique article

def send_photo(image_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'photo': image_url,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    r = requests.post(url, data=payload)
    print(r.status_code, r.text)

def send_text(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    r = requests.post(url, data=payload)
    print(r.status_code, r.text)

from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

def scheduled_task():
    """The task to be executed every 15 minutes."""
    print("Executing scheduled task: posting latest news.")
    post_latest_news()

@app.route('/')
def home():
    return "I'm alive and the scheduler is running."

if __name__ == "__main__":
    # To preserve the original behavior of running on start.
    post_latest_news()
    
    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scheduled_task, trigger="interval", minutes=15)
    scheduler.start()
    
    # Railway provides the PORT environment variable.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
