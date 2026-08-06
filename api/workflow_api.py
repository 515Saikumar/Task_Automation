from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime, timezone
from database.mongodb import workprogress_collection
from auth.security import get_current_user, RequireRole
from pydantic import BaseModel

router = APIRouter(prefix="/tasks", tags=["Workflow Tracking"])

class TaskProgressUpdate(BaseModel):
    taskupdate: str

class TaskQAReview(BaseModel):
    remarks: str
    status: str

# ==========================================
# 1. GET OWN TASKS (Employee Only)
# ==========================================
@router.get("/my", dependencies=[Depends(RequireRole(["employee"]))])
def get_my_tasks(user: dict = Depends(get_current_user)):
    # Fetch all tasks from workprogress where the empid matches the logged-in user
    tasks = list(workprogress_collection.find({"empid": user["empid"]}))
    
    # MongoDB ObjectIds must be converted to strings for JSON
    for t in tasks:
        t["_id"] = str(t["_id"])
    return tasks

# ==========================================
# 2. UPDATE PROGRESS (Employee Only)
# ==========================================
@router.patch("/{task_id}/progress", dependencies=[Depends(RequireRole(["employee"]))])
def update_progress(task_id: str, update_data: TaskProgressUpdate, user: dict = Depends(get_current_user)):
    task = workprogress_collection.find_one({"_id": ObjectId(task_id)})
    if not task: 
        raise HTTPException(404, "Task not found")
    if task["empid"] != user["empid"]: 
        raise HTTPException(403, "You do not own this task")
    
    workprogress_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {
            "status": "In Progress", 
            "taskupdate": update_data.taskupdate, 
            "updatedAt": datetime.now(timezone.utc)
        }}
    )
    return {"message": "Task progress updated"}

# ==========================================
# 3. MARK COMPLETED (Employee Only)
# ==========================================
@router.patch("/{task_id}/complete", dependencies=[Depends(RequireRole(["employee"]))])
def complete_task(task_id: str, user: dict = Depends(get_current_user)):
    task = workprogress_collection.find_one({"_id": ObjectId(task_id)})
    if not task: 
        raise HTTPException(404, "Task not found")
    if task["empid"] != user["empid"]: 
        raise HTTPException(403, "You do not own this task")
    
    workprogress_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {
            "status": "Under QA Review", 
            "updatedAt": datetime.now(timezone.utc)
        }}
    )
    return {"message": "Task completed and sent to QA"}

# ==========================================
# 4. GET QA QUEUE (QA Only)
# ==========================================
@router.get("/qa-queue", dependencies=[Depends(RequireRole(["qa"]))])
def get_qa_queue():
    tasks = list(workprogress_collection.find({"status": "Under QA Review"}))
    for t in tasks: 
        t["_id"] = str(t["_id"])
    return tasks

# ==========================================
# 5. QA REVIEW (QA Only)
# ==========================================
@router.patch("/{task_id}/review", dependencies=[Depends(RequireRole(["qa"]))])
def review_task(task_id: str, review: TaskQAReview):
    task = workprogress_collection.find_one({"_id": ObjectId(task_id)})
    if not task: 
        raise HTTPException(404, "Task not found")
    
    new_status = "In Progress" if review.status == "Rework Required" else "Approved"
    
    workprogress_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {
            "status": new_status, 
            "remarks": review.remarks, 
            "updatedAt": datetime.now(timezone.utc)
        }}
    )
    return {"message": f"Task review complete. Status: {new_status}"}