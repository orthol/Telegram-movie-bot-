import os
import logging
import requests
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
BOT_USERNAME = "@halowbot"  # Your bot username
POST_INTERVAL = 30  # minutes

# Genre mapping from TMDB
GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV",
    53: "Thriller", 10752: "War", 37: "Western"
}

class MoviePoster:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
        self.posted_movies = set()  # Track already posted movies
        logging.info("✅ MoviePoster initialized")
        
    async def test_bot_connection(self):
        """Test bot connection"""
        try:
            me = await self.bot.get_me()
            logging.info(f"✅ Bot connected: @{me.username}")
            return True
        except Exception as e:
            logging.error(f"❌ Bot connection failed: {e}")
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
            return None
        except Exception as e:
            logging.error(f"❌ TMDB API Error: {e}")
            return None

    def get_genres(self, genre_ids):
        """Convert genre IDs to names"""
        genres = [GENRE_MAP.get(gid, "") for gid in genre_ids]
        return " • ".join([g for g in genres if g])

    def format_movie_post(self, movie):
        """Format movie data with genres and inline button"""
        title = movie.get('title', 'N/A')
        release_date = movie.get('release_date', 'TBA')
        rating = movie.get('vote_average', 'N/A')
        overview = movie.get('overview', 'No description available.')
        genre_ids = movie.get('genre_ids', [])
        
        # Get genres
        genres = self.get_genres(genre_ids)
        if not genres:
            genres = "Movie"
            
        # Truncate overview
        if len(overview) > 250:
            overview = overview[:250] + "..."
            
        # Create message
        message = f"""
🎬 <b>{title}</b>

🗂️ <b>Genre:</b> {genres}
🗓️ <b>Release Date:</b> {release_date}
⭐ <b>Rating:</b> {rating}/10

📄 <b>Overview:</b>
{overview}
"""
        
        # Create inline keyboard
        keyboard = [
            [InlineKeyboardButton("🎥 Get Movie", url=f"https://t.me/{BOT_USERNAME[1:]}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        poster_path = movie.get('poster_path')
        poster_url = f"{self.image_base_url}{poster_path}" if poster_path else None
        
        return message, poster_url, reply_markup

    async def post_to_channel(self, message, poster_url=None, reply_markup=None):
        """Post to channel with retry logic"""
        try:
            if poster_url:
                await self.bot.send_photo(
                    chat_id=CHANNEL_USERNAME,
                    photo=poster_url,
                    caption=message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                await self.bot.send_message(
                    chat_id=CHANNEL_USERNAME,
                    text=message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            return True
        except Exception as e:
            logging.error(f"❌ Post failed: {e}")
            return False

    async def get_new_movies(self):
        """Get only new movies that haven't been posted yet"""
        endpoints = [
            ("movie/now_playing", "🎬 Now in Cinemas"),
            ("movie/popular", "🔥 Popular Now"),
            ("trending/movie/week", "📈 Trending This Week"),
            ("movie/upcoming", "🗓️ Coming Soon")
        ]
        
        new_movies = []
        
        for endpoint, category in endpoints:
            data = self.get_movies(endpoint)
            if data and data.get('results'):
                movies = data['results']
                
                for movie in movies:
                    movie_id = movie.get('id')
                    title = movie.get('title', '')
                    
                    # Check if we haven't posted this movie and it has a poster
                    if (movie_id not in self.posted_movies and 
                        movie.get('poster_path') and 
                        title):
                        
                        new_movies.append((movie, category))
                        self.posted_movies.add(movie_id)
                        
                        # Limit to 8 new movies per check
                        if len(new_movies) >= 8:
                            return new_movies
        
        return new_movies

    async def post_new_movies(self):
        """Post 3-4 new movies if available"""
        logging.info("🔍 Checking for new movies...")
        
        new_movies = await self.get_new_movies()
        
        if not new_movies:
            logging.info("ℹ️ No new movies found")
            return False
        
        # Post 3-4 movies max
        movies_to_post = new_movies[:4]
        success_count = 0
        
        logging.info(f"📤 Found {len(movies_to_post)} new movies to post")
        
        for movie_data, category in movies_to_post:
            message, poster_url, reply_markup = self.format_movie_post(movie_data)
            message = f"🏷️ <b>{category}</b>\n" + message
            
            success = await self.post_to_channel(message, poster_url, reply_markup)
            if success:
                success_count += 1
                logging.info(f"✅ Posted: {movie_data.get('title')}")
                await asyncio.sleep(2)  # Small delay between posts
        
        logging.info(f"🎉 Posted {success_count} new movies")
        return success_count > 0

# Global instance
movie_poster = MoviePoster()
