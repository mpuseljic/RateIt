from fastapi import FastAPI
from routes import auth

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def root():
    return {"message": "Servis za autentifikaciju"}
