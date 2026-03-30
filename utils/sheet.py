import json
import logging
from typing import List, Dict, Any, Optional

import gspread
from google.oauth2.service_account import Credentials

import config

logger = logging.getLogger(__name__)

# Cache of existing Job IDs in the sheet to prevent duplicates
_EXISTING_IDS = set()

def init_sheet() -> Optional[gspread.Worksheet]:
    """Authenticates with Google Sheets API and returns the Worksheet."""
    creds_file = config.BASE_DIR / config.GOOGLE_SHEETS_CREDENTIALS_FILE
    if not creds_file.exists():
        logger.error("Google Sheets credentials not found at %s", creds_file)
        return None
        
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_file(
            str(creds_file), scopes=scopes
        )
        gc = gspread.authorize(credentials)
        
        # Open by ID
        spreadsheet = gc.open_by_key(config.GOOGLE_SHEETS_SPREADSHEET_ID)
        
        try:
            worksheet = spreadsheet.worksheet(config.GOOGLE_SHEETS_WORKSHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            logger.info("Worksheet '%s' not found. Creating it...", config.GOOGLE_SHEETS_WORKSHEET_NAME)
            worksheet = spreadsheet.add_worksheet(title=config.GOOGLE_SHEETS_WORKSHEET_NAME, rows=1000, cols=20)
            
        # Ensure headers exist
        existing_values = worksheet.get_all_values()
        if not existing_values:
            worksheet.append_row(config.SHEET_HEADERS)
            
        return worksheet
    except Exception as e:
        logger.error("Failed to initialize Google Sheets connection: %s", e)
        return None

def check_duplicate_in_sheet(worksheet: gspread.Worksheet, job_id: str) -> bool:
    """Check if the job_id already exists in the sheet. Uses simple memory cache after first load."""
    global _EXISTING_IDS
    
    # Lazy load the ID column (Assuming 'Job ID' is always at a specific index)
    if not _EXISTING_IDS:
        try:
            headers = worksheet.row_values(1)
            # Find the 'Job ID' column index (1-based)
            id_col_index = None
            for i, h in enumerate(headers):
                if h == "Job ID":
                    id_col_index = i + 1
                    break
                    
            if id_col_index:
                # Fetch all existing IDs (skip header)
                all_ids = worksheet.col_values(id_col_index)
                _EXISTING_IDS = set(all_ids[1:])
        except Exception as e:
            logger.warning("Could not fetch existing IDs for deduplication: %s", e)
            return False
            
    return job_id in _EXISTING_IDS

def write_jobs(job_results: List[Dict[str, Any]]) -> None:
    """
    Append new job rows to the spreadsheet. 
    Never overwrite, only append.
    """
    worksheet = init_sheet()
    if not worksheet:
        logger.error("Cannot write to sheets (init failed). Saving to local cache instead.")
        _save_local(job_results)
        return
        
    rows_to_insert = []
    
    for job in job_results:
        job_id = job.get('job_id')
        if not job_id:
            logger.warning("Skipping job without ID: %s", job.get("title"))
            continue
            
        if check_duplicate_in_sheet(worksheet, job_id):
            logger.debug("Job %s already in sheet. Skipping.", job_id)
            continue
            
        # Format lists
        missing_skills = ", ".join(job.get("missing_skills", []))
        suggestions = "\n".join(job.get("suggestions", []))
        
        row = [
            job.get("platform", ""),
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("posted_raw", ""),
            job.get("posted_hours", ""),
            job.get("posted_utc", ""),
            job.get("score", ""),
            missing_skills,
            suggestions,
            job.get("cover_letter", ""),
            job.get("hr_contact", ""),
            job.get("url", ""),
            job_id,
            job.get("salary", ""),
            job.get("scraped_at", "")
        ]
        
        # Ensure row maps to config.SHEET_HEADERS exact order
        rows_to_insert.append(row)
        _EXISTING_IDS.add(job_id)

    if rows_to_insert:
        try:
            worksheet.append_rows(rows_to_insert, value_input_option='USER_ENTERED')
            logger.info("✅ Appended %d new jobs to Google Sheets.", len(rows_to_insert))
        except Exception as e:
            logger.error("Failed to append rows to Google Sheets: %s", e)
            _save_local(job_results)
    else:
        logger.info("No new non-duplicate jobs to write.")

def _save_local(job_results: List[Dict[str, Any]]) -> None:
    """Fallback: append jobs to local JSON file if Sheets API fails."""
    try:
        existing = []
        if config.CACHE_FILE.exists():
            with open(config.CACHE_FILE, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except json.JSONDecodeError:
                    pass
                    
        existing.extend(job_results)
        with open(config.CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
            
        logger.info("Saved %d jobs to local fallback cache.", len(job_results))
    except Exception as e:
        logger.error("CRITICAL: Failed to save to local cache fallback: %s", e)
