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
            response = requests.get(url, params=default_params)
            return response.json()
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

#MovieUpdate #NewRelease #{category.replace(' ', '')}
"""
        
        poster_path = movie.get('poster_path')
        if poster_path:
            return message, f"{self.image_base_url}{poster_path}"
        
        return message, None

    async def post_latest_movies(self):
        """Post latest movies to channel"""
        try:
            data = self.get_movies("movie/now_playing", {'page': 1})
            
            if not data or 'results' not in data:
                logging.error("Could not fetch latest movies")
                return

            movies = data['results'][:2]
            
            for movie in movies:
                message, poster_url = self.format_movie_post(movie, "Latest Releases")
                
                if poster_url:
                    try:
                        await self.bot.send_photo(
                            chat_id=CHANNEL_USERNAME,
                            photo=poster_url,
                            caption=message,
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logging.error(f"Error sending photo: {e}")
                        await self.bot.send_message(
                            chat_id=CHANNEL_USERNAME,
                            text=message,
                            parse_mode='HTML'
                        )
                else:
                    await self.bot.send_message(
                        chat_id=CHANNEL_USERNAME,
                        text=message,
                        parse_mode='HTML'
                    )
                
                await asyncio.sleep(5)
                
            logging.info("✅ Latest movies posted successfully")
            
        except Exception as e:
            logging.error(f"Error posting latest movies: {e}")

    async def post_trending_movies(self):
        """Post trending movies to channel"""
        try:
            data = self.get_movies("trending/movie/week")
            
            if not data or 'results' not in data:
                logging.error("Could not fetch trending movies")
                return

            movies = data['results'][:2]
            
            for movie in movies:
                message, poster_url = self.format_movie_post(movie, "Trending Now")
                
                if poster_url:
                    try:
                        await self.bot.send_photo(
                            chat_id=CHANNEL_USERNAME,
                            photo=poster_url,
                            caption=message,
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logging.error(f"Error sending photo: {e}")
                        await self.bot.send_message(
                            chat_id=CHANNEL_USERNAME,
                            text=message,
                            parse_mode='HTML'
                        )
                else:
                    await self.bot.send_message(
                        chat_id=CHANNEL_USERNAME,
                        text=message,
                        parse_mode='HTML'
                    )
                
                await asyncio.sleep(5)
                
            logging.info("✅ Trending movies posted successfully")
            
        except Exception as e:
            logging.error(f"Error posting trending movies: {e}")

    async def post_upcoming_movies(self):
        """Post upcoming movies to channel"""
        try:
            data = self.get_movies("movie/upcoming")
            
            if not data or 'results' not in data:
                logging.error("Could not fetch upcoming movies")
                return

            movies = data['results'][:2]
            
            for movie in movies:
                message, poster_url = self.format_movie_post(movie, "Coming Soon")
                
                if poster_url:
                    try:
                        await self.bot.send_photo(
                            chat_id=CHANNEL_USERNAME,
                            photo=poster_url,
                            caption=message,
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logging.error(f"Error sending photo: {e}")
                        await self.bot.send_message(
                            chat_id=CHANNEL_USERNAME,
                            text=message,
                            parse_mode='HTML'
                        )
                else:
                    await self.bot.send_message(
                        chat_id=CHANNEL_USERNAME,
                        text=message,
                        parse_mode='HTML'
                    )
                
                await asyncio.sleep(5)
                
            logging.info("✅ Upcoming movies posted successfully")
            
        except Exception as e:
            logging.error(f"Error posting upcoming movies: {e}")

    async def post_daily_update(self):
        """Post daily movie update with mixed content"""
        try:
            # Send header message
            header = f"🎬 <b>Daily Movie Update</b> 🎬\n📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
            await self.bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=header,
                parse_mode='HTML'
            )
            
            await asyncio.sleep(2)
            
            # Post 1 latest movie
            latest_data = self.get_movies("movie/now_playing", {'page': 1})
            if latest_data and 'results' in latest_data and latest_data['results']:
                movie = latest_data['results'][0]
                message, poster_url = self.format_movie_post(movie, "Latest Release")
                if poster_url:
                    try:
                        await self.bot.send_photo(CHANNEL_USERNAME, photo=poster_url, caption=message, parse_mode='HTML')
                    except:
                        await self.bot.send_message(CHANNEL_USERNAME, text=message, parse_mode='HTML')
                await asyncio.sleep(3)
            
            # Post 1 trending movie
            trending_data = self.get_movies("trending/movie/week")
            if trending_data and 'results' in trending_data and trending_data['results']:
                movie = trending_data['results'][0]
                message, poster_url = self.format_movie_post(movie, "Trending Now")
                if poster_url:
                    try:
                        await self.bot.send_photo(CHANNEL_USERNAME, photo=poster_url, caption=message, parse_mode='HTML')
                    except:
                        await self.bot.send_message(CHANNEL_USERNAME, text=message, parse_mode='HTML')
                await asyncio.sleep(3)
            
            # Post 1 upcoming movie
            upcoming_data = self.get_movies("movie/upcoming")
            if upcoming_data and 'results' in upcoming_data and upcoming_data['results']:
                movie = upcoming_data['results'][0]
                message, poster_url = self.format_movie_post(movie, "Coming Soon")
                if poster_url:
                    try:
                        await self.bot.send_photo(CHANNEL_USERNAME, photo=poster_url, caption=message, parse_mode='HTML')
                    except:
                        await self.bot.send_message(CHANNEL_USERNAME, text=message, parse_mode='HTML')
            
            logging.info("✅ Daily update posted successfully")
            
        except Exception as e:
            logging.error(f"Error posting daily update: {e}")

# Global instance
movie_poster = MoviePoster()
