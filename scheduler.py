import os
import asyncio
import logging
from datetime import datetime
from bot import movie_poster, POST_INTERVAL

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def main():
    """Main scheduler - checks every 30 minutes for new movies"""
    logging.info("🤖 Movie Auto-Poster Bot Starting...")
    
    # Validate environment
    if not all([os.getenv('BOT_TOKEN'), os.getenv('TMDB_API_KEY'), os.getenv('CHANNEL_USERNAME')]):
        logging.error("❌ Missing environment variables")
        return
    
    # Test connections
    if not await movie_poster.test_bot_connection():
        return
    
    # Send startup message
    await movie_poster.post_to_channel(
        f"🚀 <b>Movie Updates Bot Started!</b>\n"
        f"⏰ Auto-checking for new movies every {POST_INTERVAL} minutes\n"
        f"🎬 Posts include: Title, Genre, Release Date, Rating, Overview\n"
        f"🔘 With inline buttons to your bot!"
    )
    
    logging.info(f"✅ Bot started - Checking every {POST_INTERVAL} minutes")
    
    check_count = 0
    while True:
        try:
            check_count += 1
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logging.info(f"🔄 Check #{check_count} at {current_time}")
            
            # Check and post new movies
            success = await movie_poster.post_new_movies()
            
            if success:
                logging.info(f"✅ Check #{check_count} - New movies posted")
            else:
                logging.info(f"ℹ️ Check #{check_count} - No new movies")
            
            # Wait for next check (30 minutes)
            logging.info(f"⏰ Next check in {POST_INTERVAL} minutes...")
            await asyncio.sleep(POST_INTERVAL * 60)
            
        except Exception as e:
            logging.error(f"💥 Error in check #{check_count}: {e}")
            logging.info("🔄 Retrying in 5 minutes...")
            await asyncio.sleep(300)  # 5 minutes

if __name__ == '__main__':
    asyncio.run(main())
