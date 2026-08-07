from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database.mongodb import emp_collection
from auth.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

class EmployeeLogin(BaseModel):
    email: EmailStr
    employee_id: str

@router.post("/login")
def login(creds: EmployeeLogin):
    user = emp_collection.find_one({
        "email": creds.email, 
        "employee_id": creds.employee_id
    })
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Email or Employee ID")
    
    # --- NEW LOGIC: Check the primary_category ---
    if user.get("primary_category") == "QA":
        role = "qa"
    else:
        # Fallback for admins or regular employees
        role = user.get("role", "employee")
    # ---------------------------------------------
    
    token = create_access_token(data={
        "empid": user["employee_id"], 
        "role": role
    })
    
    return {"access_token": token, "token_type": "bearer", "role": role}