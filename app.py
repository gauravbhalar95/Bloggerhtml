import os
import telebot
import requests
from flask import Flask, request

# Create a Flask app
app = Flask(__name__)

# Replace with your bot token from Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Replace with your TMDB API key
TMDB_API_KEY = os.getenv('TMDB')
# The URL for webhook (replace with your actual Koyeb URL)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Initialize the TeleBot
bot = telebot.TeleBot(BOT_TOKEN)

# Global variables for managing download links
movie_data = None
download_links = []

# Function to fetch movie details from TMDB
def fetch_movie_details(movie_name):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching movie details: {response.status_code} - {response.text}")
        return None

    data = response.json()
    if data['results']:
        movie = data['results'][0]
        movie_id = movie['id']
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,recommendations"
        details_response = requests.get(details_url)
        if details_response.status_code != 200:
            print(f"Error fetching movie details: {details_response.status_code} - {details_response.text}")
            return None

        return details_response.json()
    return None

# Function to generate HTML content
def generate_html(movie_data, download_links):
    title = movie_data.get('title', 'Unknown Title')
    overview = movie_data.get('overview', 'No description available.')
    rating = movie_data.get('vote_average', 'N/A')
    poster_path = movie_data.get('poster_path')
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ''

    # HTML for download links
    links_html = ''
    for link in download_links:
        links_html += f'<a href="{link}" download><button class="download-button">{link}</button></a><br>'

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
            .download-button {{
                margin: 10px;
                padding: 10px 20px;
                font-size: 16px;
                color: #fff;
                background-color: #28a745;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div id="movie-container">
            <h1>{title}</h1>
            <p>{overview}</p>
            <p>Rating: <span class="rating">{rating}</span></p>
            <img src="{poster_url}" alt="{title} poster" style="width:200px; border-radius:8px;">
            <h2>Download Links</h2>
            {links_html}
        </div>
    </body>
    </html>
    """
    return html_content

# Command handler for `/web`
@bot.message_handler(commands=['web'])
def start_collecting_links(message):
    global download_links
    download_links = []  # Reset the list for new session
    bot.send_message(message.chat.id, "Please enter the name of the movie:")
    bot.register_next_step_handler(message, process_movie_name)

# Process the movie name
def process_movie_name(message):
    global movie_data
    movie_name = message.text
    movie_data = fetch_movie_details(movie_name)

    if movie_data:
        bot.send_message(message.chat.id, "Now, please enter the download links one by one. Send `/end` to finish.")
    else:
        bot.send_message(message.chat.id, "Sorry, I couldn't find any details for that movie. Please try again.")

# Collect download links
@bot.message_handler(func=lambda message: message.text != '/end')
def collect_links(message):
    global download_links
    download_links.append(message.text)
    bot.send_message(message.chat.id, "Download link added! Send another link or `/end` to finish.")

# Finalize and generate HTML
@bot.message_handler(commands=['end'])
def finalize_html(message):
    if not movie_data:
        bot.send_message(message.chat.id, "No movie data found. Please start with /web.")
        return

    if not download_links:
        bot.send_message(message.chat.id, "No download links provided. Please add links before ending.")
        return

    html_content = generate_html(movie_data, download_links)
    filename = f"{movie_data['title'].replace(' ', '_')}_details.html"

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)

    with open(filename, 'rb') as file:
        bot.send_document(message.chat.id, file)

    os.remove(filename)

# Webhook route to handle incoming updates
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# Set up webhook
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}/{BOT_TOKEN}')
    return response.json()

# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))