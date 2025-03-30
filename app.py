import os
import telebot
import requests
from flask import Flask, request

# Create a Flask app
app = Flask(__name__)

# Replace with your bot token from Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Initialize the TeleBot
bot = telebot.TeleBot(BOT_TOKEN)

# Function to generate high-quality SEO-optimized recipe HTML
def generate_recipe_html(title, image_urls, description, ingredients, steps, tips, faq, related_recipes, suggest_url):
    images_html = "".join([f'<img src="{url}" alt="{title}" class="recipe-image">' for url in image_urls])
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} Recipe</title>
        <meta name="description" content="{description}" />
        <meta name="robots" content="index, follow" />
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; }}
            #recipe-container {{ max-width: 800px; margin: 50px auto; padding: 20px; border-radius: 8px; background-color: #fff; }}
            h1 {{ color: #ff5722; font-size: 28px; }}
            h2, h3 {{ color: #ff2200; font-size: 22px; }}
            p {{ color: #333; font-size: 16px; }}
            .recipe-image {{ width: 100%; border-radius: 8px; margin: 10px 0; }}
            .section {{ text-align: left; margin: 20px; }}
            .faq, .related-recipes {{ margin-top: 20px; }}
            .suggest-url {{ font-size: 18px; font-weight: bold; color: #0073e6; }}
        </style>
    </head>
    <body>
        <div id="recipe-container">
            <h1>{title}</h1>
            {images_html}
            <h2>Recipe Overview</h2>
            <p>{description}</p>
            <h2>Ingredients</h2>
            <p>{ingredients}</p>
            <h2>Instructions</h2>
            <p>{steps}</p>
            <h3>Tips for Perfect Recipe</h3>
            <p>{tips}</p>
            <div class="faq">
                <h3>FAQs</h3>
                <p>{faq}</p>
            </div>
            <div class="related-recipes">
                <h3>Related Recipes</h3>
                <p>{related_recipes}</p>
            </div>
            <p class="suggest-url">Suggested URL: {suggest_url}</p>
        </div>
    </body>
    </html>
    """
    return html_content

# Command handler for `/recipe`
@bot.message_handler(commands=['recipe'])
def request_recipe_details(message):
    bot.send_message(message.chat.id, "Enter the recipe title (H1):")
    bot.register_next_step_handler(message, process_title)

def process_title(message):
    title = message.text
    bot.send_message(message.chat.id, "Enter three image URLs separated by commas:")
    bot.register_next_step_handler(message, process_images, title)

def process_images(message, title):
    image_urls = [url.strip() for url in message.text.split(',')]
    bot.send_message(message.chat.id, "Enter a short recipe description:")
    bot.register_next_step_handler(message, process_description, title, image_urls)

def process_description(message, title, image_urls):
    description = message.text
    bot.send_message(message.chat.id, "Enter ingredients list:")
    bot.register_next_step_handler(message, process_ingredients, title, image_urls, description)

def process_ingredients(message, title, image_urls, description):
    ingredients = message.text
    bot.send_message(message.chat.id, "Enter step-by-step instructions:")
    bot.register_next_step_handler(message, process_steps, title, image_urls, description, ingredients)

def process_steps(message, title, image_urls, description, ingredients):
    steps = message.text
    bot.send_message(message.chat.id, "Enter cooking tips:")
    bot.register_next_step_handler(message, process_tips, title, image_urls, description, ingredients, steps)

def process_tips(message, title, image_urls, description, ingredients, steps):
    tips = message.text
    bot.send_message(message.chat.id, "Enter FAQs:")
    bot.register_next_step_handler(message, process_faq, title, image_urls, description, ingredients, steps, tips)

def process_faq(message, title, image_urls, description, ingredients, steps, tips):
    faq = message.text
    bot.send_message(message.chat.id, "Enter related recipes:")
    bot.register_next_step_handler(message, process_related, title, image_urls, description, ingredients, steps, tips, faq)

def process_related(message, title, image_urls, description, ingredients, steps, tips, faq):
    related_recipes = message.text
    bot.send_message(message.chat.id, "Enter a suggested URL for the recipe:")
    bot.register_next_step_handler(message, generate_and_send_html, title, image_urls, description, ingredients, steps, tips, faq, related_recipes)

def generate_and_send_html(message, title, image_urls, description, ingredients, steps, tips, faq, related_recipes):
    suggest_url = message.text
    html_content = generate_recipe_html(title, image_urls, description, ingredients, steps, tips, faq, related_recipes, suggest_url)
    filename = f"{title.replace(' ', '_')}_recipe.html"
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)
    with open(filename, 'rb') as file:
        bot.send_document(message.chat.id, file)
    os.remove(filename)

# Webhook route
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
