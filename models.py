from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=False)
    job_url = Column(String(512), nullable=True)
    resume_path = Column(String(512), nullable=False)
    cover_letter_path = Column(String(512), nullable=True)
    referrer_name = Column(String(255), nullable=True)
    referrer_email = Column(String(255), nullable=True)
    recruiter_name = Column(String(255), nullable=True)
    recruiter_email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="Applied")
    is_tailored = Column(Boolean, nullable=False, default=False)
    my_location = Column(String(255), nullable=True)
    applied_date = Column(DateTime, nullable=False, default=datetime.now) 