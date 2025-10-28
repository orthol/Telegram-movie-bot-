import os
import logging
import requests
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '@YourChannelUsername')

# Validate required environment variables
if not BOT_TOKEN:
    logging.error("❌ BOT_TOKEN environment variable is missing")
    exit(1)
if not TMDB_API_KEY:
    logging.error("❌ TMDB_API_KEY environment variable is missing")
    exit(1)
if not CHANNEL_USERNAME:
    logging.error("❌ CHANNEL_USERNAME environment variable is missing")
    exit(1)

class MoviePoster:
    def __init__(self):
        try:
            self.bot = Bot(token=BOT_TOKEN)
            self.tmdb_base_url = "https://api.themoviedb.org/3"
            self.image_base_url = "https://image.tmdb.org/t/p/w500"
            logging.info("✅ MoviePoster initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize MoviePoster: {e}")
            raise
        
    async def test_bot_connection(self):
        """Test if bot can connect to Telegram"""
        try:
            me = await self.bot.get_me()
            logging.info(f"✅ Bot connected successfully: @{me.username}")
            return True
        except TelegramError as e:
            logging.error(f"❌ Bot connection failed: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error testing bot: {e}")
            return False

    def get_movies(self, endpoint, params=None):
        """Fetch movies from TMDB API"""
        url = f"{self.tmdb_base_url}/{endpoint}"
        default_params = {'api_key': TMDB_API_KEY, 'language': 'en-US'}
        if params:
            default_params.update(params)
            
        try:
            response = requests.get(url, params=default_params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"❌ TMDB API returned status code: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"❌ TMDB API Error: {e}")
            return None

    def format_movie_post(self, movie, category="Latest"):
        """Format movie data for channel post"""
        title = movie.get('title', 'N/A')
        release_date = movie.get('release_date', 'TBA')
        rating = movie.get('vote_average', 'N/A')
        overview = movie.get('overview', 'No description available.')
        
        if len(overview) > 300:
            overview = overview[:300] + "..."
            
        message = f"""
🎬 <b>{title}</b>

📅 <b>Release Date:</b> {release_date}
⭐ <b>Rating:</b> {rating}/10
🏷️ <b>Category:</b> {category}

📖 <b>Description:</b>
{overview}

#MovieUpdate #{category.replace(' ', '')}
"""
        
        poster_path = movie.get('poster_path')
        if poster_path:
            return message, f"{self.image_base_url}{poster_path}"
        
        return message, None

    async def post_to_channel(self, message, poster_url=None, retries=3):
        """Helper function to post to channel with retries"""
        for attempt in range(retries):
            try:
                if poster_url:
                    await self.bot.send_photo(
                        chat_id=CHANNEL_USERNAME,
                        photo=poster_url,
                        caption=message,
                        parse_mode='HTML',
                        read_timeout=30,
                        write_timeout=30,
                        connect_timeout=30
                    )
                else:
                    await self.bot.send_message(
                        chat_id=CHANNEL_USERNAME,
                        text=message,
                        parse_mode='HTML',
                        read_timeout=30,
                        write_timeout=30,
                        connect_timeout=30
                    )
                logging.info(f"✅ Message posted successfully (attempt {attempt + 1})")
                return True
                
            except TelegramError as e:
                logging.warning(f"⚠️ Telegram error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)  # Wait before retry
                else:
                    logging.error(f"❌ Failed to post after {retries} attempts: {e}")
                    return False
            except Exception as e:
                logging.error(f"❌ Unexpected error posting (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                else:
                    return False
        return False

    async def post_latest_movies(self):
        """Post latest movies to channel"""
        logging.info("📤 Posting latest movies...")
        data = self.get_movies("movie/now_playing", {'page': 1})
        
        if not data or 'results' not in data or not data['results']:
            logging.error("❌ No latest movies found")
            return False

        movies = data['results'][:2]
        success_count = 0
        
        for movie in movies:
            message, poster_url = self.format_movie_post(movie, "Latest Releases")
            success = await self.post_to_channel(message, poster_url)
            if success:
                success_count += 1
                await asyncio.sleep(5)  # Delay between posts

        logging.info(f"✅ Posted {success_count}/{len(movies)} latest movies")
        return success_count > 0

    async def post_trending_movies(self):
        """Post trending movies to channel"""
        logging.info("📤 Posting trending movies...")
        data = self.get_movies("trending/movie/week")
        
        if not data or 'results' not in data or not data['results']:
            logging.error("❌ No trending movies found")
            return False

        movies = data['results'][:2]
        success_count = 0
        
        for movie in movies:
            message, poster_url = self.format_movie_post(movie, "Trending Now")
            success = await self.post_to_channel(message, poster_url)
            if success:
                success_count += 1
                await asyncio.sleep(5)

        logging.info(f"✅ Posted {success_count}/{len(movies)} trending movies")
        return success_count > 0

    async def post_upcoming_movies(self):
        """Post upcoming movies to channel"""
        logging.info("📤 Posting upcoming movies...")
        data = self.get_movies("movie/upcoming")
        
        if not data or 'results' not in data or not data['results']:
            logging.error("❌ No upcoming movies found")
            return False

        movies = data['results'][:2]
        success_count = 0
        
        for movie in movies:
            message, poster_url = self.format_movie_post(movie, "Coming Soon")
            success = await self.post_to_channel(message, poster_url)
            if success:
                success_count += 1
                await asyncio.sleep(5)

        logging.info(f"✅ Posted {success_count}/{len(movies)} upcoming movies")
        return success_count > 0

    async def post_daily_update(self):
        """Post daily movie update"""
        logging.info("📤 Posting daily update...")
        try:
            header = f"🎬 <b>Daily Movie Update</b> 🎬\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            header_success = await self.post_to_channel(header)
            
            if not header_success:
                logging.error("❌ Failed to post daily update header")
                return False
                
            await asyncio.sleep(2)
            
            # Post one from each category
            categories = [
                ("movie/now_playing", "Latest Release"),
                ("trending/movie/week", "Trending Now"), 
                ("movie/upcoming", "Coming Soon")
            ]
            
            success_count = 0
            for endpoint, category in categories:
                data = self.get_movies(endpoint)
                if data and data.get('results'):
                    movie = data['results'][0]
                    message, poster_url = self.format_movie_post(movie, category)
                    success = await self.post_to_channel(message, poster_url)
                    if success:
                        success_count += 1
                    await asyncio.sleep(3)
            
            logging.info(f"✅ Daily update completed: {success_count}/{len(categories)} posts successful")
            return success_count > 0
                    
        except Exception as e:
            logging.error(f"❌ Error in daily update: {e}")
            return False

# Global instance
try:
    movie_poster = MoviePoster()
    logging.info("🎬 Movie Poster Bot is ready!")
except Exception as e:
    logging.error(f"❌ Failed to create MoviePoster instance: {e}")
    movie_poster = None
