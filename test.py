# test_retrieve.py
from sentence_transformers import SentenceTransformer, util
import numpy as np
import json

# Your code
model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_company_text(data: dict) -> str:
    description = data.get("description", "")
    overview = data.get("company_overview", "")
    news = data.get("news_summary", "")
    industries = ", ".join(data.get("industry_categories", []))
    website = data.get("website_summary", "")
    
    return (
        f"{description}\n\n"
        f"{overview}\n\n"
        f"Industries: {industries}\n\n"
        f"Website Summary: {website}\n\n"
        f"Recent News: {news}"
    )

def retrieve_similar_email(company_text: str, embeddings_file: str) -> str:
    query_emb = model.encode(company_text)
    with open(embeddings_file, "r", encoding="utf-8") as f:
        embedded = json.load(f)

    best_score, best_email = -1, None
    for e in embedded:
        emb = np.array(e["embedding"], dtype=np.float32)
        score = util.cos_sim(query_emb, emb).item()
        if score > best_score:
            best_score, best_email = score, e["email"]

    return best_email

# === RUN TEST ===

# Load company data
with open("data/company_data.json", "r", encoding="utf-8") as f:
    company_data = json.load(f)

# Extract company text
extracted_text = extract_company_text(company_data)
print("=== Extracted Company Text ===")
print(extracted_text)
print()

# Retrieve similar email
retrieved_email = retrieve_similar_email(extracted_text, "data/email_embeddings.json")
print("=== Retrieved Email ===")
print(retrieved_email)
