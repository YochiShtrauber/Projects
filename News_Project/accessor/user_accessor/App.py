
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from sqlalchemy import DateTime
from sqlalchemy import func
import uvicorn
from datetime import datetime, timedelta

SEND_FREQUENCY_SECONDS = 100


def checking_authentication(username: str, password: str, db: Session):
    db_item = db.query(UserDetailsDB).filter(
        UserDetailsDB.username == username, UserDetailsDB.password == password
    ).first()

    if db_item:
        return db_item
    else:
        return None


# Database setup
DATABASE_URL = "postgresql://postgres:postgres@postgresdb:5432/postgres"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



class UserDetailsDB(Base):
    __tablename__ = "dbusers"
    #  id as string
    username = Column(String(50), primary_key=True, index=True)
    # password as string
    password = Column(String(50), nullable=True)
    # Preferences as an array of strings (specific to PostgreSQL)
    preferences = Column(ARRAY(String), nullable=True)  # Use ARRAY for lists of strings
    # Address as a string
    email = Column(String(255), nullable=True)
    # the last time of sending news
    last_time_checking_news = Column(DateTime, nullable=True,  default=func.now())




# Create the tables in the database (only once during the initial setup)
Base.metadata.create_all(bind=engine)



class UserDetails(BaseModel):
    username: str  # ID is a string (e.g., varchar(50) in DB)
    password: str
    preferences: Optional[List[str]] = None  # List of strings (array of strings in DB)
    email: Optional[str] = None  # Address as a string



async def get_recent_user_details(db: Session) -> JSONResponse:
    # Calculate the time that is 60 seconds ago from now
    time_threshold = datetime.now() - timedelta(seconds=SEND_FREQUENCY_SECONDS)

    # Query to find all records where 'last_time_checking_news' is within the last 60 seconds
    users_to_send_news = db.query(UserDetailsDB).filter(UserDetailsDB.last_time_checking_news < time_threshold).all()

    # If we have recent users, update their 'last_time_checking_news' to the current time
    if users_to_send_news:
        current_time = datetime.now()
        for user in users_to_send_news:
            user.last_time_checking_news = current_time  # Update the last_time_checking_news column

        db.commit()  # Commit the changes to the database

    # Prepare the response with 'message' and 'data' for each user in the list
    response_data = [
        {
            "message": "id details",
            "data": {
                "username": item.username,
                "password": item.password,
                "preferences": item.preferences,
                "email": item.email,
            }
        }
        for item in users_to_send_news
    ]
    print(response_data)

    # Return the response as JSON
    return JSONResponse(content={"users": response_data})



# FastAPI app setup
app = FastAPI()


# Helper to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# New API endpoint to update SEND_FREQUENCY_SECONDS
@app.put("/update-send-frequency/")
async def update_send_frequency(new_frequency: int):
    global SEND_FREQUENCY_SECONDS
    if new_frequency < 1:
        raise HTTPException(status_code=400, detail="Frequency must be a positive integer.")

    SEND_FREQUENCY_SECONDS = new_frequency

    return JSONResponse(content={"message": f"Send frequency updated to {SEND_FREQUENCY_SECONDS} seconds."})


# New API endpoint to get current SEND_FREQUENCY_SECONDS
@app.get("/get-send-frequency/")
async def get_send_frequency():
    return JSONResponse(content={"send_frequency_seconds": SEND_FREQUENCY_SECONDS})



@app.get("/recent-users/")
async def get_recent_users(db: Session = Depends(get_db)):
    return await get_recent_user_details(db)


@app.get("/users")
async def http_find_id_data(username: str, password: str, db: Session = Depends(get_db)):
    """HTTP endpoint for getting details of id"""
    db_item = checking_authentication(username, password, db)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item was not found - the authentication"
                                                    " details are not exist. please insert correct authentication")

    return JSONResponse(
        content={
            "message": "id details",
            "data": {
                "username": db_item.username,
                "password": db_item.password,
                "preferences": db_item.preferences,
                "email": db_item.email
            }
        }
    )




@app.post("/users")
async def create_data(item: UserDetails, db: Session = Depends(get_db)):
    """Add a new item to the database."""
    # db_item = UserDetailsDB(value=item.value)
    db_item = checking_authentication(item.username, item.password, db)
    if db_item is None:
        item = UserDetailsDB(
            username=item.username,  # ID is taken from the Pydantic model
            password=item.password,
            preferences=item.preferences,  # Preferences as a list of strings
            email=item.email  # Address as a string
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return JSONResponse(
            content={
                "message": "The item was added successfully.",
                "data": {
                }
            }
        )
    else:
        raise HTTPException(status_code=404, detail="The Item was not added to the database because the authentication"
                                                    " details already exist. Please choose new authentication details.")


@app.put("/users/{username}")
async def update_data(username: str, item: UserDetails, db: Session = Depends(get_db)):
    """Update an existing item in the database."""
    db_item = checking_authentication(item.username, item.password, db)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item was not updated because it was not found - the authentication"
                                                    " details are not exist. please insert correct authentication")

    else:
        db_item.username = item.username
        db_item.password = item.password
        db_item.preferences = item.preferences  # Update preferences if provided
        db_item.email = item.email  # Update email address if provided

        db.commit()
        db.refresh(db_item)

        #return a JSON response with a message and the updated data
        return JSONResponse(
            content={
                "message": "The Item was updated",
                "data": {
                }
            }
        )



@app.delete("/data/{username}")
async def delete_data(username: str, password: str, db: Session = Depends(get_db)):
    """Delete an item from the database."""
    db_item = checking_authentication(username, password, db)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item was not deleted  because it was not found - the authentication"
                                                    " details are not exist. please insert correct authentication")

    db.delete(db_item)
    db.commit()
    # Return a response with a message and the deleted item data
    return JSONResponse(
        content={
            "message": "The Item was deleted",
                       "data": {
                       }
                }
         )





if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=5001)
