import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from the ai/.env file
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "AI_Task")

if not MONGO_URI:
    raise ValueError("No MongoDB URI found. Please set MONGO_URI or MONGODB_URL in your .env file.")

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Export collections
tasks_collection = db["tasks"]
emp_collection = db["emp"]