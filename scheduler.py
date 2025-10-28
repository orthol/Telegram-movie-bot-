import os
import asyncio
import logging
from datetime import datetime, time
from bot import movie_poster

async def main():
    """Main scheduler loop with immediate posting"""
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
        startup_msg = f"🚀 Movie Bot Started Successfully!\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n📅 Testing: Posting every minute"
        success = await movie_poster.post_to_channel(startup_msg)
        if success:
            logging.info("✅ Startup message sent")
        else:
            logging.error("❌ Failed to send startup message")
    except Exception as e:
        logging.error(f"❌ Could not send startup message: {e}")
    
    logging.info("⏰ Starting 1-minute interval posting...")
    
    # Counter to rotate through different movie types
    post_counter = 0
    
    # Main scheduler loop - post every minute
    while True:
        try:
            current_time = datetime.now()
            logging.info(f"🕒 Posting cycle #{post_counter + 1} at {current_time.strftime('%H:%M:%S')}")
            
            # Rotate through different movie types
            if post_counter % 4 == 0:
                logging.info("🎬 Posting: Latest Movies")
                await movie_poster.post_latest_movies()
            elif post_counter % 4 == 1:
                logging.info("🔥 Posting: Trending Movies")
                await movie_poster.post_trending_movies()
            elif post_counter % 4 == 2:
                logging.info("📅 Posting: Upcoming Movies")
                await movie_poster.post_upcoming_movies()
            else:
                logging.info("📊 Posting: Daily Update")
                await movie_poster.post_daily_update()
            
            post_counter += 1
            logging.info(f"✅ Completed posting cycle #{post_counter}")
            logging.info("⏰ Waiting 60 seconds for next post...")
            
            # Wait for 60 seconds before next post
            await asyncio.sleep(60)
            
        except Exception as e:
            logging.error(f"❌ Error in posting cycle: {e}")
            logging.info("⏰ Retrying in 60 seconds...")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
