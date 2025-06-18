# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from collections import defaultdict

# Import your existing modules
from linkedin_fallback_scraper import scrape_all_company_data
from linkedin_profile_scraper import fetch_linkedin_bio
from commonality_detector import compute_overlap, summarize_commonalities
from insight_extractor import extract_variant_insights
from email_generator import generate_email_variants, VARIANT_MODES

app = FastAPI(title="Caprae Cold Email API")


class EmailRequest(BaseModel):
    company_name: str
    website_url: Optional[str] = None
    user_linkedin_url: Optional[str] = None
    founder_linkedin_url: Optional[str] = None
    extra_context: Optional[str] = None
    tone: str    # e.g. "direct", "warm", etc.
    focus: str   # e.g. "Product Insight", "Curious Analyst", etc.


class EmailResponse(BaseModel):
    email: str
    title: str
    tone: str
    focus: str


@app.get("/config", summary="Get available tones and focuses")
def get_config() -> Dict[str, List[Dict[str, str]]]:
    """
    Returns the list of supported tone/focus configurations.
    """
    return {"modes": VARIANT_MODES}


@app.post(
    "/generate_email",
    response_model=EmailResponse,
    summary="Generate a cold email variant"
)
def generate_email(req: EmailRequest):
    # 1) Build the LinkedIn articles URL from company name
    slug = req.company_name.strip().lower().replace(" ", "-")
    linkedin_articles_url = f"https://www.linkedin.com/company/{slug}/posts"

    # 2) Scrape data
    sources = scrape_all_company_data(linkedin_articles_url, req.website_url or "")
    if not sources:
        raise HTTPException(
            status_code=400,
            detail="No sources found from LinkedIn or website."
        )

    # 3) Group and extract variant contexts
    grouped = defaultdict(list)
    for s in sources:
        grouped[s["source_type"]].append(s["text"])
    contexts = extract_variant_insights(grouped)

    # 4) Optional: detect commonalities between user and founder profiles
    commonality_hint = ""
    if req.user_linkedin_url and req.founder_linkedin_url:
        user_bio = fetch_linkedin_bio(req.user_linkedin_url)
        founder_bio = fetch_linkedin_bio(req.founder_linkedin_url)
        if user_bio and founder_bio:
            overlap, _ = compute_overlap(user_bio, founder_bio)
            commonality_hint = summarize_commonalities(overlap)

    # 5) Validate that the requested tone & focus exist
    mode = next(
        (m for m in VARIANT_MODES
         if m["tone"] == req.tone and m["focus"] == req.focus),
        None
    )
    if not mode:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported tone '{req.tone}' or focus '{req.focus}'"
        )

    # 6) Generate all variants, then pick the one matching tone+focus
    variants = generate_email_variants(
        company_name=req.company_name,
        context_per_variant=contexts,
        commonality_hint=commonality_hint,
        extra_context=req.extra_context or ""
    )
    variant = next(
        (v for v in variants
         if v.get("tone") == req.tone and v.get("focus") == req.focus),
        None
    )
    if not variant or "error" in variant:
        raise HTTPException(
            status_code=500,
            detail=variant.get("error", "Failed to generate email.")
        )

    return EmailResponse(
        email=variant["email"],
        title=variant["title"],
        tone=variant["tone"],
        focus=variant["focus"]
    )


@app.get("/health", summary="Health check")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
