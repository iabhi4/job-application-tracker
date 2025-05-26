import aiohttp
from bs4 import BeautifulSoup
import re
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scrape_job_info(url: str) -> Dict[str, str]:
    """
    Scrape job information from a given URL.
    Returns a dictionary containing company name, job title, and job description.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch URL: {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try to find job title
                job_title = None
                title_candidates = [
                    soup.find('h1'),  # Common for job titles
                    soup.find('title'),  # Fallback to page title
                    soup.find(class_=re.compile(r'title|job-title|position', re.I)),
                ]
                
                for candidate in title_candidates:
                    if candidate and candidate.text.strip():
                        job_title = candidate.text.strip()
                        break
                
                if not job_title:
                    job_title = "Unknown Position"
                
                # Try to find company name
                company_name = None
                company_candidates = [
                    soup.find(class_=re.compile(r'company|employer|organization', re.I)),
                    soup.find(itemprop="hiringOrganization"),
                    soup.find(itemprop="name"),
                ]
                
                for candidate in company_candidates:
                    if candidate and candidate.text.strip():
                        company_name = candidate.text.strip()
                        break
                
                if not company_name:
                    company_name = "Unknown Company"
                
                # Try to find job description
                job_description = None
                description_candidates = [
                    soup.find(class_=re.compile(r'description|job-description|details', re.I)),
                    soup.find(itemprop="description"),
                    soup.find(id=re.compile(r'description|job-description|details', re.I)),
                ]
                
                for candidate in description_candidates:
                    if candidate and candidate.text.strip():
                        job_description = candidate.text.strip()
                        break
                
                if not job_description:
                    # Fallback: try to get the main content
                    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                    if main_content:
                        job_description = main_content.text.strip()
                    else:
                        job_description = "No description available"
                
                return {
                    "company_name": company_name,
                    "job_title": job_title,
                    "job_description": job_description
                }
                
    except Exception as e:
        logger.error(f"Error scraping job info: {str(e)}")
        raise Exception(f"Failed to scrape job information: {str(e)}") 