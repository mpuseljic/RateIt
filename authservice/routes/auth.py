import uuid
import jwt
import datetime
import os
from fastapi import APIRouter, HTTPException, Request
from database import users_table
from models import User, LoginRequest, TokenResponse
from passlib.context import CryptContext
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(username: str):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    token_data = {"sub": username, "exp": expiration}
    return jwt.encode(token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None

# registracija
@router.post("/register")
def register(user: User):
    user_id = str(uuid.uuid4())
    response = users_table.query(
        KeyConditionExpression=Key("username").eq(user.username)
        )
    if response.get("Items"):
        raise HTTPException(status_code=400, detail="Korisnik već postoji.")

    users_table.put_item(Item={
        "user_id": user_id,
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password)
    })
    return {"message": "Korisnik uspješno registriran!", "user_id": user_id}

# prijava i generiranje tokena
@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    response = users_table.query(
        KeyConditionExpression=Key("username").eq(login_data.username)
    )
    items = response.get("Items", [])
    
    if not items or not verify_password(login_data.password, items[0]["password"]):
        raise HTTPException(status_code=401, detail="Neispravni podaci")

    token = create_jwt_token(items[0]["username"])
    return {"access_token": token, "token_type": "bearer"}

# provjera tokena za user servis
@router.get("/verify")
def verify_token(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Nema tokena")

    token = token.split("Bearer ")[1]
    username = decode_jwt_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Neispravni token")
    
    response = users_table.get_item(Key={"username": username})
    user = response.get("Item")
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    return {"username": username, "email": user["email"]}
