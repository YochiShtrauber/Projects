import asyncio
import os
import threading
import uuid
from fastapi import FastAPI, HTTPException
import requests
from typing import List
from confluent_kafka import Consumer, KafkaError, Producer
import json

# Initialize the FastAPI app
app = FastAPI()



# Kafka configuration
KAFKA_BROKER = "kafka:9092"  # Replace with your Kafka broker address
KAFKA_TOPIC = "news_topic"  # Replace with your Kafka topic name
KAFKA_RESPONSE_TOPIC = "news_response_topic"

producer = Producer({'bootstrap.servers': KAFKA_BROKER})

# Create a Kafka Consumer instance
consumer = Consumer({
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'test1',  # Consumer group name
    'auto.offset.reset': 'earliest'  # 'earliest' to read from the start of the topic
})

# Subscribe to the Kafka topic
consumer.subscribe([KAFKA_TOPIC])

# Fetch API key from environment variable (for security)
API_KEY = os.getenv("NEWS_DATA_API_KEY", "put you key")  # Set a default for testing

def fetch_news(api_key: str, subjects: List[str], language="en", limit=5):
    """
    Fetch news from NewsData.io based on the subjects, limiting the number of articles.

    Parameters:
    - api_key: Your API key for NewsData.io
    - subjects: List of subjects to filter news
    - language: Language of news articles (default is "en" for English)
    - limit: The maximum number of articles to return (default is 5)

    Returns:
    - List of news articles filtered by the subjects, limited to 'limit'
    """
    url = "https://newsdata.io/api/1/news?apikey=" + api_key

    # Prepare the query parameters
    params = {
        'apikey': api_key,
        'language': language,
        'q': ' OR '.join(subjects),  # Join multiple subjects with 'OR' to search for articles matching any of the topics
        'country': 'us'  # You can change this to get news from a different country
    }

    try:
        # Send the GET request with a timeout of 10 seconds
        response = requests.get(url, params=params, timeout=10, verify=True)  # verify=True ensures SSL cert verification

        # Check if the response status is OK (200)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('results', [])
            return articles[:limit]  # Return only the first 'limit' articles

        elif response.status_code == 404:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except requests.exceptions.Timeout:
        print("Error: The request timed out.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error: A request error occurred: {e}")
        return []



def extract_message(news_articles_list):
    # If no articles are found, return a 404 error
    if not news_articles_list:
        raise HTTPException(status_code=404, detail="No articles found")

    # Extract only the titles of the articles
    titles = [article.get('title', 'No Title') for article in news_articles_list]

    # Return the response as a JSON object
    return titles


def handle_news_message(user: str, subjects: List[str], language: str, limit: int, address: str):
     news_articles_list = fetch_news(API_KEY, subjects, language, limit)
     #print(news_articles_list)
     titles_list = extract_message(news_articles_list)

     if not titles_list == None:
         key = uuid.uuid4()  # Generate a unique UUID instance
         # The message to send
         message_value = {
             "user": user,
             "news": titles_list,
             "address": address
         }

         # Produce the message to Kafka
         producer.produce(KAFKA_RESPONSE_TOPIC, key=key.bytes, value=json.dumps(message_value))
         producer.flush()  # Ensure the message is sent before returning




@app.on_event("startup")
async def startup():
    """Start Kafka consumer in a background thread"""
    # Start the consumer thread
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.daemon = True  # Make sure it stops when the program exits
    consumer_thread.start()



async def consume_messages():
    """Asynchronously consume messages from Kafka topic"""
    try:
        while True:
            msg = consumer.poll(1.0)  # Poll for messages with 1 second timeout
            if msg is None: continue  # Skip if no message is received
            if msg.error():  # Handle errors
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"Error: {msg.error()}")
                continue

            print(f"Consumed message: {msg.value().decode('utf-8')}")
            try:
                message = json.loads(msg.value().decode('utf-8'))
                handle_news_message(message["user"], message["subjects"], message["language"], message["limit"], message["address"])
                print("Parsed message:", message)
            except json.JSONDecodeError:
                print("Failed to parse message")

    except KeyboardInterrupt:
        print("Consumer interrupted")
    finally:
        consumer.close()



def start_consumer():
    """Start the Kafka consumer in an event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(consume_messages())






if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
