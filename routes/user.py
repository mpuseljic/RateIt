import uuid
from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import users_table
from models import User, LoginRequest
from auth import hash_password, verify_password, create_jwt_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register")
def register(user: User):
    user_id = str(uuid.uuid4())
    response = users_table.scan(FilterExpression="username = :u",
                                ExpressionAttributeValues={":u": user.username})
    if response.get("Items"):
        raise HTTPException(status_code=400, detail="User already exists.")

    users_table.put_item(Item={
        "user_id": user_id,
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password)
    })
    return {"message": "User successfully registered", "user_id": user_id}

@router.post("/login")
def login(login_data: LoginRequest):
    response = users_table.scan(FilterExpression="username = :u",
                                ExpressionAttributeValues={":u": login_data.username})
    items = response.get("Items", [])
    
    if not items or not verify_password(login_data.password, items[0]["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_jwt_token(items[0]["user_id"])
    return {"access_token": token, "token_type": "bearer"}


@router.get("/{user_id}")
def get_user(user_id: str):
    response = users_table.get_item(Key={"user_id": user_id})
    user = response.get("Item")

    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen.")

    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user["email"]
    }
    
@router.post("/{username}/favorites/{product_name}")
def add_favorite(username: str, product_name: str):
    response = users_table.scan(
        FilterExpression="username = :u",
        ExpressionAttributeValues={":u": username}
    )
    
    items = response.get("Items", [])
    if not items:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")
    
    user = items[0]  
    
    if "favorites" not in user:
        user["favorites"] = []

    if product_name in user["favorites"]:
        raise HTTPException(status_code=400, detail="Proizvod je već u favoritima")

    user["favorites"].append(product_name)

    users_table.put_item(Item=user)

    return {"message": f"Proizvod '{product_name}' dodan u favorite korisnika '{username}'"}

@router.get("/{username}/favorites")
def get_favorites(username: str):
    response = users_table.scan(
        FilterExpression="username = :u",
        ExpressionAttributeValues={":u": username}
    )

    items = response.get("Items", [])
    if not items:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    user = items[0] 
    return {"favorites": user.get("favorites", [])}

@router.delete("/{username}/favorites/{product_name}")
def remove_favorite(username: str, product_name: str):
    response = users_table.scan(
        FilterExpression="username = :u",
        ExpressionAttributeValues={":u": username}
    )

    items = response.get("Items", [])
    if not items:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    user = items[0]

    if "favorites" not in user or product_name not in user["favorites"]:
        raise HTTPException(status_code=400, detail="Proizvod nije pronađen u favoritima")

    user["favorites"].remove(product_name)

    users_table.put_item(Item=user)

    return {"message": f"Proizvod '{product_name}' uklonjen iz favorita korisnika '{username}'"}

