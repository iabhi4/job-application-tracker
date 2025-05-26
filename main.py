from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import os
from typing import Optional, List
import shutil

from models import JobApplication, Base
from database import engine, SessionLocal
from scraper import scrape_job_info

# Create upload directories if they don't exist
os.makedirs("uploads/resumes", exist_ok=True)
os.makedirs("uploads/cover_letters", exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Job Application Tracker")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded documents
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.post("/applications/")
async def create_application(
    job_title: str = Form(...),
    company_name: str = Form(...),
    job_description: str = Form(...),
    resume: UploadFile = File(...),
    cover_letter: Optional[UploadFile] = File(None),
    referrer_name: Optional[str] = Form(None),
    referrer_email: Optional[str] = Form(None),
    recruiter_name: Optional[str] = Form(None),
    recruiter_email: Optional[str] = Form(None),
    status: str = Form("Applied")
):
    try:
        # Save resume
        resume_path = f"uploads/resumes/{resume.filename}"
        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        
        # Save cover letter if provided
        cover_letter_path = None
        if cover_letter:
            cover_letter_path = f"uploads/cover_letters/{cover_letter.filename}"
            with open(cover_letter_path, "wb") as buffer:
                shutil.copyfileobj(cover_letter.file, buffer)
        
        # Create database entry
        db = SessionLocal()
        application = JobApplication(
            company_name=company_name,
            job_title=job_title,
            job_description=job_description,
            job_url=None,
            resume_path=resume_path,
            cover_letter_path=cover_letter_path,
            referrer_name=referrer_name,
            referrer_email=referrer_email,
            recruiter_name=recruiter_name,
            recruiter_email=recruiter_email,
            status=status,
            applied_date=datetime.now()
        )
        
        db.add(application)
        db.commit()
        db.refresh(application)
        db.close()
        
        return JSONResponse(content={"message": "Application created successfully", "id": application.id})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/applications/")
async def get_applications(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    status: Optional[str] = None
):
    db = SessionLocal()
    query = db.query(JobApplication)
    
    if search:
        search = f"%{search}%"
        query = query.filter(
            (JobApplication.company_name.ilike(search)) |
            (JobApplication.job_title.ilike(search)) |
            (JobApplication.referrer_name.ilike(search)) |
            (JobApplication.recruiter_name.ilike(search))
        )
    
    if status:
        query = query.filter(JobApplication.status == status)
    
    total = query.count()
    applications = query.offset(skip).limit(limit).all()
    db.close()
    
    return {
        "total": total,
        "applications": applications
    }

@app.get("/applications/{application_id}")
async def get_application(application_id: int):
    db = SessionLocal()
    application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    db.close()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application

@app.put("/applications/{application_id}")
async def update_application(
    application_id: int,
    status: Optional[str] = None,
    referrer_name: Optional[str] = None,
    referrer_email: Optional[str] = None,
    recruiter_name: Optional[str] = None,
    recruiter_email: Optional[str] = None
):
    db = SessionLocal()
    application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    
    if not application:
        db.close()
        raise HTTPException(status_code=404, detail="Application not found")
    
    if status:
        application.status = status
    if referrer_name:
        application.referrer_name = referrer_name
    if referrer_email:
        application.referrer_email = referrer_email
    if recruiter_name:
        application.recruiter_name = recruiter_name
    if recruiter_email:
        application.recruiter_email = recruiter_email
    
    db.commit()
    db.refresh(application)
    db.close()
    
    return application

@app.delete("/applications/{application_id}")
async def delete_application(application_id: int):
    db = SessionLocal()
    application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    
    if not application:
        db.close()
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Delete associated files
    if application.resume_path and os.path.exists(application.resume_path):
        os.remove(application.resume_path)
    if application.cover_letter_path and os.path.exists(application.cover_letter_path):
        os.remove(application.cover_letter_path)
    
    db.delete(application)
    db.commit()
    db.close()
    
    return {"message": "Application deleted successfully"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 