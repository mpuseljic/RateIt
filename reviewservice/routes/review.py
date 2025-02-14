import aiohttp
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Header, Body
from database import reviews_table, S3_BUCKET_NAME, s3_client
from models import Review, Comment
from typing import Optional
from decimal import Decimal
import uuid

router = APIRouter()

# provjera tokena
async def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token nedostaje")

    async with aiohttp.ClientSession() as session:
        async with session.get("http://authservice:8001/auth/verify", headers={"Authorization": authorization}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=401, detail="Nevažeći token")
            data = await resp.json()
            return {"user_id": data["user_id"], "token": authorization.split("Bearer ")[1]}  


# dodaje recenziju samo ako user posroji
@router.post("/")
async def add_review(review: Review, auth=Depends(verify_token)):
    user_id = auth["user_id"]  
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://userservice:8002/users/me", headers={"Authorization": f"Bearer {auth['token']}"}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=404, detail="Korisnik nije pronađen")
            user_data = await resp.json()

    username = user_data["username"] 
    review.username = username
    reviews_table.put_item(Item=review.dict())

    return {"message": "Recenzija uspješno dodana!", "review_id": review.review_id}

# pregled svih recenzija
@router.get("/")
def get_all_reviews():
    response = reviews_table.scan()
    reviews = response.get("Items", [])
    return {"total_reviews": len(reviews), "reviews": reviews}

# pregled recenzija određenog korisnika
@router.get("/user/{username}")
def get_reviews_for_user(username: str):
    response = reviews_table.scan(
        FilterExpression="username = :u",
        ExpressionAttributeValues={":u": username}
    )
    reviews = response.get("Items", [])
    if not reviews:
        raise HTTPException(status_code=404, detail="Ovaj korisnik nema recenzija.")
    return {"username": username, "reviews": reviews}

# pregled recenzija za određeni proizvod, također može se i filtirati po ocjeni
@router.get("/product/{product_name}")
def get_reviews_by_product_name(product_name: str, min_rating: Optional[int] = None):
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
@router.get("/product/{product_name}/sort")
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
@router.post("/{review_id}/like")
def like_review(review_id: str):
    response = reviews_table.get_item(Key={"review_id": review_id})
    
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Recenzija nije pronađena.")

    review = response["Item"]
    review["likes"] = review.get("likes", 0) + 1

    reviews_table.put_item(Item=review)
    
    return {"message": "Lajk uspješno dodan", "review": review}

# dodavanje komentara na recenziju
@router.post("/{review_id}/comment")
def add_comment(review_id: str, comment_data: Comment):
    response = reviews_table.get_item(Key={"review_id": review_id})
    
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Recenzija nije pronađena.")

    review = response["Item"]
    new_comment = comment_data.dict()
    review["comments"] = review.get("comments", []) + [new_comment]

    reviews_table.put_item(Item=review)
    return {"message": "Komentar uspješno dodan", "review": review}

# pregled recenzija s komentarima
@router.get("/product/{product_name}/comments")
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

# prosječna ocjena proizvoda
@router.get("/product/{product_name}/rating")
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

# pregled recenzija po kategorijama
@router.get("/category/{category_name}")
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

# pregled najpopularnijih proizvoda na tememelju broja recenzija
@router.get("/top-rated")
def get_top_rated_products():
    response = reviews_table.scan()
    all_reviews = response.get("Items", [])
    
    product_counts = {}
    for review in all_reviews:
        product_counts[review["product_name"]] = product_counts.get(review["product_name"], 0) + 1

    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {"top_rated_products": [{"product_name": p[0], "review_count": p[1]} for p in top_products]}

# upload slike za recenziju
@router.post("/{review_id}/upload-image")
def upload_review_image(review_id: str, file: UploadFile = File(...)):
    file_extension = file.filename.split(".")[-1]
    file_key = f"reviews/{review_id}/{uuid.uuid4()}.{file_extension}"

    s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, file_key)
    image_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file_key}"

    response = reviews_table.get_item(Key={"review_id": review_id})
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Recenzija nije pronađena.")

    review = response["Item"]
    review["image_url"] = image_url
    reviews_table.put_item(Item=review)

    return {"message": "Slika uspješno uploadana!", "image_url": image_url}

# pregled slike recenzije
@router.get("/{review_id}/image")
def get_review_image(review_id: str):
    response = reviews_table.get_item(Key={"review_id": review_id})
    if "Item" not in response or "image_url" not in response["Item"]:
        raise HTTPException(status_code=404, detail="Slika nije pronađena.")

    return {"image_url": response["Item"]["image_url"]}

# brisanje slike recenzije
@router.delete("/{review_id}/image")
def delete_review_image(review_id: str):
    response = reviews_table.get_item(Key={"review_id": review_id})
    if "Item" not in response or "image_url" not in response["Item"]:
        raise HTTPException(status_code=404, detail="Slika nije pronađena.")

    file_key = response["Item"]["image_url"].split(f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/")[-1]
    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file_key)

    del response["Item"]["image_url"]
    reviews_table.put_item(Item=response["Item"])

    return {"message": "Slika obrisana!"}

# ažuriranje recenzije 
@router.put("/{review_id}")
async def update_review(review_id: str, updated_review: Review = Body(...), auth=Depends(verify_token)):
    user_id = auth["user_id"]  
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://userservice:8002/users/me", headers={"Authorization": f"Bearer {auth['token']}"}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=404, detail="Korisnik nije pronađen")
            user_data = await resp.json()

    username = user_data["username"]
    response = reviews_table.get_item(Key={"review_id": review_id})
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Recenzija nije pronađena.")

    review = response["Item"]
    if review["username"] != username: 
        raise HTTPException(status_code=403, detail="Nemate dopuštenje za uređivanje ove recenzije.")
    update_data = updated_review.dict(exclude_unset=True)
    review.update(update_data)

    reviews_table.put_item(Item=review)

    return {"message": "Recenzija uspješno ažurirana!", "review": review}

# brisanje recenzije 
@router.delete("/{review_id}")
async def delete_review(review_id: str, auth=Depends(verify_token)):
    user_id = auth["user_id"]  
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://userservice:8002/users/me", headers={"Authorization": f"Bearer {auth['token']}"}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=404, detail="Korisnik nije pronađen")
            user_data = await resp.json()

    username = user_data["username"] 
    response = reviews_table.get_item(Key={"review_id": review_id})
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Recenzija nije pronađena.")

    review = response["Item"]
    if review["username"] != username:  
        raise HTTPException(status_code=403, detail="Nemate dopuštenje za brisanje ove recenzije.")

    reviews_table.delete_item(Key={"review_id": review_id})

    return {"message": "Recenzija uspješno obrisana!"}

