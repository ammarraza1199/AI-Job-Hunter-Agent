"""
config.py — Central Configuration for AI Job Hunter Agent
All secrets via .env, all tunable constants here. Never hardcode secrets.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ─── Load .env ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ─── API Keys & Credentials ───────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GOOGLE_SHEETS_CREDENTIALS_FILE: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
GOOGLE_SHEETS_SPREADSHEET_ID: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
GOOGLE_SHEETS_WORKSHEET_NAME: str = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "Jobs")

# ─── Groq Model ───────────────────────────────────────────────────────────────
GROQ_MODEL: str = "llama3-70b-8192"
GROQ_MAX_TOKENS: int = 4096
GROQ_TEMPERATURE: float = 0.3
GROQ_RETRY_ATTEMPTS: int = 3
GROQ_RETRY_BACKOFF: list = [5, 10, 20]   # seconds between Groq retries

# ─── Scraping Limits ──────────────────────────────────────────────────────────
MAX_JOBS_PER_PLATFORM: int = 50
MAX_JOBS_LINKEDIN: int = 25           # LinkedIn ban risk is higher
MAX_SCROLL_ATTEMPTS: int = 10
MAX_PAGES_INDEED: int = 5

# ─── Timing & Delays ──────────────────────────────────────────────────────────
DELAY_MIN: float = 2.0                # seconds — minimum delay between actions
DELAY_MAX: float = 6.0                # seconds — maximum delay between actions
SCROLL_DELAY_MIN: float = 1.0
SCROLL_DELAY_MAX: float = 2.5
SCROLL_INCREMENT_MIN: int = 300       # pixels
SCROLL_INCREMENT_MAX: int = 500       # pixels
LINKEDIN_COOLDOWN_SECONDS: int = 3600  # 1 hour between LinkedIn runs

# ─── Time Filtering ───────────────────────────────────────────────────────────
FILTER_MAX_HOURS: int = 24            # Drop jobs older than this
FILTER_PREFER_HOURS: int = 12         # Flag jobs newer than this as preferred

# ─── Retry ────────────────────────────────────────────────────────────────────
RETRY_ATTEMPTS: int = 3
RETRY_BACKOFF: list = [2, 4, 8]       # exponential backoff in seconds

# ─── URL Filters ──────────────────────────────────────────────────────────────
URL_FILTERS = {
    "indeed": "fromage=1",
    "naukri": "jobAge=1",
    "linkedin": "f_TPR=r86400",
}

# ─── Session / Cookie Storage ─────────────────────────────────────────────────
SESSION_DIR: Path = BASE_DIR / "sessions"
SESSION_DIR.mkdir(exist_ok=True)
LINKEDIN_SESSION_FILE: Path = SESSION_DIR / "linkedin_session.json"
SESSION_MAX_AGE_HOURS: int = 12       # Re-login after this many hours

# ─── Cache ────────────────────────────────────────────────────────────────────
CACHE_DIR: Path = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE: Path = CACHE_DIR / "processed_jobs.json"

# ─── Logs ─────────────────────────────────────────────────────────────────────
LOG_DIR: Path = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE: Path = LOG_DIR / "job_agent.log"
LOG_LEVEL: int = logging.INFO

# ─── Browser ──────────────────────────────────────────────────────────────────
HEADLESS: bool = True                 # Set False for debugging
BROWSER_TIMEOUT: int = 30_000        # ms — page/action timeout
NAVIGATION_TIMEOUT: int = 60_000     # ms — full page navigation timeout

# ─── Platform Base URLs ───────────────────────────────────────────────────────
INDEED_BASE_URL: str = "https://www.indeed.com"
NAUKRI_BASE_URL: str = "https://www.naukri.com"
LINKEDIN_BASE_URL: str = "https://www.linkedin.com"

# ─── Google Sheets Column Schema ─────────────────────────────────────────────
SHEET_HEADERS = [
    "Platform", "Title", "Company", "Location",
    "Posted (Raw)", "Posted (Hours)", "Posted (UTC)",
    "Score", "Missing Skills", "Suggestions",
    "Cover Letter", "HR Contact", "URL",
    "Job ID", "Salary", "Scraped At",
]

# ─── Validation ───────────────────────────────────────────────────────────────
def validate_config() -> list[str]:
    """
    Validate required configuration values.
    Returns a list of missing/invalid config keys.
    """
    errors: list[str] = []
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY is not set in .env")
    if not GOOGLE_SHEETS_SPREADSHEET_ID:
        errors.append("GOOGLE_SHEETS_SPREADSHEET_ID is not set in .env")
    creds_path = BASE_DIR / GOOGLE_SHEETS_CREDENTIALS_FILE
    if not creds_path.exists():
        errors.append(f"Google credentials file not found: {creds_path}")
    return errors
