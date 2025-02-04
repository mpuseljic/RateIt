import uuid
from fastapi import FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from database import users_table
from models import User, LoginRequest
from auth import hash_password, verify_password, create_jwt_token
from fastapi import FastAPI, HTTPException, status

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

# prijava usera i generiranje jwt
@app.post("/login")
def login(login_data: LoginRequest):
    response = users_table.scan(
        FilterExpression="username = :u",
        ExpressionAttributeValues={":u": login_data.username}
    )

    items = response.get("Items", [])
    if not items:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Neispravni podaci.")

    user = items[0]

    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Neispravni podaci.")

    token = create_jwt_token(user["user_id"])
    return {"access_token": token, "token_type": "bearer"}
