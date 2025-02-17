import aiohttp
import os
from fastapi import APIRouter, HTTPException, Request, Depends
from database import users_table
from models import UserFavorites

router = APIRouter()

# poziva auth servis da provjeri tokrn
async def get_current_user(request: Request):
    async with aiohttp.ClientSession() as session:
        async with session.get("http://authservice:8001/auth/verify", headers=request.headers) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=401, detail="Neispravni token")
            return await resp.json()

# vraća podatke korisnika na temelju tokena
@router.get("/me")
async def get_user_profile(user_data: dict = Depends(get_current_user)):
    username= user_data["username"]
    response = users_table.get_item(Key={"username": username})
    user = response.get("Item")
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")
    return {
        
        "username": user["username"],
        "email": user["email"]
    }
    
# dodavanje proizvoda u omiljeno
@router.post("/favorites/{product_name}")
async def add_favorite(product_name: str, user_data: dict = Depends(get_current_user)):
    username = user_data["username"]
    response = users_table.get_item(Key={"username": username})
    user = response.get("Item")
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    user["favorites"] = user.get("favorites", [])
    if product_name in user["favorites"]:
        raise HTTPException(status_code=400, detail="Proizvod je već u favoritima")

    user["favorites"].append(product_name)
    users_table.put_item(Item=user)
    return {"message": "Proizvod uspješno dodan u favorite"}

# pregled omiljenih proizvoda
@router.get("/favorites")
async def get_favorites(user_data: dict = Depends(get_current_user)):
    username = user_data["username"]
    response = users_table.get_item(Key={"username": username})
    user = response.get("Item")
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    return {"favorites": user.get("favorites", [])}

# uklanjanje proizvoda iz favorita
@router.delete("/favorites/{product_name}")
async def remove_favorite(product_name: str, user_data: dict = Depends(get_current_user)):
    username = user_data["username"]
    response = users_table.get_item(Key={"username": username})
    user = response.get("Item")
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    if product_name not in user.get("favorites", []):
        raise HTTPException(status_code=400, detail="Proizvod nije u favoritima")

    user["favorites"].remove(product_name)
    users_table.put_item(Item=user)
    return {"message": "Proizvod uspješno uklonjen iz favorita"}