# 📝 Job Application Tracker

A personal-use web app to track your job applications. Built with FastAPI (backend), SQLite (database), and Streamlit (frontend).

## Features

- **Add a Job Application**
  - Enter job title, company name, and job description
  - Upload resume (required) and cover letter (optional)
  - Add associated people (referrer, recruiter)
  - Track application status (Applied, Rejected, Assessment, Interview, Offer)
  - Auto-captures the date applied

- **View Applications**
  - See all applications in a searchable/filterable table
  - View/download attached files
  - View full job description
  - Update status or associated people
  - Delete an entry

- **Statistics Dashboard**
  - See total applications, and counts for today, this week, and this month

## Tech Stack
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Database:** SQLite (SQLAlchemy ORM)
- **File Storage:** Local `uploads/` folder

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repo-url>
cd job-application-tracker
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the FastAPI Backend
```bash
python main.py
```
- The API will be available at [http://localhost:8000](http://localhost:8000)
- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Run the Streamlit Frontend
In a new terminal (with the virtual environment activated):
```bash
streamlit run app.py
```
- The app will be available at [http://localhost:8501](http://localhost:8501)

## File Uploads
- Uploaded resumes and cover letters are stored in `uploads/resumes/` and `uploads/cover_letters/`.
- These folders are auto-created by the app if missing.
- Uploaded files are **not** tracked by git (see `.gitignore`).
- To keep the folder structure in git, a `.gitkeep` file is included.

## Database
- The app uses a local SQLite database (`db.sqlite`).
- If you change the database schema, you may need to delete `db.sqlite` and restart the backend (for development/testing).

## Notes
- No authentication: this is a single-user, personal-use app.
- If you want to deploy or use with multiple users, add authentication and use a production database.

## Screenshots
_Add screenshots here if desired._

## License
MIT (or your chosen license)
