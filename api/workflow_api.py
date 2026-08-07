from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime, timezone, timedelta
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
    tasks = list(workprogress_collection.find({"empid": user["empid"]}))
    for t in tasks:
        t["_id"] = str(t["_id"])
    return tasks

# ==========================================
# 2. UPDATE PROGRESS (Employee Only)
# ==========================================
@router.patch("/{task_id}/progress", dependencies=[Depends(RequireRole(["employee"]))])
def update_progress(task_id: str, update_data: TaskProgressUpdate, user: dict = Depends(get_current_user)):
    task = workprogress_collection.find_one({"_id": ObjectId(task_id)})
    if not task: raise HTTPException(404, "Task not found")
    if task["empid"] != user["empid"]: raise HTTPException(403, "You do not own this task")
    
    # Set offset for IST (UTC + 5:30)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    current_time = datetime.now(ist_tz).strftime('%Y-%m-%d %I:%M %p')
    
    new_entry = f"[{current_time}] {update_data.taskupdate}"
    
    existing_update = task.get("taskupdate", "")
    if existing_update:
        combined_update = existing_update + "\n" + new_entry
    else:
        combined_update = new_entry

    workprogress_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": "In Progress", "taskupdate": combined_update, "updatedAt": datetime.now(timezone.utc)}}
    )
    return {"message": "Progress updated successfully"}

# ==========================================
# 3. MARK COMPLETED (Employee Only)
# ==========================================
@router.patch("/{task_id}/complete", dependencies=[Depends(RequireRole(["employee"]))])
def complete_task(task_id: str, user: dict = Depends(get_current_user)):
    task = workprogress_collection.find_one({"_id": ObjectId(task_id)})
    if not task: raise HTTPException(404, "Task not found")
    if task["empid"] != user["empid"]: raise HTTPException(403, "You do not own this task")
    
    workprogress_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": "Under QA Review", "updatedAt": datetime.now(timezone.utc)}}
    )
    return {"message": "Task completed and sent to QA"}

# ==========================================
# 4. GET QA QUEUE (QA Only)
# ==========================================
@router.get("/qa-queue", dependencies=[Depends(RequireRole(["qa"]))])
def get_qa_queue():
    # Fetch tasks that are currently waiting for review OR have already been reviewed (they have remarks)
    tasks = list(workprogress_collection.find({
        "$or": [
            {"status": "Under QA Review"},
            {"remarks": {"$ne": "", "$exists": True}}
        ]
    }))
    
    for t in tasks: 
        t["_id"] = str(t["_id"])
    return tasks

# ==========================================
# 5. QA REVIEW (QA Only)
# ==========================================
@router.patch("/{task_id}/review", dependencies=[Depends(RequireRole(["qa"]))])
def review_task(task_id: str, review: TaskQAReview, user: dict = Depends(get_current_user)):
    task = workprogress_collection.find_one({"_id": ObjectId(task_id)})
    if not task: raise HTTPException(404, "Task not found")
    
    new_status = "In Progress" if review.status == "Rework Required" else "Approved"
    
    # Create IST timestamp for QA Audit trail
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    current_time = datetime.now(ist_tz).strftime('%Y-%m-%d %I:%M %p')
    
    action_text = "REJECTED (Rework)" if review.status == "Rework Required" else "APPROVED"
    new_remark_entry = f"[{current_time}] QA ({user['empid']}) - {action_text}:\n{review.remarks}"
    
    existing_remarks = task.get("remarks", "")
    if existing_remarks and existing_remarks != "None":
        combined_remarks = existing_remarks + "\n\n" + new_remark_entry
    else:
        combined_remarks = new_remark_entry

    workprogress_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": new_status, "remarks": combined_remarks, "updatedAt": datetime.now(timezone.utc)}}
    )
    return {"message": f"Task review complete. Status: {new_status}"}