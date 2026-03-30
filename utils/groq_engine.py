import json
import logging
import time
from typing import Dict, Any, List

import groq
from groq import Groq

import config
from utils.retry_handler import retry_call

logger = logging.getLogger(__name__)

# Initialize client globally but lazily
_client = None

def get_client() -> Groq:
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in config/env")
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client

def analyze_job(resume_json: Dict[str, Any], job_post: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single job posting against the provided parsed resume JSON.
    Returns a dictionary matching the schema:
    {
       "score": int,
       "missing_skills": list,
       "suggestions": list,
       "cover_letter": str
    }
    """
    client = get_client()
    
    system_prompt = (
        "You are an expert technical recruiter and career coach. "
        "Analyze the provided job description against the user's resume. "
        "Return the output STRICTLY as a valid JSON object with the following keys:\n"
        "- \"score\": Integer from 0-100 representing the match percentage.\n"
        "- \"missing_skills\": List of strings showing key skills required by the job but missing from the resume.\n"
        "- \"suggestions\": List of strings offering actionable advice on how to improve the resume for this role.\n"
        "- \"cover_letter\": A short, professional, highly tailored cover letter (2-3 paragraphs) for this job."
    )
    
    user_content = json.dumps({
        "resume": resume_json,
        "job": {
            "title": job_post.get("title"),
            "company": job_post.get("company"),
            "description": job_post.get("description")
        }
    })

    def _call_groq():
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=config.GROQ_TEMPERATURE,
            max_tokens=config.GROQ_MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not content:
             raise ValueError("Empty response from Groq")
        return json.loads(content)

    try:
        result = retry_call(
            _call_groq,
            attempts=config.GROQ_RETRY_ATTEMPTS,
            backoff=config.GROQ_RETRY_BACKOFF,
            exceptions=(groq.APIError, groq.APIConnectionError, groq.RateLimitError, ValueError, json.JSONDecodeError)
        )
        if result is None:
            raise ValueError("Groq analysis failed after retries.")
        return result
    except Exception as e:
        logger.error("Failed to analyze job %s: %s", job_post.get("title"), e)
        # Graceful fallback
        return {
            "score": 0,
            "missing_skills": [],
            "suggestions": ["Failed to generate analysis due to API error."],
            "cover_letter": ""
        }

def batch_analyze(resume_json: Dict[str, Any], job_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of jobs, rate limiting the requests gracefully.
    Modifies the dictionaries in `job_list` by adding the AI analysis results.
    """
    logger.info("Starting AI batch analysis on %d jobs...", len(job_list))
    
    for i, job in enumerate(job_list):
        logger.debug("Analyzing job %d/%d: %s", i+1, len(job_list), job.get("title"))
        analysis = analyze_job(resume_json, job)
        
        job["score"] = analysis.get("score", 0)
        job["missing_skills"] = analysis.get("missing_skills", [])
        job["suggestions"] = analysis.get("suggestions", [])
        job["cover_letter"] = analysis.get("cover_letter", "")
        
        # Rate limit compliance: wait between calls
        time.sleep(1.0)
        
    return job_list
