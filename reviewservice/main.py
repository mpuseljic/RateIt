from fastapi import FastAPI
from routes import review

app = FastAPI()

app.include_router(review.router, prefix="/reviews", tags=["Reviews"])

@app.get("/")
def root():
    return {"message": "Review servis"}
