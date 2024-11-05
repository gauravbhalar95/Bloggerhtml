import os
import telebot
import requests
from flask import Flask, request, jsonify

# Create a Flask app
app = Flask(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
TMDB_API_KEY = os.getenv('TMDB')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Ensure this is the full URL to your Koyeb deployment

# Initialize the TeleBot
bot = telebot.TeleBot(BOT_TOKEN)

# Function to fetch movie details from TMDB
def fetch_movie_details(movie_name):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching movie: {response.status_code} - {response.text}")
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

# Webhook route to handle incoming updates
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# Route to set the webhook
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
    response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}')
    
    if response.status_code == 200:
        print("Webhook set successfully")
        return jsonify({'status': 'Webhook set successfully', 'response': response.json()})
    else:
        print("Failed to set webhook:", response.text)
        return jsonify({'status': 'Failed to set webhook', 'error': response.text}), 500

# Route to remove the webhook
@app.route('/remove_webhook', methods=['GET'])
def remove_webhook():
    response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook')
    
    if response.status_code == 200:
        print("Webhook removed successfully")
        return jsonify({'status': 'Webhook removed successfully', 'response': response.json()})
    else:
        print("Failed to remove webhook:", response.text)
        return jsonify({'status': 'Failed to remove webhook', 'error': response.text}), 500

# Health check route for Koyeb
@app.route('/health', methods=['GET'])
def health():
    return "Healthy", 200

# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)