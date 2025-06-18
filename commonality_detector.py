# commonality_detector.py
import re

def tokenize(text: str) -> set:
    return set(re.findall(r"\b\w{4,}\b", text.lower()))

def compute_overlap(text1: str, text2: str):
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    overlap = tokens1.intersection(tokens2)
    summary = f"**{len(overlap)} shared keywords found**: {', '.join(sorted(overlap))[:500]}..."
    return overlap, summary

def summarize_commonalities(overlap_set: set) -> str:
    if not overlap_set:
        return ""
    keywords = sorted(list(overlap_set))[:10]
    return "Common themes: " + ", ".join(keywords)
