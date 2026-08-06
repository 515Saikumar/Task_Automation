import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone # <-- ADDED timezone for proper timestamps

# --- DIRECTORY PATH FIX ---
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# --------------------------

# MUST BE AT THE VERY TOP: Load environment variables before importing anything else!
load_dotenv()

import io
import pandas as pd

from agent.graph import graph
# --- ADDED workprogress_collection import ---
from database.mongodb import tasks_collection, workprogress_collection
from bson import ObjectId

from tools.email_tool import send_task_email

def process_excel(file_id: str):
    # Fetch Excel document from MongoDB
    document = tasks_collection.find_one({"_id": ObjectId(file_id)})

    if not document:
        raise Exception("Excel file not found.")

    # Convert binary data to DataFrame
    excel_bytes = io.BytesIO(document["file_data"])
    df = pd.read_excel(excel_bytes)

    # Check if the user forgot the "Task" header
    if "Task" not in df.columns.str.strip().str.title():
        excel_bytes.seek(0)
        df = pd.read_excel(excel_bytes, header=None, names=["Task"])
    else:
        df.columns = df.columns.str.strip().str.title()

    # Process each task
    for i, task_text in enumerate(df["Task"], start=1):
        
        initial_state = {
            "input_text": task_text,
            "parsed_task": {},
            "duplicate": False,
            "project": None,
            "due_date_valid": False,
            "result": {}
        }

        result = graph.invoke(initial_state)

        allocation = result.get("allocation") or {}
        if not allocation.get("success", True):
            print("\nAllocation failed for task:", task_text)
            print("Reason:", allocation.get("message", "Unknown allocation error."))
            continue

        task = result["task"]
        employee = allocation.get("assigned_employee")
        if not employee:
            print("\nAllocation completed but no assigned employee was returned for task:", task_text)
            continue

        print("=" * 70)
        print(f"TASK {i}")
        print("=" * 70)

        print(f"Task Name        : {task['task_name']}")
        print(f"Description      : {task['description']}")
        print(f"Category         : {task['category']}")
        print(f"Priority         : {task['priority']}")
        print(f"Due Date         : {task['due_date']}")

        print("\nAssigned Employee")
        print("-" * 70)
        print(f"Employee ID      : {employee['employee_id']}")
        print(f"Name             : {employee['name']}")
        print(f"Email            : {employee['email']}")

        # --- Send the email ---
        print("\nSending Notification Email...")
        send_task_email(employee, task)
        
        # --- NEW: PREVENT DUPLICATES & SAVE TO WORKPROGRESS ---
        print("Checking for duplicates in workprogress database...")
        
        # Ensure the date is stored as a proper string or datetime
        due_date_val = task.get('due_date', '')
        try:
            # Try to format it cleanly if the LLM returned YYYY-MM-DD
            due_date_val = datetime.strptime(due_date_val, "%Y-%m-%d")
        except:
            pass # Keep it as a string if it's words like "ASAP" or "Not Specified"

        # Check if this exact task is already active for this employee
        existing_task = workprogress_collection.find_one({
            "empid": employee['employee_id'],
            "task": task['task_name'],
            "status": {"$in": ["Assigned", "In Progress", "Rework Required", "Under QA Review"]}
        })

        if existing_task:
            print(f"⚠️ Duplicate detected: '{task['task_name']}' is already assigned to {employee['name']}. Skipping database insert.")
        else:
            workprogress_doc = {
                "empid": employee['employee_id'],
                "task": task['task_name'],
                "duedate": due_date_val,
                "taskupdate": "",
                "status": "In Progress", 
                "remarks": "",
                "createdAt": datetime.now(timezone.utc), # <-- FIXED Deprecation warning
                "updatedAt": datetime.now(timezone.utc)  # <-- FIXED Deprecation warning
            }
            
            workprogress_collection.insert_one(workprogress_doc)
            print("✅ Task successfully added to workprogress!")
        # ---------------------------------------------

        print("\n")


if __name__ == "__main__":
    import pymongo
    
    print("Fetching the most recently uploaded Excel file from MongoDB...")
    latest_document = tasks_collection.find_one({}, sort=[("_id", pymongo.DESCENDING)])
    
    if latest_document:
        print(f"Found file: {latest_document.get('filename')} | ID: {latest_document['_id']}\n")
        process_excel(str(latest_document["_id"]))
    else:
        print("No Excel files found in the database. Please upload one via the frontend first.")