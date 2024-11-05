import telebot
import requests
import os
from flask import Flask, request

# Replace with your bot token from Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Replace with your TMDB API key
TMDB_API_KEY = os.getenv('TMDB')
# Get the webhook URL from the environment variable
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

bot = telebot.TeleBot(BOT_TOKEN)

# Initialize Flask app
app = Flask(__name__)

# Function to set webhook
def set_webhook():
    response = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}')
    if response.status_code == 200:
        print('Webhook set successfully!')
    else:
        print(f'Error setting webhook: {response.status_code} - {response.text}')

# Set webhook on startup
set_webhook()

# Function to fetch movie details from TMDB
def fetch_movie_details(movie_name):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None

    data = response.json()
    if data['results']:
        movie = data['results'][0]
        movie_id = movie['id']
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,recommendations"
        details_response = requests.get(details_url)
        if details_response.status_code != 200:
            print(f"Error: {details_response.status_code} - {details_response.text}")
            return None

        return details_response.json()
    return None

# Function to generate HTML content
def generate_html(movie_data, download_link):
    title = movie_data.get('title', 'Unknown Title')
    overview = movie_data.get('overview', 'No description available.')
    rating = movie_data.get('vote_average', 'N/A')
    poster_path = movie_data.get('poster_path')
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ''

    # HTML for the cast members
    cast_html = ''
    for cast in movie_data.get('credits', {}).get('cast', [])[:4]:  # Top 4 cast members
        profile_path = cast.get('profile_path')
        profile_url = f"https://image.tmdb.org/t/p/w185{profile_path}" if profile_path else ''
        cast_html += f"""
        <div class="cast-member">
            <img src="{profile_url}" alt="{cast['name']}" class="cast-photo">
            <p class="cast-name">{cast['name']}</p>
        </div>
        """

    # HTML for recommended movies
    recommendations_html = ''
    for rec in movie_data.get('recommendations', {}).get('results', [])[:4]:  # Top 4 recommendations
        rec_poster_path = rec.get('poster_path')
        rec_poster_url = f"https://image.tmdb.org/t/p/w185{rec_poster_path}" if rec_poster_path else ''
        recommendations_html += f"""
        <div class="recommendation">
            <img src="{rec_poster_url}" alt="{rec['title']}" class="recommendation-poster">
            <p class="recommendation-title">{rec['title']}</p>
        </div>
        """

    # HTML Template with Download Button
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Movie Details</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; }}
            #movie-container {{ max-width: 800px; margin: 50px auto; padding: 20px; border-radius: 8px; background-color: #fff; }}
            h1 {{ color: #ff001f; }}
            p {{ color: #1100ff; }}
            .rating {{ font-size: 24px; color: #ffd700; }}
            .cast {{ display: flex; justify-content: space-around; }}
            .cast-member {{ margin: 10px; }}
            .cast-photo {{ width: 100px; height: auto; border-radius: 8px; }}
            .recommendations {{ display: flex; justify-content: space-around; margin-top: 20px; }}
            .recommendation {{ margin: 10px; }}
            .recommendation-poster {{ width: 80px; height: auto; border-radius: 8px; }}
            .download-button {{
                margin-top: 20px;
                padding: 10px 20px;
                font-size: 18px;
                font-weight: bold;
                color: #fff;
                background-color: #ff5722;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                animation: blink 1.5s linear infinite;
            }}
            @keyframes blink {{
                0%, 100% {{ background-color: #ff5722; }}
                50% {{ background-color: #ff2200; }}
            }}
        </style>
    </head>
    <body>
        <div id="movie-container">
            <h1>{title}</h1>
            <p>{overview}</p>
            <p>Rating: <span class="rating">{rating}</span></p>
            <img src="{poster_url}" alt="{title} poster" style="width:200px; border-radius:8px;">
            <h2>Cast</h2>
            <div class="cast">{cast_html}</div>
            <h2>Recommended Movies</h2>
            <div class="recommendations">{recommendations_html}</div>
            <a href="{download_link}" download>
                <button class="download-button">Download</button>
            </a>
        </div>
    </body>
    </html>
    """
    return html_content

# Command handler for `/movie`
@bot.message_handler(commands=['movie'])
def send_movie_details(message):
    bot.send_message(message.chat.id, "Please enter the name of the movie:")
    bot.register_next_step_handler(message, process_movie_name)

# Process the movie name
def process_movie_name(message):
    movie_name = message.text
    bot.send_message(message.chat.id, "Please enter the download link for the poster:")
    bot.register_next_step_handler(message, process_download_link, movie_name)

# Process the download link
def process_download_link(message, movie_name):
    download_link = message.text
    movie_data = fetch_movie_details(movie_name)

    if movie_data:
        html_content = generate_html(movie_data, download_link)

        # Save HTML content to a file
        filename = f"{movie_name.replace(' ', '_')}_details.html"
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(html_content)

        # Send the HTML file to the user
        with open(filename, 'rb') as file:
            bot.send_document(message.chat.id, file)

        # Remove the file after sending
        os.remove(filename)
    else:
        bot.send_message(message.chat.id, "Sorry, I couldn't find any details for that movie.")

# Webhook endpoint to receive updates
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_data = request.get_json()
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return '', 200

# Start the Flask app
if __name__ == '__main__':
    app.run(port=8080)  # Change to your desired port