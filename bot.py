import os
import logging
import requests
import asyncio
import random
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
                        parse_mode='HTML'
                    )
                else:
                    await self.bot.send_message(
                        chat_id=CHANNEL_USERNAME,
                        text=message,
                        parse_mode='HTML'
                    )
                return True
                
            except TelegramError as e:
                logging.warning(f"⚠️ Telegram error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                else:
                    return False
            except Exception as e:
                logging.error(f"❌ Unexpected error posting (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                else:
                    return False
        return False

    async def get_random_movies(self, category_name):
        """Get random movies from different endpoints to ensure variety"""
        endpoints = [
            ("movie/now_playing", {}),
            ("movie/popular", {}),
            ("movie/top_rated", {}),
            ("trending/movie/week", {}),
            ("movie/upcoming", {'page': random.randint(1, 3)}),
            ("discover/movie", {'sort_by': 'popularity.desc', 'page': random.randint(1, 5)})
        ]
        
        # Try different endpoints until we find movies
        for endpoint, params in endpoints:
            data = self.get_movies(endpoint, params)
            if data and data.get('results'):
                movies = data['results']
                # Filter out movies without posters and shuffle
                movies_with_posters = [m for m in movies if m.get('poster_path')]
                if movies_with_posters:
                    selected_movies = random.sample(movies_with_posters, min(2, len(movies_with_posters)))
                    return selected_movies, category_name
        
        return [], category_name

    async def post_latest_movies(self):
        """Post latest movies to channel"""
        movies, category = await self.get_random_movies("Latest Movies")
        
        if not movies:
            logging.error("❌ No movies found")
            return False

        success_count = 0
        for movie in movies:
            message, poster_url = self.format_movie_post(movie, category)
            success = await self.post_to_channel(message, poster_url)
            if success:
                success_count += 1
            await asyncio.sleep(3)

        logging.info(f"✅ Posted {success_count}/{len(movies)} {category}")
        return success_count > 0

    async def post_trending_movies(self):
        """Post trending movies to channel"""
        movies, category = await self.get_random_movies("Trending Now")
        
        if not movies:
            logging.error("❌ No trending movies found")
            return False

        success_count = 0
        for movie in movies:
            message, poster_url = self.format_movie_post(movie, category)
            success = await self.post_to_channel(message, poster_url)
            if success:
                success_count += 1
            await asyncio.sleep(3)

        logging.info(f"✅ Posted {success_count}/{len(movies)} {category}")
        return success_count > 0

    async def post_upcoming_movies(self):
        """Post upcoming movies to channel"""
        movies, category = await self.get_random_movies("Coming Soon")
        
        if not movies:
            logging.error("❌ No upcoming movies found")
            return False

        success_count = 0
        for movie in movies:
            message, poster_url = self.format_movie_post(movie, category)
            success = await self.post_to_channel(message, poster_url)
            if success:
                success_count += 1
            await asyncio.sleep(3)

        logging.info(f"✅ Posted {success_count}/{len(movies)} {category}")
        return success_count > 0

    async def post_daily_update(self):
        """Post daily movie update with mixed content"""
        try:
            header = f"🎬 <b>Daily Movie Mix</b> 🎬\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            await self.post_to_channel(header)
            await asyncio.sleep(2)
            
            # Get random movies from different categories
            categories = ["Popular Picks", "Top Rated", "New Discoveries", "Fan Favorites"]
            random_category = random.choice(categories)
            
            movies, _ = await self.get_random_movies(random_category)
            if movies:
                for movie in movies[:2]:  # Post max 2 movies
                    message, poster_url = self.format_movie_post(movie, random_category)
                    await self.post_to_channel(message, poster_url)
                    await asyncio.sleep(3)
            
            return True
                    
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
