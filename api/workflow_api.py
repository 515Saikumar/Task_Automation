from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from database.mongodb import workprogress_collection, emp_collection
from auth.security import get_current_user, RequireRole
from pydantic import BaseModel

router = APIRouter(prefix="/tasks", tags=["Workflow Tracking"])

class TaskProgressUpdate(BaseModel):
    taskupdate: str

class TaskQAReview(BaseModel):
    remarks: str
    status: str

class TaskReassign(BaseModel):
    new_empid: str

class ManualTaskAllocation(BaseModel):
    empid: str
    task: str
    description: str = ""
    priority: str = "Normal"
    category: str = "General"
    due_date: str = ""

# ==========================================
# 0. MANUAL TASK ALLOCATION (Admin/Manager)
# ==========================================
@router.post("/allocate")
def allocate_task_manually(task_data: ManualTaskAllocation):
    emp = emp_collection.find_one({"employee_id": task_data.empid})
    if not emp:
        raise HTTPException(404, "Employee not found")
        
    try:
        due_date_val = datetime.strptime(task_data.due_date, "%Y-%m-%d") if task_data.due_date else ""
    except ValueError:
        due_date_val = task_data.due_date
        
    workprogress_doc = {
        "empid": emp["employee_id"],
        "empname": emp["name"],
        "task": task_data.task,
        "description": task_data.description,
        "priority": task_data.priority,
        "required_skills": [],
        "category": task_data.category,
        "dependencies": [],
        "duedate": due_date_val,
        "taskupdate": "",
        "status": "In Progress",
        "remarks": "",
        "contributors": [],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }
    
    workprogress_collection.insert_one(workprogress_doc)
    
    new_active = emp.get("active_tasks", 0) + 1
    max_tasks = emp.get("max_tasks", 4)
    new_availability = new_active < max_tasks
    
    emp_collection.update_one(
        {"employee_id": emp["employee_id"]},
        {"$set": {
            "active_tasks": new_active,
            "availability": new_availability
        }}
    )
    
    return {"message": f"Task '{task_data.task}' manually assigned to {emp['name']}."}

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
# 2.5 REASSIGN TASK (Employee Only)
# ==========================================
@router.patch("/{task_id}/reassign", dependencies=[Depends(RequireRole(["employee"]))])
def reassign_task(task_id: str, reassign_data: TaskReassign, user: dict = Depends(get_current_user)):
    task = workprogress_collection.find_one({"_id": ObjectId(task_id)})
    if not task: raise HTTPException(404, "Task not found")
    if task["empid"] != user["empid"]: raise HTTPException(403, "You do not own this task")
    
    new_emp = emp_collection.find_one({"employee_id": reassign_data.new_empid})
    if not new_emp: raise HTTPException(404, "New employee not found")
    
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    current_time = datetime.now(ist_tz).strftime('%Y-%m-%d %I:%M %p')
    
    new_entry = f"[{current_time}] [System] Task reassigned from {task['empname']} ({task['empid']}) to {new_emp['name']} ({new_emp['employee_id']}) due to leave/reassignment."
    
    existing_update = task.get("taskupdate", "")
    combined_update = existing_update + "\n" + new_entry if existing_update else new_entry
    
    # Maintain contributors history
    contributors = task.get("contributors", [])
    if task["empid"] not in [c["empid"] for c in contributors]:
        contributors.append({"empid": task["empid"], "name": task["empname"]})
    
    workprogress_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {
            "empid": new_emp["employee_id"],
            "empname": new_emp["name"],
            "taskupdate": combined_update,
            "contributors": contributors,
            "updatedAt": datetime.now(timezone.utc)
        }}
    )
    
    # Update active tasks count
    old_emp = emp_collection.find_one({"employee_id": task["empid"]})
    if old_emp:
        emp_collection.update_one({"employee_id": task["empid"]}, {"$set": {"active_tasks": max(0, old_emp.get("active_tasks", 1) - 1)}})
    emp_collection.update_one({"employee_id": new_emp["employee_id"]}, {"$set": {"active_tasks": new_emp.get("active_tasks", 0) + 1}})
    
    return {"message": f"Task reassigned successfully to {new_emp['name']}."}

# ==========================================
# 3. MARK COMPLETED (Employee Only)
# ==========================================
@router.patch("/{task_id}/complete", dependencies=[Depends(RequireRole(["employee"]))])
def complete_task(task_id: str, user: dict = Depends(get_current_user)):
    task = workprogress_collection.find_one({"_id": ObjectId(task_id)})
    if not task: raise HTTPException(404, "Task not found")
    if task["empid"] != user["empid"]: raise HTTPException(403, "You do not own this task")
    
    # Find an available QA engineer (preferably one with the least active tasks)
    qa_emp = emp_collection.find_one(
        {"primary_category": "QA"}, 
        sort=[("active_tasks", 1)]
    )
    
    qa_name = qa_emp["name"] if qa_emp else "QA Team"
    qa_id = qa_emp["employee_id"] if qa_emp else "UNASSIGNED"

    workprogress_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {
            "status": "Under QA Review", 
            "assigned_qa": qa_id,
            "qa_name": qa_name,
            "updatedAt": datetime.now(timezone.utc)
        }}
    )
    
    # If we assigned a QA, we could increment their active_tasks here if desired, 
    # but for now, just tagging them is enough to notify the employee.
    
    return {"message": f"Task completed and sent to {qa_name} for QA review."}

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
    
    if new_status == "Approved":
        emp = emp_collection.find_one({"employee_id": task["empid"]})
        if emp:
            new_active = max(0, emp.get("active_tasks", 1) - 1)
            max_tasks = emp.get("max_tasks", 4)
            new_availability = new_active < max_tasks
            
            emp_collection.update_one(
                {"employee_id": task["empid"]},
                {"$set": {
                    "active_tasks": new_active,
                    "availability": new_availability
                }}
            )
    elif review.status == "Rework Required":
        # Initialize at 100 if missing, and decrease by 2 for the rework remark
        emp = emp_collection.find_one({"employee_id": task["empid"]})
        if emp:
            current_score = emp.get("performance_score", 100)
            emp_collection.update_one(
                {"employee_id": task["empid"]},
                {"$set": {"performance_score": current_score - 2}}
            )

    return {"message": f"Task review complete. Status: {new_status}"}