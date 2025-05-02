import os
import redis
import asyncpg
import logging
import json
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)

# PostgreSQL Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/postgres")

# Create FastAPI instance
app = FastAPI()

# Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("startup")
async def startup():
    retries = 5
    for _ in range(retries):
        try:
            # Try connecting to PostgreSQL
            app.state.pool = await asyncpg.create_pool(DATABASE_URL)
            logging.info("Database connection successful.")
            break
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
    else:
        logging.error("Exceeded maximum retries for connecting to the database.")
        raise Exception("Could not connect to the database.")

@app.on_event("shutdown")
async def shutdown():
    if app.state.pool:
        await app.state.pool.close()
        logging.info("Database pool closed.")

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI!"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # Check Redis for cached user data
    cached_data = redis_client.get(f"user:{user_id}")
    
    if cached_data:
        return {"user": json.loads(cached_data)}
    
    # Fetch from PostgreSQL if not in cache
    async with app.state.pool.acquire() as connection:
        try:
            result = await connection.fetchrow('SELECT * FROM users WHERE id=$1', user_id)
            if result:
                redis_client.setex(f"user:{user_id}", 3600, json.dumps(dict(result)))
                return {"user": dict(result)}
            return {"message": "User not found"}
        except Exception as e:
            logging.error(f"Error fetching user from database: {e}")
            return {"message": "Database error occurred."}

# Pydantic models for request validation (if needed)
class User(BaseModel):
    id: int
    name: str
    email: str
