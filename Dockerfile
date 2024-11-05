# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variables
ENV BOT_TOKEN=7268627071:AAHJXah9jXlZW_4hfzzs9JpY8j8J2ypDNjc
ENV TMDB=fa709e9b046aeca0aac65b776b6b0b63
ENV WEBHOOK_URL=https://electric-johna-telegrambotsearch-d47601f4.koyeb.app/

# Run app.py when the container launches
CMD python app.py
