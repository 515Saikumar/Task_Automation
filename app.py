from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.upload_api import router as upload_router
from api.employee_api import router as employee_router
from api.auth_api import router as auth_router      
from api.workflow_api import router as workflow_router 

import uvicorn

app = FastAPI(title="AI Task Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(employee_router, prefix="/api")
app.include_router(auth_router)       
app.include_router(workflow_router)   

@app.get("/")
def health_check():
    return {"status": "Active", "message": "AI Task Manager is running!"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000, reload=True)