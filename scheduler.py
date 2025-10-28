import os
import asyncio
import logging
from datetime import datetime
from bot import movie_poster

async def safe_post(operation, operation_name):
    """Safely execute a posting operation with error handling"""
    try:
        logging.info(f"🔄 Attempting: {operation_name}")
        success = await operation()
        if success:
            logging.info(f"✅ Success: {operation_name}")
        else:
            logging.error(f"❌ Failed: {operation_name}")
        return True  # Continue running even if post fails
    except Exception as e:
        logging.error(f"💥 CRITICAL ERROR in {operation_name}: {e}")
        logging.error("🔄 Continuing to next cycle despite error...")
        return True  # Always continue

async def main():
    """Main scheduler loop with robust error handling"""
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
    try:
        connection_ok = await movie_poster.test_bot_connection()
        if not connection_ok:
            logging.error("❌ Bot connection test failed. Please check BOT_TOKEN.")
            return
    except Exception as e:
        logging.error(f"❌ Bot connection test error: {e}")
        return
    
    # Test TMDB API connection
    logging.info("🔌 Testing TMDB API connection...")
    try:
        api_ok = await movie_poster.test_api_connection()
        if not api_ok:
            logging.error("❌ TMDB API test failed. Please check TMDB_API_KEY.")
            return
    except Exception as e:
        logging.error(f"❌ TMDB API test error: {e}")
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
            logging.info(f"🔄 ===== POSTING CYCLE #{post_counter + 1} at {current_time.strftime('%H:%M:%S')} =====")
            
            # Rotate through different movie types with safe execution
            if post_counter % 4 == 0:
                await safe_post(movie_poster.post_latest_movies, "Latest Movies")
            elif post_counter % 4 == 1:
                await safe_post(movie_poster.post_trending_movies, "Trending Movies")
            elif post_counter % 4 == 2:
                await safe_post(movie_poster.post_upcoming_movies, "Upcoming Movies")
            else:
                await safe_post(movie_poster.post_daily_update, "Daily Update")
            
            post_counter += 1
            logging.info(f"✅ Completed posting cycle #{post_counter}")
            logging.info(f"⏰ Next cycle in 60 seconds... (Will be cycle #{post_counter + 1})")
            
            # Wait for 60 seconds before next post
            await asyncio.sleep(60)
            
        except Exception as e:
            logging.error(f"💥 MAIN LOOP ERROR: {e}")
            logging.info("🔄 Restarting main loop in 60 seconds...")
            await asyncio.sleep(60)

if __name__ == '__main__':
    # Add global exception handler
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Bot stopped by user")
    except Exception as e:
        logging.error(f"💥 GLOBAL ERROR: {e}")
        logging.info("🔄 Restarting bot...")
        # You could add auto-restart logic here if needed
