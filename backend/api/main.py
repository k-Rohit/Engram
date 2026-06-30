import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message" : "Hello!"}

@app.get("/health")
def check_health():
    return {"status": "Healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, log_level="info")