import tweepy
from openai import OpenAI
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
TWEET_HISTORY_FILE = "tweeted_words.txt"

def load_tweeted_words():
    if os.path.exists(TWEET_HISTORY_FILE):
        try:
            with open(TWEET_HISTORY_FILE, "r") as file:
                # Read all lines and strip whitespace, filter out empty lines
                words = [line.strip().lower() for line in file.readlines() if line.strip()]
                print(f"[INFO] Loaded {len(words)} words from history file.")
                return words
        except Exception as e:
            print(f"[WARNING] Error reading history file: {e}. Starting with empty history.")
            return []
    else:
        print("[INFO] No history file found. Creating a new one.")
        # Create an empty file
        open(TWEET_HISTORY_FILE, "w").close()
        return []

def save_tweeted_words(words):
    with open(TWEET_HISTORY_FILE, "w") as file:
        # Write each word on a new line
        for word in words:
            file.write(f"{word}\n")

# Set up OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Query OpenAI with Logging
def get_unique_word(existing_words, retries=3, delay=5):
    for attempt in range(retries):
        try:
            print(f"[DEBUG] Attempt {attempt + 1}: Querying OpenAI API...")
            
            # Use the new OpenAI API format for chat completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Specify your model here
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Provide a unique, interesting word, its meaning, and an example sentence."}
                ],
                max_tokens=100
            )
            
            # Print the raw response to debug its structure
            print(f"[DEBUG] Raw OpenAI API response: {response}")

            # Access the content correctly from the response object
            message_content = response.choices[0].message.content.strip()
            
            # If no content, skip to the next retry
            if not message_content:
                print(f"[ERROR] No valid content in the response")
                continue
            
            print(f"[DEBUG] OpenAI Response: {message_content}")

            # Split the response into lines and extract word, meaning, and sentence
            lines = message_content.split("\n")
            
            # More robust parsing of the response
            word = None
            meaning = None
            sentence = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.lower().startswith("word:") or line.lower().startswith("word "):
                    word = line.split(":", 1)[1].strip() if ":" in line else line.replace("Word", "", 1).strip()
                elif line.lower().startswith("meaning:") or line.lower().startswith("meaning "):
                    meaning = line.split(":", 1)[1].strip() if ":" in line else line.replace("Meaning", "", 1).strip()
                elif line.lower().startswith("example:") or line.lower().startswith("example ") or line.lower().startswith("example sentence:"):
                    sentence = line.split(":", 1)[1].strip() if ":" in line else line.replace("Example sentence", "", 1).replace("Example", "", 1).strip()
            
            # If we couldn't parse the response properly, try a different approach
            if not all([word, meaning, sentence]):
                if len(lines) >= 3:
                    word = lines[0].split(":", 1)[1].strip() if ":" in lines[0] else lines[0].strip()
                    meaning = lines[1].split(":", 1)[1].strip() if ":" in lines[1] else lines[1].strip()
                    sentence = lines[2].split(":", 1)[1].strip() if ":" in lines[2] else lines[2].strip()
            
            if word and word.lower() not in existing_words:
                return word, meaning, sentence
            elif word:
                print(f"[DEBUG] Word '{word}' already used. Trying again...")
            else:
                print(f"[ERROR] Could not parse word from response: {message_content}")

        except Exception as e:
            print(f"[ERROR] OpenAI API error: {e}")
            time.sleep(delay)

    print("[ERROR] Failed to get a unique word after retries.")
    return None, None, None

# Compose Tweet
def compose_tweet(word, meaning, sentence):
    hashtags = "#vocabulary #spellingbee"
    tweet = f"Word: {word}\n\nMeaning: {meaning}\n\nExample: {sentence}\n\n{hashtags}"
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
            # Use the v2 API instead of the deprecated v1.1 API
            client = tweepy.Client(
                consumer_key=API_KEY,
                consumer_secret=API_SECRET,
                access_token=ACCESS_TOKEN,
                access_token_secret=ACCESS_SECRET
            )
            response = client.create_tweet(text=tweet_text)
            print(f"[SUCCESS] Tweet posted! Tweet ID: {response.data['id']}")

            tweeted_words.append(word.lower())
            save_tweeted_words(tweeted_words)
        except Exception as e:
            print(f"[ERROR] Twitter API error: {e}")
    else:
        print("[ERROR] No valid word found. Skipping tweet.")

# Run the bot
if __name__ == "__main__":
    tweet()
