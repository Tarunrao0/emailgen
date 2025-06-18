#insight_extractor.py
from collections import defaultdict
from typing import Dict, List

def extract_variant_insights(grouped_sources: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Takes grouped sources and returns variant-specific context blocks.
    """
    def from_sources(keys: List[str]) -> str:
        texts = []
        for key in keys:
            if key in grouped_sources:
                texts.extend(grouped_sources[key])
        return "\n\n".join(texts)

    return {
        "Product Insight": from_sources(["website_homepage", "website_blog", "website_news"]),
        "Team & Talent Fit": from_sources(["linkedin_about", "website_about", "website_team"]),
        "Market Perspective": from_sources(["linkedin_articles", "website_blog", "website_insights"]),
        "Founder Commonality": "",  # Injected separately in commonality_hint
        "Strategic Fit": from_sources(["website_about", "website_homepage"]),
        "Curious Analyst": from_sources(["website_blog", "linkedin_articles"]),
        "Relational & Friendly": from_sources(["linkedin_articles", "linkedin_about"]),
    }
