import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

class MovieBot:
    def __init__(self):
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
        
    async def start(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        welcome_text = f"""
🎬 Welcome to Movie Updates Bot, {user.first_name}!

Available Commands:
/start - Show this welcome message
/latest - Get latest movie updates
/trending - Trending movies this week
/upcoming - Upcoming movies
/search <movie_name> - Search for a specific movie
"""
        
        keyboard = [
            [InlineKeyboardButton("🎯 Latest Movies", callback_data="latest")],
            [InlineKeyboardButton("🔥 Trending", callback_data="trending")],
            [InlineKeyboardButton("📅 Upcoming", callback_data="upcoming")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    def get_movies(self, endpoint, params=None):
        url = f"{self.tmdb_base_url}/{endpoint}"
        default_params = {'api_key': TMDB_API_KEY, 'language': 'en-US'}
        if params:
            default_params.update(params)
            
        try:
            response = requests.get(url, params=default_params)
            return response.json()
        except:
            return None

    def format_movie_message(self, movie):
        title = movie.get('title', 'N/A')
        release_date = movie.get('release_date', 'TBA')
        rating = movie.get('vote_average', 'N/A')
        overview = movie.get('overview', 'No description available.')
        
        if len(overview) > 400:
            overview = overview[:400] + "..."
            
        message = f"""
🎬 <b>{title}</b>

📅 <b>Release Date:</b> {release_date}
⭐ <b>Rating:</b> {rating}/10

📖 <b>Description:</b>
{overview}
"""
        
        poster_path = movie.get('poster_path')
        if poster_path:
            return message, f"{self.image_base_url}{poster_path}"
        
        return message, None

    async def send_latest_movies(self, update: Update, context: CallbackContext):
        query = update.callback_query
        if query:
            await query.answer()
            chat_id = query.message.chat_id
        else:
            chat_id = update.message.chat_id

        await context.bot.send_chat_action(chat_id, action='typing')
        
        data = self.get_movies("movie/now_playing", {'page': 1})
        
        if not data or 'results' not in data:
            await context.bot.send_message(chat_id, "❌ Could not fetch movies. Try again later.")
            return

        movies = data['results'][:3]
        
        for movie in movies:
            message, poster_url = self.format_movie_message(movie)
            
            if poster_url:
                try:
                    await context.bot.send_photo(chat_id=chat_id, photo=poster_url, caption=message, parse_mode='HTML')
                except:
                    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
            else:
                await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

    async def send_trending_movies(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        await context.bot.send_chat_action(query.message.chat_id, action='typing')
        
        data = self.get_movies("trending/movie/week")
        
        if not data or 'results' not in data:
            await context.bot.send_message(query.message.chat_id, "❌ Could not fetch movies. Try again later.")
            return

        movies = data['results'][:3]
        
        for movie in movies:
            message, poster_url = self.format_movie_message(movie)
            
            if poster_url:
                try:
                    await context.bot.send_photo(chat_id=query.message.chat_id, photo=poster_url, caption=message, parse_mode='HTML')
                except:
                    await context.bot.send_message(query.message.chat_id, text=message, parse_mode='HTML')
            else:
                await context.bot.send_message(query.message.chat_id, text=message, parse_mode='HTML')

    async def send_upcoming_movies(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        await context.bot.send_chat_action(query.message.chat_id, action='typing')
        
        data = self.get_movies("movie/upcoming")
        
        if not data or 'results' not in data:
            await context.bot.send_message(query.message.chat_id, "❌ Could not fetch movies. Try again later.")
            return

        movies = data['results'][:3]
        
        for movie in movies:
            message, poster_url = self.format_movie_message(movie)
            
            if poster_url:
                try:
                    await context.bot.send_photo(chat_id=query.message.chat_id, photo=poster_url, caption=message, parse_mode='HTML')
                except:
                    await context.bot.send_message(query.message.chat_id, text=message, parse_mode='HTML')
            else:
                await context.bot.send_message(query.message.chat_id, text=message, parse_mode='HTML')

    async def search_movie(self, update: Update, context: CallbackContext):
        if not context.args:
            await update.message.reply_text("Please provide a movie name. Example: /search Avengers")
            return

        movie_name = " ".join(context.args)
        await context.bot.send_chat_action(update.message.chat_id, action='typing')
        
        data = self.get_movies("search/movie", {'query': movie_name})
        
        if not data or 'results' not in data or not data['results']:
            await update.message.reply_text(f"No movies found for '{movie_name}'")
            return

        movie = data['results'][0]
        message, poster_url = self.format_movie_message(movie)
        
        if poster_url:
            try:
                await update.message.reply_photo(photo=poster_url, caption=message, parse_mode='HTML')
            except:
                await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text(message, parse_mode='HTML')

    async def button_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        await query.answer()
        
        if query.data == "latest":
            await self.send_latest_movies(update, context)
        elif query.data == "trending":
            await self.send_trending_movies(update, context)
        elif query.data == "upcoming":
            await self.send_upcoming_movies(update, context)

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        help_text = """
🤖 Movie Bot Commands:
/start - Start the bot
/latest - Latest movie releases  
/trending - Trending movies
/upcoming - Upcoming movies
/search <movie> - Search movies
/help - This message
"""
        await update.message.reply_text(help_text)

def main():
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create bot instance
    movie_bot = MovieBot()
    
    # Add handlers
    application.add_handler(CommandHandler("start", movie_bot.start))
    application.add_handler(CommandHandler("latest", movie_bot.send_latest_movies))
    application.add_handler(CommandHandler("trending", movie_bot.send_trending_movies))
    application.add_handler(CommandHandler("upcoming", movie_bot.send_upcoming_movies))
    application.add_handler(CommandHandler("search", movie_bot.search_movie))
    application.add_handler(CommandHandler("help", movie_bot.help_command))
    application.add_handler(CallbackQueryHandler(movie_bot.button_handler))

    # Start polling
    print("🤖 Movie Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
