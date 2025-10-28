import os
import logging
import requests
import asyncio
from telegram import Bot
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
        self.bot = Bot(token=BOT_TOKEN)
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
        
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
                logging.error(f"API returned status code: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"API Error: {e}")
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

    async def post_to_channel(self, message, poster_url=None):
        """Helper function to post to channel"""
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
        except Exception as e:
            logging.error(f"Error posting to channel: {e}")
            return False

    async def post_latest_movies(self):
        """Post latest movies to channel"""
        logging.info("📤 Posting latest movies...")
        data = self.get_movies("movie/now_playing", {'page': 1})
        
        if not data or 'results' not in data or not data['results']:
            logging.error("❌ No latest movies found")
            return

        movies = data['results'][:2]  # Post 2 latest movies
        
        for movie in movies:
            message, poster_url = self.format_movie_post(movie, "Latest Releases")
            success = await self.post_to_channel(message, poster_url)
            if success:
                await asyncio.sleep(5)  # Delay between posts

    async def post_trending_movies(self):
        """Post trending movies to channel"""
        logging.info("📤 Posting trending movies...")
        data = self.get_movies("trending/movie/week")
        
        if not data or 'results' not in data or not data['results']:
            logging.error("❌ No trending movies found")
            return

        movies = data['results'][:2]
        
        for movie in movies:
            message, poster_url = self.format_movie_post(movie, "Trending Now")
            success = await self.post_to_channel(message, poster_url)
            if success:
                await asyncio.sleep(5)

    async def post_upcoming_movies(self):
        """Post upcoming movies to channel"""
        logging.info("📤 Posting upcoming movies...")
        data = self.get_movies("movie/upcoming")
        
        if not data or 'results' not in data or not data['results']:
            logging.error("❌ No upcoming movies found")
            return

        movies = data['results'][:2]
        
        for movie in movies:
            message, poster_url = self.format_movie_post(movie, "Coming Soon")
            success = await self.post_to_channel(message, poster_url)
            if success:
                await asyncio.sleep(5)

    async def post_daily_update(self):
        """Post daily movie update"""
        logging.info("📤 Posting daily update...")
        try:
            header = f"🎬 <b>Daily Movie Update</b> 🎬\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            await self.post_to_channel(header)
            await asyncio.sleep(2)
            
            # Post one from each category
            categories = [
                ("movie/now_playing", "Latest Release"),
                ("trending/movie/week", "Trending Now"), 
                ("movie/upcoming", "Coming Soon")
            ]
            
            for endpoint, category in categories:
                data = self.get_movies(endpoint)
                if data and data.get('results'):
                    movie = data['results'][0]
                    message, poster_url = self.format_movie_post(movie, category)
                    await self.post_to_channel(message, poster_url)
                    await asyncio.sleep(3)
                    
        except Exception as e:
            logging.error(f"❌ Error in daily update: {e}")

# Global instance
movie_poster = MoviePoster()
