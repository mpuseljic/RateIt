import uuid
from fastapi import FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from database import users_table, reviews_table
from models import User, LoginRequest, Review
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

# dohvaćanje usera
@app.get("/users/{user_id}")
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
    
# dodavanje nove recenzije
@app.post("/reviews")
def add_review(review: Review):
    reviews_table.put_item(Item=review.dict())
    return {
        "message": "Recenzija uspješno dodana",
        "review_id": review.review_id,
        "product_name": review.product_name
    }
    
# prikaz svih recenzija
@app.get("/reviews")
def get_all_reviews():
    response = reviews_table.scan()
    reviews = response.get("Items", [])
    return {"total_reviews": len(reviews), "reviews": reviews}

# prikaz recenzija za određenog usera
@app.get("/users/{username}/reviews")
def get_reviews_for_user(username: str):
    response = reviews_table.scan(
        FilterExpression="username = :u",
        ExpressionAttributeValues={":u": username}
    )
    reviews = response.get("Items", [])
    if not reviews:
        raise HTTPException(status_code=404, detail="Ovaj korisnik nema recenzija.")
    return {"username": username, "reviews": reviews}

# prikaz recenzija za određeni proizvod
@app.get("/products/{product_name}/reviews")
def get_reviews_by_product_name(product_name: str):
    if not product_name:
        raise HTTPException(status_code=400, detail="product_name je obavezan.")

    response = reviews_table.scan(
        FilterExpression="product_name = :p",
        ExpressionAttributeValues={":p": product_name}
    )

    reviews = response.get("Items", [])
    if not reviews:
        raise HTTPException(status_code=404, detail="Nema recenzija za ovaj proizvod.")

    return {"product_name": product_name, "reviews": reviews}
