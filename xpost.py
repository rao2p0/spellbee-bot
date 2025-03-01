import tweepy
import openai
import os
import json
import time

# Load API keys
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Authenticate with Twitter
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# File to store previously tweeted words
TWEET_HISTORY_FILE = "tweeted_words.json"

def load_tweeted_words():
    if os.path.exists(TWEET_HISTORY_FILE):
        with open(TWEET_HISTORY_FILE, "r") as file:
            return json.load(file)
    return []

def save_tweeted_words(words):
    with open(TWEET_HISTORY_FILE, "w") as file:
        json.dump(words, file)

# Set up OpenAI client
openai.api_key = OPENAI_API_KEY

# Query OpenAI with Logging
def get_unique_word(existing_words, retries=3, delay=5):
    for attempt in range(retries):
        try:
            print(f"[DEBUG] Attempt {attempt + 1}: Querying OpenAI API...")
            
            # Use the new OpenAI API format for chat completion
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini-2024-07-18",  # Your specific model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Provide a unique, interesting word, its meaning, and an example sentence."}
                ],
                max_tokens=100
            )

            result = response["choices"][0]["message"]["content"].strip()
            print(f"[DEBUG] OpenAI Response: {result}")

            lines = result.split("\n")
            word = lines[0].split(":")[1].strip() if ":" in lines[0] else lines[0].strip()
            meaning = lines[1].split(":")[1].strip() if ":" in lines[1] else lines[1].strip()
            sentence = lines[2].split(":")[1].strip() if ":" in lines[2] else lines[2].strip()

            if word.lower() not in existing_words:
                return word, meaning, sentence
            
        except Exception as e:
            print(f"[ERROR] OpenAI API error: {e}")
            time.sleep(delay)

    print("[ERROR] Failed to get a unique word after retries.")
    return None, None, None

# Compose Tweet
def compose_tweet(word, meaning, sentence):
    hashtags = "#vocabulary #spellbee"
    tweet = f"Word of the day: {word}\n\nMeaning: {meaning}\n\nExample: {sentence}\n\n{hashtags}"
    print(f"[DEBUG] Composed Tweet: {tweet}")
    return tweet

# Main Function
def tweet():
    print("[DEBUG] Loading previously tweeted words...")
    tweeted_words = load_tweeted_words()
    print(f"[DEBUG] Previously Tweeted Words: {tweeted_words}")

    word, meaning, sentence = get_unique_word(tweeted_words)

    if word:
        tweet_text = compose_tweet(word, meaning, sentence)
        try:
            print("[DEBUG] Posting Tweet...")
            api.update_status(tweet_text)
            print("[SUCCESS] Tweet posted!")

            tweeted_words.append(word.lower())
            save_tweeted_words(tweeted_words)
        except tweepy.TweepError as e:
            print(f"[ERROR] Twitter API error: {e}")
    else:
        print("[ERROR] No valid word found. Skipping tweet.")

# Run the bot
if __name__ == "__main__":
    tweet()
