from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URL")
if not MONGO_URI:
    raise ValueError("No MongoDB URI found. Please set MONGO_URI or MONGODB_URL in your .env file.")

DATABASE_NAME = os.getenv("DATABASE_NAME", "AI_Task")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

class EmployeeRepository:
    def __init__(self):
        # The MongoDB collection for employee records is named 'emp' in this database.
        self.collection = db["emp"]

    def get_all(self):
        employees = list(self.collection.find({}))
        for emp in employees:
            emp["_id"] = str(emp["_id"]) 
        return employees

    def add(self, employee_data: dict):
        result = self.collection.insert_one(employee_data)
        employee_data["_id"] = str(result.inserted_id)
        return employee_data

    # --- NEW UPDATE METHOD ---
    def update(self, employee_id: str, employee_data: dict):
        if "_id" in employee_data:
            del employee_data["_id"] # Don't try to update the immutable MongoDB _id
            
        result = self.collection.update_one(
            {"_id": ObjectId(employee_id)},
            {"$set": employee_data}
        )
        return result.matched_count > 0

    def delete(self, employee_id: str):
        result = self.collection.delete_one({"_id": ObjectId(employee_id)})
        return result.deleted_count > 0