from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database.mongodb import emp_collection
from auth.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

class EmployeeLogin(BaseModel):
    email: EmailStr
    employee_id: str  # Acting as our password

@router.post("/login")
def login(creds: EmployeeLogin):
    # Find the employee matching BOTH email and employee_id
    user = emp_collection.find_one({
        "email": creds.email, 
        "employee_id": creds.employee_id
    })
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Email or Employee ID")
    
    # If role isn't set in your DB yet, default them to 'employee'
    # If the user is an admin, you can manually add "role": "admin" to their MongoDB document
    role = user.get("role", "employee")
    
    # Generate the JWT Token
    token = create_access_token(data={
        "empid": user["employee_id"], 
        "role": role
    })
    
    return {"access_token": token, "token_type": "bearer", "role": role}