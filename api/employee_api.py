from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from repository.employee_repository import EmployeeRepository

router = APIRouter(tags=["Emp"])
repo = EmployeeRepository()

# Updated schema matching your MongoDB structure
class EmployeeSchema(BaseModel):
    employee_id: str
    name: str
    department: str
    designation: str
    primary_category: str
    secondary_categories: Optional[List[str]] = []
    skills: Optional[List[str]] = []
    experience: int = 0
    availability: bool = True
    active_tasks: int = 0
    max_tasks: int = 5
    performance_score: int = 100
    email: str

@router.get("/emp")
def get_employees():
    return repo.get_all()

@router.post("/emp")
def add_employee(emp: EmployeeSchema):
    return repo.add(emp.model_dump())

# --- NEW PUT ROUTE FOR EDITING ---
@router.put("/emp/{employee_id}")
def update_employee(employee_id: str, emp: EmployeeSchema):
    success = repo.update(employee_id, emp.model_dump())
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"success": True, "message": "Employee updated successfully"}

@router.delete("/emp/{employee_id}")
def delete_employee(employee_id: str):
    success = repo.delete(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"success": True, "message": "Employee deleted successfully"}