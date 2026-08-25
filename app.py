# ============================================================
# app.py
# ============================================================

# -----------------------------
# Python standard library
# -----------------------------
import json
from datetime import datetime

# -----------------------------
# FastAPI imports
# -----------------------------
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# -----------------------------
# LangChain imports
# -----------------------------
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

# -----------------------------
# Existing project imports
# -----------------------------
from api.upload_api import router as upload_router
from api.auth_api import router as auth_router
from api.employee_api import router as employee_router
from api.workflow_api import router as workflow_router
from database.mongodb import workprogress_collection, tasks_collection


# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Task Automation API",
    description="Task Automation and Employee Work Progress API",
    version="1.0.0"
)

# ============================================================
# CORS MIDDLEWARE (FIX FOR BLOCKED REQUESTS / 405 ERRORS)
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


# ============================================================
# REGISTER ROUTERS
# ============================================================

app.include_router(upload_router)
app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(workflow_router)


# ============================================================
# GET RECENT EXCEL FILES (FIX FOR /api/tasks 404)
# ============================================================

@app.get("/api/tasks")
def get_recent_task_files():
    """
    Fetches the list of recently uploaded Excel files for the Admin Dashboard.
    Excludes the heavy binary 'file_data' to keep the response fast.
    """
    try:
        files = list(tasks_collection.find({}, {"file_data": 0}))
        
        result = []
        for f in files:
            result.append({
                "_id": str(f["_id"]),
                "filename": f.get("filename", "Unknown File"),
                "status": f.get("status", "Uploaded"),
                "uploaded_at": f.get("uploaded_at", datetime.now().isoformat())
            })
            
        return result
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []


# ============================================================
# UPLOAD EXCEL FILE (FIX FOR /api/upload-excel 404)
# ============================================================

@app.post("/api/upload-excel")
async def upload_excel_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Receives the Excel file from the React Admin Dashboard, saves it to MongoDB,
    and triggers the AI processing pipeline in the background.
    """
    try:
        # Read the file data as bytes
        file_data = await file.read()
        
        # Create the document for MongoDB
        doc = {
            "filename": file.filename,
            "file_data": file_data,
            "status": "Uploaded",
            "uploaded_at": datetime.now().isoformat()
        }
        
        # Insert into the database
        result = tasks_collection.insert_one(doc)
        file_id = str(result.inserted_id)
        
        # Import your processing function from main.py
        try:
            from main import process_excel
            # Run the AI allocation in the background so the UI doesn't hang
            background_tasks.add_task(process_excel, file_id)
        except ImportError:
            print("⚠️ Could not import process_excel from main.py. Is main.py in the same directory?")
        
        return {"success": True, "file_id": file_id}
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return {"success": False, "detail": str(e)}


# ============================================================
# WORK PROGRESS DATABASE TOOL
# ============================================================

@tool
def query_workprogress(search_term: str) -> str:
    """
    Queries employee work progress from MongoDB.

    Input should be a search term such as:
    - employee ID
    - task name
    - status
    """
    try:
        query = {
            "$or": [
                {
                    "empid": {
                        "$regex": search_term,
                        "$options": "i"
                    }
                },
                {
                    "task": {
                        "$regex": search_term,
                        "$options": "i"
                    }
                },
                {
                    "status": {
                        "$regex": search_term,
                        "$options": "i"
                    }
                }
            ]
        }

        # Query MongoDB
        results = list(
            workprogress_collection.find(
                query,
                {
                    "_id": 0
                }
            )
        )

        # No results
        if not results:
            return (
                f"No work progress found for "
                f"'{search_term}'."
            )

        # Convert datetime values to JSON-compatible strings
        for doc in results:
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.isoformat()

        # Return results as JSON string
        return json.dumps(
            results,
            default=str
        )

    except Exception as e:
        return (
            f"Error querying database: {str(e)}"
        )


# ============================================================
# INITIALIZE OPENAI LLM
# ============================================================

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# ============================================================
# LANGCHAIN TOOLS
# ============================================================

tools = [
    query_workprogress
]


# ============================================================
# LANGCHAIN PROMPT
# ============================================================

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a helpful HR and Project Management assistant.

You can access employee work progress information
from the MongoDB database using the provided tools.

When the user asks about:

- Employee work progress
- Employee ID
- Tasks
- Task status
- Completed tasks
- Pending tasks
- Employee activity

use the database tool to retrieve the relevant information.

Answer the user clearly and concisely.

Do not invent employee information.

If the database does not contain the requested information,
clearly tell the user that no matching records were found.
"""
        ),
        (
            "human",
            "{input}"
        ),
        (
            "placeholder",
            "{agent_scratchpad}"
        )
    ]
)


# ============================================================
# CREATE TOOL-CALLING AGENT
# ============================================================

agent = create_tool_calling_agent(
    llm,
    tools,
    prompt
)


# ============================================================
# CREATE AGENT EXECUTOR
# ============================================================

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)


# ============================================================
# CHAT REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    message: str


# ============================================================
# CHAT API
# ============================================================

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    try:
        # Run LangChain agent
        response = agent_executor.invoke(
            {
                "input": request.message
            }
        )

        return {
            "response": response["output"]
        }

    except Exception as e:
        return {
            "response": (
                f"Sorry, I encountered an error: "
                f"{str(e)}"
            )
        }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Task Automation API is running",
        "status": "success"
    }


# ============================================================
# API HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=10000, 
        reload=True
    )