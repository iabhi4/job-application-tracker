from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import os
from typing import Optional, List
import shutil
import uuid
from pydantic import BaseModel

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

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    referrer_name: Optional[str] = None
    referrer_email: Optional[str] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None

def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename."""
    return os.path.splitext(filename)[1]

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
        # Generate a unique identifier for this application
        application_id = str(uuid.uuid4())
        
        # Save resume with unique identifier
        resume_extension = get_file_extension(resume.filename)
        resume_path = f"uploads/resumes/{application_id}_resume{resume_extension}"
        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        
        # Save cover letter if provided
        cover_letter_path = None
        if cover_letter:
            cover_letter_extension = get_file_extension(cover_letter.filename)
            cover_letter_path = f"uploads/cover_letters/{application_id}_cover_letter{cover_letter_extension}"
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
    limit: int = 50,  # Increased default limit
    search: Optional[str] = None,
    status: Optional[str] = None
):
    db = SessionLocal()
    try:
        # Base query
        query = db.query(JobApplication)
        
        # Apply search filter if provided
        if search:
            search = f"%{search}%"
            query = query.filter(
                (JobApplication.company_name.ilike(search)) |
                (JobApplication.job_title.ilike(search)) |
                (JobApplication.referrer_name.ilike(search)) |
                (JobApplication.recruiter_name.ilike(search))
            )
        
        # Apply status filter if provided
        if status:
            query = query.filter(JobApplication.status == status)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        applications = query.order_by(JobApplication.applied_date.desc()).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "applications": applications,
            "page": skip // limit + 1,
            "total_pages": (total + limit - 1) // limit
        }
    finally:
        db.close()

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
    update_data: ApplicationUpdate
):
    print(f"Updating application {application_id} with data: {update_data}")
    db = SessionLocal()
    try:
        application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Update fields if provided
        if update_data.status is not None:
            print(f"Updating status from {application.status} to {update_data.status}")
            application.status = update_data.status
        if update_data.referrer_name is not None:
            application.referrer_name = update_data.referrer_name
        if update_data.referrer_email is not None:
            application.referrer_email = update_data.referrer_email
        if update_data.recruiter_name is not None:
            application.recruiter_name = update_data.recruiter_name
        if update_data.recruiter_email is not None:
            application.recruiter_email = update_data.recruiter_email
        
        try:
            db.commit()
            db.refresh(application)
            print(f"Successfully updated application. New status: {application.status}")
            return application
        except Exception as db_error:
            print(f"Database error during update: {str(db_error)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
    finally:
        db.close()

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