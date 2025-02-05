import uuid
from fastapi import FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from database import users_table, reviews_table
from models import User, LoginRequest, Review, Comment
from auth import hash_password, verify_password, create_jwt_token
from fastapi import FastAPI, HTTPException, status
from decimal import Decimal
from typing import Optional

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
    try:
        review.validate_category(review.category)  
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    reviews_table.put_item(Item=review.dict())
    return {"message": "Recenzija uspješno dodana!", "review_id": review.review_id}
    
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

# prikaz recenzija za određeni proizvod i mogućnost filtriranja po ratingu
@app.get("/products/{product_name}/reviews")
def get_reviews_by_product_name(product_name: str, min_rating: Optional[int] = None):
    if not product_name:
        raise HTTPException(status_code=400, detail="product_name je obavezan.")

    filter_expression = "product_name = :p"
    expression_values = {":p": product_name}

    if min_rating is not None:
        filter_expression += " AND rating >= :r"
        expression_values[":r"] = Decimal(min_rating) 

    response = reviews_table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_values
    )

    reviews = response.get("Items", [])
    if not reviews:
        raise HTTPException(status_code=404, detail="Nema recenzija koje zadovoljavaju kriterije.")

    return {"product_name": product_name, "reviews": reviews}

# sortiranje po datumu
@app.get("/products/{product_name}/sortingreviews")
def sort_reviews(product_name: str, sort: str = "desc"):
    response = reviews_table.scan(
        FilterExpression="product_name = :p",
        ExpressionAttributeValues={":p": product_name}
    )

    reviews = response.get("Items", [])

    if not reviews:
        raise HTTPException(status_code=404, detail="Nema recenzija za ovaj proizvod.")

    reviews.sort(key=lambda x: x["created_at"], reverse=(sort == "desc"))

    return {"product_name": product_name, "reviews": reviews}

# lajkanje recenzija
@app.post("/reviews/{review_id}/like")
def like_review(review_id: str):
    response = reviews_table.get_item(Key={"review_id": review_id})
    
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Recenzija nije pronađena.")

    review = response["Item"]
    review["likes"] = review.get("likes", 0) + 1

    reviews_table.put_item(Item=review)
    
    return {"message": "Lajk uspješno dodan", "review": review}

# dodavanje komentara na recenziju
@app.post("/reviews/{review_id}/comments")
def add_comment(review_id: str, comment_data: Comment):
    response = reviews_table.get_item(Key={"review_id": review_id})
    
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Recenzija nije pronađena.")

    review = response["Item"]
    new_comment = comment_data.dict()
    review["comments"] = review.get("comments", []) + [new_comment]

    reviews_table.put_item(Item=review)
    return {"message": "Komentar uspješno dodan", "review": review}

# prikaz recenzija s komentarima
@app.get("/products/{product_name}/reviews/comments")
def get_reviews_and_comments(product_name: str):
    response = reviews_table.scan(
        FilterExpression="product_name = :p",
        ExpressionAttributeValues={":p": product_name}
    )

    reviews = response.get("Items", [])
    if not reviews:
        raise HTTPException(status_code=404, detail="Nema recenzija za ovaj proizvod.")

    for review in reviews:
        review["comments"] = review.get("comments", [])

    return {"product_name": product_name, "reviews": reviews}

# prosječna ocjene proizvoda
@app.get("/products/{product_name}/rating")
def get_average_rating(product_name: str):
    response = reviews_table.scan(
        FilterExpression="product_name = :p",
        ExpressionAttributeValues={":p": product_name}
    )

    reviews = response.get("Items", [])
    if not reviews:
        raise HTTPException(status_code=404, detail="Nema recenzija za ovaj proizvod.")

    avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
    return {"product_name": product_name, "average_rating": round(avg_rating, 2)}

# dohvaćanje proizvoda po kategoriji
@app.get("/categories/{category_name}/reviews")
def get_reviews_by_category(category_name: str):
    response = reviews_table.scan(
        FilterExpression="category = :c",
        ExpressionAttributeValues={":c": category_name}
    )
    reviews = response.get("Items", [])

    if not reviews:
        raise HTTPException(status_code=404, detail="Nema recenzija za ovu kategoriju.")

    products = {}
    for review in reviews:
        product_name = review["product_name"]
        if product_name not in products:
            products[product_name] = []
        products[product_name].append(review)

    return {"category": category_name, "products": products}