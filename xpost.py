import tweepy
import openai
import os
import json
import random
import time

# Load API keys from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Authenticate with Twitter
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Set OpenAI API Key
openai.api_key = OPENAI_API_KEY

# File to store previously tweeted words
TWEET_HISTORY_FILE = "tweeted_words.json"

# Load previously tweeted words
def load_tweeted_words():
    if os.path.exists(TWEET_HISTORY_FILE):
        with open(TWEET_HISTORY_FILE, "r") as file:
            return json.load(file)
    return []

# Save tweeted words
def save_tweeted_words(words):
    with open(TWEET_HISTORY_FILE, "w") as file:
        json.dump(words, file)

# Query OpenAI for a word, meaning, and sentence with retries
def get_unique_word(existing_words, retries=3, delay=5):
    for _ in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Provide a unique, interesting word, its meaning, and an example sentence."}],
                max_tokens=100
            )
            result = response["choices"][0]["message"]["content"]
            
            # Extract word, meaning, and example sentence
            lines = result.split("\n")
            word = lines[0].split(":")[1].strip() if ":" in lines[0] else lines[0].strip()
            meaning = lines[1].split(":")[1].strip() if ":" in lines[1] else lines[1].strip()
            sentence = lines[2].split(":")[1].strip() if ":" in lines[2] else lines[2].strip()

            # Ensure it's a new word
            if word.lower() not in existing_words:
                return word, meaning, sentence
            
        except Exception as e:
            print(f"OpenAI API error: {e}, retrying in {delay} seconds...")
            time.sleep(delay)

    return None, None, None  # Fail gracefully after retries

# Format tweet
def compose_tweet(word, meaning, sentence):
    hashtags = "#vocabulary #spellbee"
    tweet = f"Word of the day: {word}\n\nMeaning: {meaning}\n\nExample: {sentence}\n\n{hashtags}"
    return tweet

# Main function to run the bot
def tweet():
    tweeted_words = load_tweeted_words()

    word, meaning, sentence = get_unique_word(tweeted_words)

    if word:
        tweet_text = compose_tweet(word, meaning, sentence)
        try:
            api.update_status(tweet_text)
            print(f"Tweeted: {tweet_text}")

            # Append new word to history
            tweeted_words.append(word.lower())
            save_tweeted_words(tweeted_words)
        except tweepy.TweepError as e:
            print(f"Error tweeting: {e}")

# Run the bot
if __name__ == "__main__":
    tweet()
