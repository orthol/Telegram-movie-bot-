import os
import asyncio
import logging
import threading
from datetime import datetime
from flask import Flask
from bot import movie_poster

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Movie Bot is alive and running!"

async def main():
    logging.info("🤖 Movie Bot Starting...")

    if not all([os.getenv('BOT_TOKEN'), os.getenv('TMDB_API_KEY'), os.getenv('CHANNEL_USERNAME')]):
        logging.error("❌ Missing environment variables")
        return

    if movie_poster is None:
        logging.error("❌ Movie poster not initialized")
        return

    await movie_poster.post_to_channel("🚀 Movie Bot Started - Posting every 2 minutes with variety!")
    logging.info("✅ Starting continuous posting every 2 minutes...")

    cycle = 0
    while True:
        try:
            cycle += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            logging.info(f"🔄 CYCLE #{cycle} at {current_time}")

            if cycle % 3 == 1:
                await movie_poster.post_latest_movies()
            elif cycle % 3 == 2:
                await movie_poster.post_trending_movies()
            else:
                await movie_poster.post_upcoming_movies()

            logging.info(f"✅ Cycle #{cycle} completed")
            logging.info("⏰ Waiting 2 minutes...")
            await asyncio.sleep(120)

        except Exception as e:
            logging.error(f"💥 Error: {e}")
            await asyncio.sleep(120)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
