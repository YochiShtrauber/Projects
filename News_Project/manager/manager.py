
import threading
import uuid
from datetime import time
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from confluent_kafka import Producer, Consumer, KafkaError
from starlette.responses import HTMLResponse
import requests
import json
import asyncio
import time



app = FastAPI()

# Kafka configuration
KAFKA_BROKER = "kafka:9092"  # replace with your Kafka broker's address
KAFKA_TOPIC = "news_topic"  # replace with your topic name
KAFKA_RESPONSE_TOPIC = "news_response_topic"


# Create a Kafka Producer instance
producer = Producer({'bootstrap.servers': KAFKA_BROKER})

# Create a Kafka Consumer instance
consumer = Consumer({
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'test1',  # Consumer group name
    'auto.offset.reset': 'earliest'  # 'earliest' to read from the start of the topic
})

# Subscribe to the Kafka topic
consumer.subscribe([KAFKA_RESPONSE_TOPIC])



def send_email_request(recipient_email, subject, body):
    # Define the URL of your FastAPI endpoint
    url = f"{SERVICE_MAIL_URL}/send-email"  # Adjust the URL if needed

    # Define the data you want to send in the POST request
    data = {
        "recipient_email": recipient_email,  # The recipient's email address
        "subject": subject,  # Subject of the email
        "body": body  # The email content
    }

    # Send the POST request to the FastAPI server
    response = requests.post(url, json=data)
    if response.status_code == 404:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()





def consume_messages():
    """Asynchronously consume messages from Kafka topic"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        msg = consumer.poll(1.0)  # Poll for messages with 1 second timeout
        if msg is None:
            continue  # Skip if no message is received
        if msg.error():  # Handle errors
            if msg.error().code() != KafkaError._PARTITION_EOF:
                print(f"Error: {msg.error()}")
            continue

        print(f"Consumed message: {msg.value().decode('utf-8')}")
        try:
            user_news_details = json.loads(msg.value().decode('utf-8'))
            print("Parsed message:", user_news_details)
            if user_news_details:
                message = f"hello {user_news_details['user']}, here are the news:\n\n"
                for i, title in enumerate(user_news_details["news"], start=1):
                    message += f"{i}: {title}\n\n"

                # sending email
                response = send_email_request(user_news_details["address"], "news", message)


        except json.JSONDecodeError:
            print("Failed to parse message")


def start_consumer():
    """Start the Kafka consumer in an event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(consume_messages())



# HTTP Client Setup
SERVICE_USER_URL = "http://user_accessor:5001"
SERVICE_MAIL_URL = "http://mail_accessor:8003"



class UserDetails(BaseModel):
    username: str
    password: str
    email: str
    preferences: Optional[List[str]] = None

@app.get("/api/users")
async def call_service_user_http_endpoint(username: str, password: str):
    """Call Service user via HTTP."""
    params = {"username": username, "password": password}
    response = requests.get(f"{SERVICE_USER_URL}/users", params=params)
    if response.status_code == 404:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    response.raise_for_status()
    return response.json()



@app.post("/api/users")
async def create_data(item: UserDetails):
    """Add a new item to the data."""
    response = requests.post(f"{SERVICE_USER_URL}/users", json=item.dict())
    if response.status_code == 404:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    response.raise_for_status()
    return response.json()



@app.put("/api/users")
async def update_data(item: UserDetails):
    """Update an existing item in Service B's data list."""
    response = requests.put(f"{SERVICE_USER_URL}/users/" + item.username, json=item.dict())
    if response.status_code == 404:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    # Raise an exception if the request failed
    response.raise_for_status()
    return response.json()


@app.post("/api/users")
async def register_user(user: UserDetails):
    """Register a new user."""
    # Send a POST request to the user service to create the new user
    response = requests.post(f"{SERVICE_USER_URL}/users", json=user.dict())

    # Check for errors in the response from the user service
    if response.status_code == 404:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to register user")

    # If user creation is successful, return a success message
    return {"message": "User successfully registered"}




@app.delete("/api/users")
async def delete_data(username: str, password: str):
    """Delete an item from Service B's data list."""
    params = {"id": username, "password": password}
    response = requests.delete(f"{SERVICE_USER_URL}/data/{username}", params=params)
    if response.status_code == 404:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    response.raise_for_status()
    return response.json()




DAPR_HTTP_PORT = "3500"  # Manager service DAPR HTTP port
PUBSUB_NAME = "rabbitmq"    # The name of your pub/sub component (from the YAML file)

def delivery_report(err, msg):
    """Called once for each message produced to indicate delivery result"""
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


#@app.get("/send/kafka")
def send_to_kafka(user: str, subjects: str, language: str, limit: int, address: str):
    # The message to send
    key = uuid.uuid4()  # Generate a unique UUID instance
    # The message to send
    message_value = {
        "user": user,
        "subjects": subjects,
        "language": language,
        "limit": limit,
        "address": address
    }

    # Produce the message to Kafka
    producer.produce(KAFKA_TOPIC, key=key.bytes, value=json.dumps(message_value), callback=delivery_report)
    producer.flush()  # Ensure the message is sent before returning

    return {"ok": "ok"}




class User(BaseModel):
    username: str
    password: str


@app.post("/login")
async def login(user: User):
    await call_service_user_http_endpoint(user.username, user.password)
    return {"message": "Login successful"}





def get_recent_users_from_api():
    # find the users to update the recent time of sending news, update that time, return them
    url = f"{SERVICE_USER_URL}/recent-users/"  # Adjust to your local or deployed URL

    try:
        # Send a GET request to the recent-users endpoint
        response = requests.get(url)
        print(response.text)
        # If the request was successful (status code 200), return the response data
        if response.status_code == 200:
            return response.json()  # Returns the JSON data from the response
        else:
            # If something went wrong, raise an exception with the error message
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except requests.exceptions.RequestException as e:
        # Handle any request exceptions (network issues, etc.)
        print(f"Error calling /recent-users/: {e}")
        raise HTTPException(status_code=500, detail="Error calling /recent-users API")




def send_news_to_user_with_up_time():
    """Fetch users and send news."""
    # Get the recent users asynchronously
    # get users and send news
    response = get_recent_users_from_api()  # Fetching users asynchronously
    if not response or "users" not in response:
        print("No users found or invalid response format.")
        return
    users_to_send_news = response["users"]  # Extracting the list of users from the response
    # Iterate over each user and send news to Kafka asynchronously
    for user in users_to_send_news:
        # Extracting user data from the 'data' field
        user_data = user['data']
        if 'username' in user_data and 'preferences' in user_data and 'email' in user_data:
            # Send user data to Kafka
            send_to_kafka(user_data['username'], user_data['preferences'], 'en', 5, user_data['email'])


#every x seconds call another func
def schedule_function():
    while True:
        send_news_to_user_with_up_time()
        time.sleep(10)


@app.on_event("startup")
async def startup():
    """Start Kafka consumer in a background thread"""
    # Start the consumer thread
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.daemon = True  # Make sure it stops when the program exits
    consumer_thread.start()
    schedule_thread = threading.Thread(target=schedule_function)
    schedule_thread.daemon = True  # Make sure it stops when the program exits
    schedule_thread.start()



@app.get("/", response_class=HTMLResponse)
async def login_page():
    with open("templates/login.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    with open("templates/register.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/users", response_class=HTMLResponse)
async def users_page():
    with open("templates/users.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
