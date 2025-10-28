import asyncio
import schedule
import time
from datetime import datetime
from bot import movie_poster
import logging

async def run_scheduled_task(task_function, task_name):
    """Run a scheduled task with error handling"""
    try:
        logging.info(f"🕒 Running scheduled task: {task_name}")
        await task_function()
        logging.info(f"✅ Completed: {task_name}")
    except Exception as e:
        logging.error(f"❌ Error in {task_name}: {e}")

def schedule_tasks():
    """Schedule all automatic posting tasks"""
    
    # Daily comprehensive update at 10:00 AM
    schedule.every().day.at("10:00").do(
        lambda: asyncio.create_task(run_scheduled_task(movie_poster.post_daily_update, "Daily Update"))
    )
    
    # Latest movies every 6 hours
    schedule.every(6).hours.do(
        lambda: asyncio.create_task(run_scheduled_task(movie_poster.post_latest_movies, "Latest Movies"))
    )
    
    # Trending movies every 12 hours
    schedule.every(12).hours.do(
        lambda: asyncio.create_task(run_scheduled_task(movie_poster.post_trending_movies, "Trending Movies"))
    )
    
    # Upcoming movies once per day at 14:00
    schedule.every().day.at("14:00").do(
        lambda: asyncio.create_task(run_scheduled_task(movie_poster.post_upcoming_movies, "Upcoming Movies"))
    )

async def main():
    """Main function to run the scheduler"""
    logging.info("🤖 Starting Movie Auto-Poster Bot...")
    
    # Schedule all tasks
    schedule_tasks()
    
    # Run immediately on startup (optional)
    logging.info("🚀 Running initial posts...")
    await movie_poster.post_daily_update()
    await asyncio.sleep(10)
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)  # Check every minute

if __name__ == '__main__':
    asyncio.run(main())
