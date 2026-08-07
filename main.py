import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone 

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

load_dotenv()

import io
import pandas as pd

from agent.graph import graph
from database.mongodb import tasks_collection, workprogress_collection
from bson import ObjectId
from tools.email_tool import send_task_email

def process_excel(file_id: str):
    document = tasks_collection.find_one({"_id": ObjectId(file_id)})
    if not document:
        raise Exception("Excel file not found.")

    excel_bytes = io.BytesIO(document["file_data"])
    df = pd.read_excel(excel_bytes)

    if "Task" not in df.columns.str.strip().str.title():
        excel_bytes.seek(0)
        df = pd.read_excel(excel_bytes, header=None, names=["Task"])
    else:
        df.columns = df.columns.str.strip().str.title()

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
            continue

        task = result["task"]
        employee = allocation.get("assigned_employee")
        if not employee:
            continue

        print("=" * 70)
        print(f"TASK {i} - Assigned to {employee['name']}")
        print("=" * 70)

        send_task_email(employee, task)
        
        due_date_val = task.get('due_date', '')
        try:
            due_date_val = datetime.strptime(due_date_val, "%Y-%m-%d")
        except:
            pass 

        existing_task = workprogress_collection.find_one({
            "empid": employee['employee_id'],
            "task": task['task_name'],
            "status": {"$in": ["Assigned", "In Progress", "Rework Required", "Under QA Review"]}
        })

        if existing_task:
            print(f"⚠️ Duplicate detected: '{task['task_name']}' is already assigned. Skipping database insert.")
        else:
            workprogress_doc = {
                "empid": employee['employee_id'],
                "task": task['task_name'],
                "duedate": due_date_val,
                "taskupdate": "",
                "status": "In Progress", 
                "remarks": "",
                "createdAt": datetime.now(timezone.utc), 
                "updatedAt": datetime.now(timezone.utc)  
            }
            workprogress_collection.insert_one(workprogress_doc)
            print("✅ Task successfully added to workprogress!")

        print("\n")


if __name__ == "__main__":
    import pymongo
    
    print("Fetching the most recently uploaded Excel file from MongoDB...")
    latest_document = tasks_collection.find_one({}, sort=[("_id", pymongo.DESCENDING)])
    
    if latest_document:
        print(f"Found file: {latest_document.get('filename')}")
        process_excel(str(latest_document["_id"]))
    else:
        print("No Excel files found.")