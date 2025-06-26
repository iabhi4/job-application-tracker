import logging
logging.getLogger("watchdog").setLevel(logging.WARNING)
import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import os
from typing import Optional
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
API_URL = "http://localhost:8000"
STATUS_OPTIONS = ["Applied", "Rejected", "Assessment", "Interview", "Offer"]

# Page config
st.set_page_config(
    page_title="Job Application Tracker",
    page_icon="📝",
    layout="wide"
)

# Custom CSS for improved tabs and buttons
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
        border: none;
        transition: background 0.2s;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        color: #fff;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3.5rem;
        white-space: pre-wrap;
        background-color: #18181b;
        color: #fff;
        border-radius: 8px 8px 0 0;
        gap: 1rem;
        padding-top: 10px;
        padding-bottom: 10px;
        font-size: 1.1rem;
        font-weight: 500;
        border: 2px solid #18181b;
        border-bottom: none;
        margin-bottom: -2px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fff;
        color: #2563eb;
        border: 2px solid #2563eb;
        border-bottom: 2px solid #fff;
    }
    .stats-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        padding: 1rem;
        background-color: #f8fafc;
        border-radius: 8px;
    }
    .stat-box {
        text-align: center;
        padding: 1rem;
        background-color: white;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        flex: 1;
        margin: 0 0.5rem;
        color: #222 !important;
    }
    .stat-box h2, .stat-box h3 {
        color: #222 !important;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

def create_application_form():
    st.markdown("### Add New Application")
    
    with st.form("new_application"):
        job_title = st.text_input("Job Title")
        company_name = st.text_input("Company Name")
        job_description = st.text_area("Job Description")
        my_location = st.text_input("My Location (Optional)")
        
        col1, col2 = st.columns(2)
        with col1:
            resume = st.file_uploader("Resume (PDF/DOC)", type=["pdf", "doc", "docx"])
        with col2:
            cover_letter = st.file_uploader("Cover Letter (Optional)", type=["pdf", "doc", "docx"])
        
        st.markdown("### Associated People")
        col1, col2 = st.columns(2)
        with col1:
            referrer_name = st.text_input("Referrer Name")
            referrer_email = st.text_input("Referrer Email")
        with col2:
            recruiter_name = st.text_input("Recruiter Name")
            recruiter_email = st.text_input("Recruiter Email")
        
        status = st.selectbox("Status", STATUS_OPTIONS)
        is_tailored = st.checkbox("Is Tailored", value=False)
        
        submitted = st.form_submit_button("Submit Application")
        
        if submitted:
            logger.debug(f"Form submitted with Title: {job_title}, Company: {company_name}")
            logger.debug(f"Resume file: {resume.name if resume else 'None'}")
            
            if not job_title or not company_name or not job_description or not resume:
                st.error("Job Title, Company Name, Job Description, and Resume are required!")
                return
            
            try:
                # Prepare files and form data
                files = {
                    'resume': (resume.name, resume.getvalue()),
                }
                if cover_letter:
                    files['cover_letter'] = (cover_letter.name, cover_letter.getvalue())
                
                data = {
                    'job_title': job_title,
                    'company_name': company_name,
                    'job_description': job_description,
                    'my_location': my_location or None,
                    'referrer_name': referrer_name or None,
                    'referrer_email': referrer_email or None,
                    'recruiter_name': recruiter_name or None,
                    'recruiter_email': recruiter_email or None,
                    'status': status,
                    'is_tailored': is_tailored
                }
                
                logger.debug(f"Sending request to {API_URL}/applications/")
                logger.debug(f"Data: {data}")
                logger.debug(f"Files: {list(files.keys())}")
                
                # Send request to FastAPI backend
                response = requests.post(
                    f"{API_URL}/applications/",
                    files=files,
                    data=data
                )
                
                logger.debug(f"Response status code: {response.status_code}")
                logger.debug(f"Response content: {response.text}")
                
                if response.status_code == 200:
                    st.success("Application added successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            
            except Exception as e:
                logger.error(f"Error submitting application: {str(e)}", exc_info=True)
                st.error(f"Error submitting application: {str(e)}")

def view_applications():
    st.markdown("### Applications")
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Search (Company/Title/Person)")
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All"] + STATUS_OPTIONS)
    
    try:
        # Fetch applications
        params = {}
        if search:
            params['search'] = search
        if status_filter != "All":
            params['status'] = status_filter
            
        response = requests.get(f"{API_URL}/applications/", params=params)
        
        if response.status_code == 200:
            data = response.json()
            applications = data['applications']
            total = data['total']
            
            if not applications:
                st.info("No applications found.")
                return
            
            # Display total count
            st.markdown(f"**Total Applications: {total}**")
            
            # Display applications
            for app in applications:
                with st.expander(f"{app['job_title']} at {app['company_name']} ({app['status']})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Company:** {app['company_name']}")
                        st.markdown(f"**Position:** {app['job_title']}")
                        st.markdown(f"**Applied:** {app['applied_date']}")
                        st.markdown(f"**Status:** {app['status']}")
                        st.markdown(f"**Is Tailored:** {'Yes' if app['is_tailored'] else 'No'}")
                        if app['my_location']:
                            st.markdown(f"**My Location:** {app['my_location']}")
                        st.markdown(f"**Job Description:**\n{app['job_description']}")
                        
                        if app['referrer_name'] or app['recruiter_name']:
                            st.markdown("**Contacts:**")
                            if app['referrer_name']:
                                st.markdown(f"- Referrer: {app['referrer_name']} ({app['referrer_email']})")
                            if app['recruiter_name']:
                                st.markdown(f"- Recruiter: {app['recruiter_name']} ({app['recruiter_email']})")
                    
                    with col2:
                        st.markdown("**Documents:**")
                        if app['resume_path']:
                            st.markdown(f"- [Resume]({API_URL}/{app['resume_path']})")
                        if app['cover_letter_path']:
                            st.markdown(f"- [Cover Letter]({API_URL}/{app['cover_letter_path']})")
                    
                    # Update status, is_tailored, and my_location
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        new_status = st.selectbox(
                            "Update Status",
                            STATUS_OPTIONS,
                            index=STATUS_OPTIONS.index(app['status']),
                            key=f"status_{app['id']}"
                        )
                    with col2:
                        new_is_tailored = st.checkbox(
                            "Is Tailored",
                            value=app['is_tailored'],
                            key=f"tailored_{app['id']}"
                        )
                    with col3:
                        new_my_location = st.text_input(
                            "My Location",
                            value=app['my_location'] or "",
                            key=f"location_{app['id']}"
                        )
                    
                    if new_status != app['status'] or new_is_tailored != app['is_tailored'] or new_my_location != (app['my_location'] or ""):
                        if st.button("Update", key=f"update_{app['id']}"):
                            try:
                                logger.debug(f"Updating application {app['id']}")
                                
                                # Prepare the update data
                                update_data = {
                                    "status": new_status,
                                    "referrer_name": app['referrer_name'],
                                    "referrer_email": app['referrer_email'],
                                    "recruiter_name": app['recruiter_name'],
                                    "recruiter_email": app['recruiter_email'],
                                    "is_tailored": new_is_tailored,
                                    "my_location": new_my_location if new_my_location else None
                                }
                                
                                logger.debug(f"Sending update data: {update_data}")
                                
                                # Send the update request
                                response = requests.put(
                                    f"{API_URL}/applications/{app['id']}",
                                    headers={"Content-Type": "application/json"},
                                    json=update_data
                                )
                                
                                logger.debug(f"Status update response: {response.status_code}")
                                logger.debug(f"Status update content: {response.text}")
                                
                                if response.status_code == 200:
                                    st.success("Status updated successfully!")
                                    # Force a complete refresh of the page
                                    st.rerun()
                                else:
                                    st.error(f"Failed to update status: {response.json().get('detail', 'Unknown error')}")
                            except Exception as e:
                                logger.error(f"Error updating status: {str(e)}", exc_info=True)
                                st.error(f"Error updating status: {str(e)}")
                    
                    # Delete button
                    if st.button("Delete Application", key=f"delete_{app['id']}"):
                        try:
                            response = requests.delete(f"{API_URL}/applications/{app['id']}")
                            if response.status_code == 200:
                                st.success("Application deleted!")
                                # Force a complete refresh of the page to update stats and count
                                st.experimental_rerun()
                            else:
                                st.error("Failed to delete application")
                        except Exception as e:
                            st.error(f"Error deleting application: {str(e)}")
        
        else:
            st.error("Failed to fetch applications")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

def get_application_count():
    try:
        response = requests.get(f"{API_URL}/applications/", params={"limit": 1})
        if response.status_code == 200:
            return response.json().get("total", 0)
    except Exception:
        pass
    return 0

def get_application_stats():
    try:
        response = requests.get(f"{API_URL}/applications/stats")
        if response.status_code == 200:
            applications = response.json()
            
            # Convert to DataFrame for easier date filtering
            df = pd.DataFrame(applications)
            df['applied_date'] = pd.to_datetime(df['applied_date'])
            
            # Get current date and calculate date ranges
            now = datetime.now()
            today = now.date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # Calculate counts
            total = len(df)
            daily = len(df[df['applied_date'].dt.date == today])
            weekly = len(df[df['applied_date'].dt.date >= week_ago])
            monthly = len(df[df['applied_date'].dt.date >= month_ago])
            
            return {
                'total': total,
                'daily': daily,
                'weekly': weekly,
                'monthly': monthly
            }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
    return {'total': 0, 'daily': 0, 'weekly': 0, 'monthly': 0}

def display_stats(stats):
    st.markdown("""
        <div class="stats-container">
            <div class="stat-box">
                <h3>Total Applications</h3>
                <h2>{total}</h2>
            </div>
            <div class="stat-box">
                <h3>Today</h3>
                <h2>{daily}</h2>
            </div>
            <div class="stat-box">
                <h3>This Week</h3>
                <h2>{weekly}</h2>
            </div>
            <div class="stat-box">
                <h3>This Month</h3>
                <h2>{monthly}</h2>
            </div>
        </div>
    """.format(**stats), unsafe_allow_html=True)

def main():
    st.title("📝 Job Application Tracker")
    
    # Get and display stats
    stats = get_application_stats()
    display_stats(stats)
    
    tab1, tab2 = st.tabs(["Add Application", "View Applications"])
    
    with tab1:
        create_application_form()
    
    with tab2:
        view_applications()

if __name__ == "__main__":
    main() 