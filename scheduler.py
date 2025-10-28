import os
import asyncio
import logging
from datetime import datetime, time
from bot import movie_poster

async def main():
    """Main scheduler loop with manual time checking"""
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
    
    # Test TMDB API connection
    logging.info("🔌 Testing TMDB API connection...")
    api_ok = await movie_poster.test_api_connection()
    if not api_ok:
        logging.error("❌ TMDB API test failed. Please check TMDB_API_KEY.")
        return
    
    # Send startup message
    try:
        startup_msg = f"🚀 Movie Bot Started Successfully!\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n📅 Auto-posting: 9AM, 12PM, 3PM, 6PM daily\n✅ Both Telegram & TMDB API connected!"
        success = await movie_poster.post_to_channel(startup_msg)
        if success:
            logging.info("✅ Startup message sent")
        else:
            logging.error("❌ Failed to send startup message")
    except Exception as e:
        logging.error(f"❌ Could not send startup message: {e}")
    
    # Track last run times to avoid duplicates
    last_run = {
        'daily_update': None,
        'latest_movies': None,
        'trending_movies': None,
        'upcoming_movies': None
    }
    
    logging.info("⏰ Starting 24/7 scheduler loop...")
    
    # Main scheduler loop
    while True:
        try:
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute
            
            # Schedule configuration (24-hour format)
            schedule_times = {
                'daily_update': time(9, 0),    # 9:00 AM
                'latest_movies': time(12, 0),  # 12:00 PM
                'trending_movies': time(15, 0), # 3:00 PM
                'upcoming_movies': time(18, 0) # 6:00 PM
            }
            
            # Check each scheduled task
            for task_name, scheduled_time in schedule_times.items():
                # Check if it's the right time and we haven't run it recently
                if (current_hour == scheduled_time.hour and 
                    current_minute == scheduled_time.minute and
                    (last_run.get(task_name) != current_time.date())):
                    
                    logging.info(f"🕒 Time for: {task_name}")
                    
                    # Run the appropriate task
                    if task_name == 'daily_update':
                        await movie_poster.post_daily_update()
                    elif task_name == 'latest_movies':
                        await movie_poster.post_latest_movies()
                    elif task_name == 'trending_movies':
                        await movie_poster.post_trending_movies()
                    elif task_name == 'upcoming_movies':
                        await movie_poster.post_upcoming_movies()
                    
                    # Update last run time
                    last_run[task_name] = current_time.date()
                    logging.info(f"✅ Completed: {task_name}")
            
            # Log current status every 30 minutes (optional)
            if current_minute == 0 or current_minute == 30:
                logging.info(f"📊 Bot is running... Current time: {current_time.strftime('%H:%M')}")
                logging.info(f"📅 Next posts: 9:00, 12:00, 15:00, 18:00")
            
            # Wait for 1 minute before checking again
            await asyncio.sleep(60)
            
        except Exception as e:
            logging.error(f"❌ Scheduler error: {e}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
