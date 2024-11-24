import os
import telebot
import requests
from flask import Flask, request

# Create a Flask app
app = Flask(__name__)

# Replace with your bot token from Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Replace with your webhook URL (for deployment)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Initialize the TeleBot
bot = telebot.TeleBot(BOT_TOKEN)

# Global variables for managing movie data and links
movie_data = None
collected_links = []

# Function to fetch movie details
def fetch_movie_details(movie_name):
    # Simulating TMDB API for movie data
    return {
        "title": movie_name,
        "overview": f"Details about the movie {movie_name}",
        "poster_path": "/sample_poster.jpg",
        "vote_average": 8.5
    }

# Function to generate HTML
def generate_html(movie_data, links):
    title = movie_data.get('title', 'Unknown Title')
    overview = movie_data.get('overview', 'No description available.')
    rating = movie_data.get('vote_average', 'N/A')
    poster_path = movie_data.get('poster_path')
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ''

    links_html = ''
    for link in links:
        links_html += f'<a href="{link}" target="_blank"><button class="link-button">{link}</button></a><br>'

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Movie Details</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; }}
            .movie-container {{ max-width: 800px; margin: 50px auto; padding: 20px; background-color: #fff; border-radius: 8px; }}
            h1 {{ color: #2a9df4; }}
            .overview {{ color: #333; }}
            .rating {{ font-size: 20px; color: #ffd700; }}
            .link-button {{
                display: inline-block;
                margin: 10px;
                padding: 10px 20px;
                font-size: 16px;
                color: #fff;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                cursor: pointer;
            }}
            .link-button:hover {{ background-color: #0056b3; }}
        </style>
    </head>
    <body>
        <div class="movie-container">
            <h1>{title}</h1>
            <p class="overview">{overview}</p>
            <p>Rating: <span class="rating">{rating}</span></p>
            <img src="{poster_url}" alt="{title} Poster" style="max-width:200px; border-radius:10px;">
            <h2>Links</h2>
            {links_html}
        </div>
    </body>
    </html>
    """
    return html_content

# Command `/web` to start collecting links
@bot.message_handler(commands=['web'])
def start_collecting_links(message):
    global collected_links
    collected_links = []  # Reset links for a new session
    bot.send_message(message.chat.id, "Please enter the movie name:")
    bot.register_next_step_handler(message, process_movie_name)

# Process the movie name and prompt for links
def process_movie_name(message):
    global movie_data
    movie_name = message.text
    movie_data = fetch_movie_details(movie_name)
    if movie_data:
        bot.send_message(message.chat.id, "Now, send the links (one at a time). Send `/end` when you're done.")
    else:
        bot.send_message(message.chat.id, "Could not fetch movie details. Please try again.")

# Collect all links
@bot.message_handler(func=lambda message: message.text != '/end')
def collect_links(message):
    global collected_links
    collected_links.append(message.text)
    bot.send_message(message.chat.id, f"Link added: {message.text}\nSend another link or type `/end` to finish.")

# Generate the final HTML on `/end`
@bot.message_handler(commands=['end'])
def finalize_and_send_html(message):
    global collected_links, movie_data

    if not movie_data:
        bot.send_message(message.chat.id, "No movie details available. Please start with /web.")
        return

    if not collected_links:
        bot.send_message(message.chat.id, "No links collected. Please add links before finalizing.")
        return

    html_content = generate_html(movie_data, collected_links)
    filename = f"{movie_data['title'].replace(' ', '_')}_details.html"

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)

    with open(filename, 'rb') as file:
        bot.send_document(message.chat.id, file)

    os.remove(filename)
    bot.send_message(message.chat.id, "HTML file generated and sent successfully!")

# Webhook route
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# Set webhook
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}/{BOT_TOKEN}")
    return response.json()

# Start Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))