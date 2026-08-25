from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from repository.excel_repository import ExcelRepository
from database.mongodb import tasks_collection, workprogress_collection
from main import process_excel

router = APIRouter(tags=["Excel Upload"])

@router.post("/upload-excel")
async def upload_excel(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_bytes = await file.read()
    file_id = ExcelRepository.save_excel(
        filename=file.filename,
        content_type=file.content_type,
        file_bytes=file_bytes
    )
    background_tasks.add_task(process_excel, str(file_id))
    return {
        "success": True,
        "message": "Excel uploaded successfully. AI Task allocation is running in the background!",
        "file_id": file_id
    }

@router.get("/tasks")
def get_excel_files():
    # Exclude the heavy binary data when just listing files
    files = list(tasks_collection.find({}, {"file_data": 0}))
    for f in files:
        f["_id"] = str(f["_id"])
    return files

# --- ADDED: Delete Route ---
@router.delete("/tasks/{file_id}")
def delete_excel_file(file_id: str):
    success = ExcelRepository.delete_excel(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"success": True, "message": "File deleted successfully"}

@router.get("/admin/tasks-overview")
def get_admin_tasks_overview():
    tasks = list(workprogress_collection.find().sort("createdAt", -1))
    for t in tasks:
        t["_id"] = str(t["_id"])
    
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("status") == "Approved" or t.get("status") == "Done")
    ongoing_tasks = total_tasks - completed_tasks
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "ongoing_tasks": ongoing_tasks,
        "tasks": tasks
    }

@router.get("/admin/groq-models")
def get_groq_models():
    import os
    import requests
    from dotenv import load_dotenv
    load_dotenv()
    headers={'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}'}
    res = requests.get('https://api.groq.com/openai/v1/models', headers=headers)
    return res.json()