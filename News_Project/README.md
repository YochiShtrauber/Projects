# final-project-zio-net

# Personalized News Update Aggregator 


## Project Description:
  

The project aims to develop a microservice-based application that aggregates news and technology 
updates based on user preferences. The system will fetch the latest news, pick up most interesting 
news using AI based on user preferences, and send this information to users via email. 
The "manager" service is responsible for handling requests, validating them and passing them to the accessor services.
The communication between the "manager" service and the "news_accessor" using Kafka.
The "user_accessor" service processes the requests from the manager and manipulates the data in PostgreSQL accordingly.

## Technologies Used:
- Python (FastAPI): The framework used to develop the microservices in the PyCharm environment.
- Docker: A platform used to containerize and manage the microservices.
- Kafka: A message broker for the communication between the microservices.
- PostgreSQL: The database used to store and retrieve user entries.

## Getting Started:
1. Clone the repository.
2. Navigate to the project directory.
3. Run the command `docker-compose up` to start the services.

## Architecture:
- Manager Service: Accepts requests related to user entries, validates them, and pushes to the Kafka queue for the News accessor, or sends message to the service.
- Accessor User: Picks up requests from the manager, processes the requests, and performs actions on PostgreSQL.
- Accessor News: Picks up requests from the manager, by Kafka, processes the requests, performs actions and sends response also by Kafka. 
- Accessor Mail: Picks up requests from the manager, processes the requests and performs actions.
- Kafka: Used as the messaging system for the exchange of requests between the Manager and the news service.
- PostgreSQL: The database used to store and retrieve user entries.

## Usage:
The Manager service exposes the following endpoints:
- `GET /api/users`: Returns details of one user.
- `PUT /api/users/{username}`: Updates one user.
- `DELETE /api/users/{username}`: Deletes the user.
- `POST /api/users`: Adds a new user.
- `PUT /update-send-frequency/?new_frequency=10`: increase / decrease the frequency of getting messages



