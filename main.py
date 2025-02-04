import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from database import users_table
from models import User
from auth import hash_password

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# registracija usera
@app.post("/register")
def register(user: User):
    user_id = str(uuid.uuid4()) 
    response = users_table.scan(FilterExpression="username = :u", 
                                ExpressionAttributeValues={":u": user.username})
    if response.get("Items"):
        raise HTTPException(status_code=400, detail="User pod tim imenom već postoji.")

    hashed_password = hash_password(user.password)
    users_table.put_item(Item={
        "user_id": user_id,
        "username": user.username,
        "email": user.email,
        "password": hashed_password
    })
    
    return {"message": "User je uspješno registriran..", "user_id": user_id}
