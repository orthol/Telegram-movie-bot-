import os
import asyncio
import schedule
import time
from datetime import datetime
from bot import movie_poster
import logging

async def run_scheduled_task(task_function, task_name):
    """Run a scheduled task with error handling"""
    try:
        logging.info(f"🕒 Starting: {task_name}")
        if movie_poster is None:
            logging.error("❌ Movie poster not initialized, skipping task")
            return
            
        success = await task_function()
        if success:
            logging.info(f"✅ Completed: {task_name}")
        else:
            logging.error(f"❌ Failed: {task_name}")
    except Exception as e:
        logging.error(f"❌ Error in {task_name}: {e}")

def setup_schedule():
    """Setup all scheduled tasks"""
    
    # Daily update at 9:00 AM
    schedule.every().day.at("09:00").do(
        lambda: asyncio.create_task(run_scheduled_task(movie_poster.post_daily_update, "Daily Update"))
    )
    
    # Latest movies at 12:00 PM
    schedule.every().day.at("12:00").do(
        lambda: asyncio.create_task(run_scheduled_task(movie_poster.post_latest_movies, "Latest Movies"))
    )
    
    # Trending movies at 3:00 PM  
    schedule.every().day.at("15:00").do(
        lambda: asyncio.create_task(run_scheduled_task(movie_poster.post_trending_movies, "Trending Movies"))
    )
    
    # Upcoming movies at 6:00 PM
    schedule.every().day.at("18:00").do(
        lambda: asyncio.create_task(run_scheduled_task(movie_poster.post_upcoming_movies, "Upcoming Movies"))
    )

async def main():
    """Main scheduler loop"""
    logging.info("🤖 Movie Auto-Poster Bot Starting...")
    
    # Verify environment variables
    required_vars = ['BOT_TOKEN', 'TMDB_API_KEY', 'CHANNEL_USERNAME']
    for var in required_vars:
        if not os.getenv(var):
            logging.error(f"❌ Missing environment variable: {var}")
            return
    
    logging.info("✅ All environment variables found")
    
    # Check if movie_poster initialized
    if movie_poster is None:
        logging.error("❌ Movie poster failed to initialize. Check previous errors.")
        return
    
    # Test bot connection
    logging.info("🔌 Testing bot connection...")
    connection_ok = await movie_poster.test_bot_connection()
    if not connection_ok:
        logging.error("❌ Bot connection test failed. Please check BOT_TOKEN.")
        return
    
    # Setup schedule
    setup_schedule()
    
    # Send startup message
    try:
        startup_msg = f"🚀 Movie Bot Started Successfully!\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n📅 Next posts: 9AM, 12PM, 3PM, 6PM"
        success = await movie_poster.post_to_channel(startup_msg)
        if success:
            logging.info("✅ Startup message sent")
        else:
            logging.error("❌ Failed to send startup message")
    except Exception as e:
        logging.error(f"❌ Could not send startup message: {e}")
    
    logging.info("⏰ Scheduler started. Waiting for scheduled posts...")
    
    # Main loop
    while True:
        try:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logging.error(f"❌ Scheduler error: {e}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
