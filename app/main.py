from fastapi import FastAPI
import redis
import psycopg2

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI app in Docker!"}
