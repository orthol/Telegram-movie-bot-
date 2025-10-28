import os
import asyncio
import logging
import threading
from datetime import datetime
from flask import Flask
from bot import movie_poster

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Movie Bot is alive and running!"

async def post_loop():
    """Continuously post movie updates every 2 minutes"""
    if not all([os.getenv('BOT_TOKEN'), os.getenv('TMDB_API_KEY'), os.getenv('CHANNEL_USERNAME')]):
        logging.error("❌ Missing environment variables. Exiting loop.")
        return

    if movie_poster is None:
        logging.error("❌ movie_poster not initialized.")
        return

    await movie_poster.post_to_channel("🚀 Movie Bot Started — posting every 2 minutes!")
    cycle = 0

    while True:
        try:
            cycle += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            logging.info(f"🔄 Starting cycle #{cycle} at {current_time}")

            if cycle % 3 == 1:
                await movie_poster.post_latest_movies()
            elif cycle % 3 == 2:
                await movie_poster.post_trending_movies()
            else:
                await movie_poster.post_upcoming_movies()

            logging.info(f"✅ Cycle #{cycle} finished successfully.")
            await asyncio.sleep(120)  # wait 2 minutes

        except Exception as e:
            logging.error(f"💥 Error in cycle #{cycle}: {e}")
            await asyncio.sleep(60)  # wait 1 min before retry

def run_async_loop():
    """Runs the async post loop forever in a thread-safe way"""
    while True:
        try:
            asyncio.run(post_loop())
        except Exception as e:
            logging.error(f"⚠️ Async loop crashed: {e}. Restarting...")
        # short delay before restart
        import time
        time.sleep(5)

def run_flask():
    """Keeps service alive for Choreo health checks"""
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    threading.Thread(target=run_async_loop, daemon=True).start()
    run_flask()
