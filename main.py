import os
import sys
from dotenv import load_dotenv

# --- DIRECTORY PATH FIX ---
# Ensures Python can find your 'database', 'agent', and 'tools' folders 
# if you run this script from inside a subfolder.
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# --------------------------

# MUST BE AT THE VERY TOP: Load environment variables before importing anything else!
load_dotenv()

import io
import pandas as pd

from agent.graph import graph
from database.mongodb import tasks_collection
from bson import ObjectId

# --- ADDED: Import the new email tool ---
from tools.email_tool import send_task_email
# ----------------------------------------

def process_excel(file_id: str):
    # Fetch Excel document from MongoDB
    document = tasks_collection.find_one({"_id": ObjectId(file_id)})

    if not document:
        raise Exception("Excel file not found.")

    # Convert binary data to DataFrame
    excel_bytes = io.BytesIO(document["file_data"])
    df = pd.read_excel(excel_bytes)

    # Check if the user forgot the "Task" header
    # If "Task" isn't found, we reload treating the first row as data, not a header!
    if "Task" not in df.columns.str.strip().str.title():
        excel_bytes.seek(0)  # Reset the file reader
        df = pd.read_excel(excel_bytes, header=None, names=["Task"])
    else:
        # Standardize the column names if the header DOES exist
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
        print(f"Department       : {employee['department']}")
        print(f"Designation      : {employee['designation']}")
        print(f"Experience       : {employee['experience']} Years")
        print(f"Performance      : {employee['performance_score']}")
        print(f"Current Tasks    : {employee['active_tasks']}")
        print(f"Email            : {employee['email']}")

        print("\nStatus")
        print("-" * 70)
        print(result["result"]["status"])

        # --- ADDED: Send the email to the assigned employee! ---
        print("\nSending Notification Email...")
        send_task_email(employee, task)
        # -------------------------------------------------------

        print("\n")


if __name__ == "__main__":
    import pymongo
    
    print("Fetching the most recently uploaded Excel file from MongoDB...")
    
    # --- FIXED: Changed excel_collection to tasks_collection ---
    # Sort by '_id' in descending order to get the newest file
    latest_document = tasks_collection.find_one({}, sort=[("_id", pymongo.DESCENDING)])
    # -----------------------------------------------------------
    
    if latest_document:
        print(f"Found file: {latest_document.get('filename')} | ID: {latest_document['_id']}\n")
        
        # Automatically process it!
        process_excel(str(latest_document["_id"]))
    else:
        print("No Excel files found in the database. Please upload one via the frontend first.")