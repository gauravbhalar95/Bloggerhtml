import os
import telebot
from flask import Flask, request

# Flask App Setup
app = Flask(__name__)

# Bot Token from Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Initialize the Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Function to generate recipe HTML
def generate_recipe_html(title, description, image_url):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} Recipe</title>
        <meta name="description" content="{description}" />
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; }}
            #recipe-container {{ max-width: 800px; margin: 50px auto; padding: 20px; border-radius: 8px; background-color: #fff; }}
            h1 {{ color: #ff5722; }}
            h2, h3 {{ color: #ff2200; }}
            p {{ color: #1100ff; }}
            img {{ width: 100%; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div id="recipe-container">
            <h1>{title}</h1>
            <img src="{image_url}" alt="{title} Recipe">
            <h2>Recipe Overview</h2>
            <p>{description}</p>
        </div>
    </body>
    </html>
    """
    return html_content

# Command Handler for /recipe
@bot.message_handler(commands=['recipe'])
def get_recipe_title(message):
    bot.send_message(message.chat.id, "Enter the recipe title:")
    bot.register_next_step_handler(message, get_recipe_description)

def get_recipe_description(message):
    title = message.text
    bot.send_message(message.chat.id, "Enter the recipe description:")
    bot.register_next_step_handler(message, get_recipe_image, title)

def get_recipe_image(message, title):
    description = message.text
    bot.send_message(message.chat.id, "Enter the image URL:")
    bot.register_next_step_handler(message, process_recipe, title, description)

def process_recipe(message, title, description):
    image_url = message.text
    html_content = generate_recipe_html(title, description, image_url)
    filename = f"{title.replace(' ', '_')}.html"
    
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)
    
    with open(filename, 'rb') as file:
        bot.send_document(message.chat.id, file)
    
    os.remove(filename)

# Webhook route for Telegram Updates
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# Route to set the webhook
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}/{BOT_TOKEN}')
    return response.json()

# Start the Flask App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
