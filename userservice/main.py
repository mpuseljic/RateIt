from fastapi import FastAPI
from routes import user

app = FastAPI()

app.include_router(user.router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "User Service Running"}