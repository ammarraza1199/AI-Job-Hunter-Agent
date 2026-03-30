import argparse
import logging
import time
import sys

import config
from services import resume_parser, job_matcher
from scraper.indeed import IndeedScraper
from scraper.naukri import NaukriScraper
from scraper.linkedin import LinkedInScraper

# Setup Root Logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")

def main():
    parser = argparse.ArgumentParser(description="AI Job Hunter Agent")
    parser.add_argument("--resume", type=str, required=True, help="Path to your resume (PDF/DOCX)")
    parser.add_argument("--query", type=str, required=True, help="Job role / keywords (e.g. 'Python Developer')")
    parser.add_argument("--location", type=str, required=True, help="Target location (e.g. 'Hyderabad')")
    parser.add_argument("--platforms", type=str, help="Comma-separated platforms (e.g. indeed,naukri,linkedin). Default: all")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("🚀 STARTING AI JOB HUNTER PIPELINE")
    logger.info("=" * 60)
    
    # 0. Validate Setup
    errors = config.validate_config()
    if errors:
        logger.error("Configuration Errors found:")
        for e in errors:
            logger.error(" - %s", e)
        sys.exit(1)

    # 1. Parse Resume
    try:
        logger.info("📄 Parsing resume: %s", args.resume)
        resume_data = resume_parser.parse_resume(args.resume)
        logger.info("✅ Resume parsed for %s (%.1f years exp). skills count: %d", 
                    resume_data.get("name"), 
                    resume_data.get("total_years_experience", 0), 
                    len(resume_data.get("skills", [])))
    except Exception as e:
        logger.error("Failed to parse resume: %s", e)
        sys.exit(1)

    # 2. Scrape platforms
    platforms_to_run = ["indeed", "naukri", "linkedin"]
    if args.platforms:
        platforms_to_run = [p.strip().lower() for p in args.platforms.split(",")]
        
    all_raw_jobs = []
    
    # Run sequentially (Playwright can be run concurrently, but seq is safer for IP/resources)
    if "indeed" in platforms_to_run:
        all_raw_jobs.extend(IndeedScraper().scrape(args.query, args.location))
        
    if "naukri" in platforms_to_run:
        all_raw_jobs.extend(NaukriScraper().scrape(args.query, args.location))
        
    if "linkedin" in platforms_to_run:
        all_raw_jobs.extend(LinkedInScraper().scrape(args.query, args.location))

    logger.info("Total raw jobs scraped across platforms: %d", len(all_raw_jobs))

    if not all_raw_jobs:
        logger.warning("No jobs found. Exiting.")
        sys.exit(0)

    # 3. Match, filter, deduplicate, AI process, and store
    logger.info("🧠 Processing and AI evaluating...")
    final_jobs = job_matcher.process_and_store(resume_data, all_raw_jobs)
    
    logger.info("=" * 60)
    logger.info("✅ PIPELINE COMPLETE. %d jobs pushed to Google Sheets.", len(final_jobs))
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
