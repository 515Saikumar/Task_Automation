import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone 

# --- NEW: Imports for FastAPI & AI Chatbot ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from langchain_openai import ChatOpenAI
try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    try:
        from langchain.agents.agent import AgentExecutor
        from langchain.agents.tool_calling_agent.base import create_tool_calling_agent
    except ImportError:
        try:
            from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
        except ImportError as e:
            raise ImportError(
                "Could not import AgentExecutor. In newer LangChain versions, "
                "AgentExecutor is moved. Please run `pip install langchain-classic` "
                "or install an older version of LangChain."
            ) from e
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
# ---------------------------------------------

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

load_dotenv()

import io
import pandas as pd
import pymongo # Moved to top level for AI tool access if needed

from agent.graph import graph
from database.mongodb import tasks_collection, workprogress_collection, emp_collection
from bson import ObjectId
from tools.email_tool import send_task_email

# ==========================================
# NEW: AI Chatbot Tool & Agent Configuration
# ==========================================

@tool
def query_workprogress(search_term: str) -> str:
    """
    Queries employee work progress from MongoDB. 
    Input should be a search term like an employee's ID, task name, or status.
    """
    try:
        query = {
            "$or": [
                {"empid": {"$regex": search_term, "$options": "i"}},
                {"task": {"$regex": search_term, "$options": "i"}},
                {"status": {"$regex": search_term, "$options": "i"}}
            ]
        }
        
        # Exclude ObjectId for clean JSON parsing
        results = list(workprogress_collection.find(query, {"_id": 0}))
        
        if not results:
            return f"No work progress found for '{search_term}'."
            
        # Convert datetime objects to strings before JSON serialization
        for doc in results:
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.isoformat()
                    
        return json.dumps(results)
    except Exception as e:
        return f"Error querying database: {str(e)}"

# Initialize the LangChain Agent
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = [query_workprogress]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful HR and Project Management assistant. Use the provided tools to fetch employee work progress from the database and answer user queries clearly and concisely."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# ==========================================
# NEW: FastAPI Application Setup
# ==========================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = agent_executor.invoke({"input": request.message})
        return {"response": response["output"]}
    except Exception as e:
        return {"response": f"Sorry, I encountered an error: {str(e)}"}


# ==========================================
# EXISTING: Excel Processing Logic
# ==========================================

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
                "empname": employee['name'],
                "task": task['task_name'],
                "description": task.get('description', ''),
                "priority": task.get('priority', 'Normal'),
                "required_skills": task.get('required_skills', []),
                "category": task.get('category', 'General'),
                "dependencies": task.get('dependencies', []),
                "duedate": due_date_val,
                "taskupdate": "",
                "status": "In Progress", 
                "remarks": "",
                "createdAt": datetime.now(timezone.utc), 
                "updatedAt": datetime.now(timezone.utc)  
            }
            workprogress_collection.insert_one(workprogress_doc)
            
            emp = emp_collection.find_one({"employee_id": employee['employee_id']})
            if emp:
                new_active = emp.get("active_tasks", 0) + 1
                max_tasks = emp.get("max_tasks", 4)
                new_availability = new_active < max_tasks
                
                emp_collection.update_one(
                    {"employee_id": employee['employee_id']},
                    {"$set": {
                        "active_tasks": new_active,
                        "availability": new_availability
                    }}
                )
            print("✅ Task successfully added to workprogress and employee active_tasks updated!")

        print("\n")


if __name__ == "__main__":
    # If run directly as a script (e.g., python main.py), it will execute the manual pipeline
    print("Fetching the most recently uploaded Excel file from MongoDB...")
    latest_document = tasks_collection.find_one({}, sort=[("_id", pymongo.DESCENDING)])
    
    if latest_document:
        print(f"Found file: {latest_document.get('filename')}")
        process_excel(str(latest_document["_id"]))
    else:
        print("No Excel files found.")
        
    # NOTE: To run the FastAPI server, use the terminal command:
    # uvicorn main:app --reload