import os
import telebot
import requests
from flask import Flask, request

# Initialize Flask app
app = Flask(__name__)

# Retrieve environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Webhook URL for your bot

# Initialize the TeleBot
bot = telebot.TeleBot(BOT_TOKEN)

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

    cast_html = ''.join([
        f"<div><img src='https://image.tmdb.org/t/p/w185{cast.get('profile_path')}' alt='{cast['name']}'><p>{cast['name']}</p></div>"
        for cast in movie_data.get('credits', {}).get('cast', [])[:4]
    ])
    recommendations_html = ''.join([
        f"<div><img src='https://image.tmdb.org/t/p/w185{rec.get('poster_path')}' alt='{rec['title']}'><p>{rec['title']}</p></div>"
        for rec in movie_data.get('recommendations', {}).get('results', [])[:4]
    ])

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{title} - Movie Details</title>
    </head>
    <body>
        <h1>{title}</h1>
        <p>{overview}</p>
        <p>Rating: {rating}</p>
        <img src="{poster_url}" alt="{title} poster">
        <h2>Cast</h2>
        {cast_html}
        <h2>Recommended Movies</h2>
        {recommendations_html}
        <a href="{download_link}" download><button>Download</button></a>
    </body>
    </html>
    """

# Command handler for `/movie`
@bot.message_handler(commands=['movie'])
def send_movie_details(message):
    bot.send_message(message.chat.id, "Please enter the movie name:")
    bot.register_next_step_handler(message, process_movie_name)

# Process movie name
def process_movie_name(message):
    movie_name = message.text
    bot.send_message(message.chat.id, "Please enter the download link:")
    bot.register_next_step_handler(message, process_download_link, movie_name)

# Process download link
def process_download_link(message, movie_name):
    download_link = message.text
    movie_data = fetch_movie_details(movie_name)

    if movie_data:
        html_content = generate_html(movie_data, download_link)
        filename = f"{movie_name.replace(' ', '_')}_details.html"
        
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(html_content)

        with open(filename, 'rb') as file:
            bot.send_document(message.chat.id, file)
        os.remove(filename)
    else:
        bot.send_message(message.chat.id, "Sorry, I couldn't find any details for that movie.")

# Webhook route to handle updates
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

# Set webhook route
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}/{BOT_TOKEN}"
    response = requests.get(url)
    return response.json()

# Start Flask app on port 8080
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)