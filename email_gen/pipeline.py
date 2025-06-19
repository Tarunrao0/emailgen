import json
import os
from dotenv import load_dotenv
from groq import Groq
from email_gen.vector_embedding.prompt_template import get_template
from email_gen.vector_embedding.retrieve_email import extract_company_text, retrieve_similar_email

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("❌ Missing GROQ_API_KEY in .env")

client = Groq(api_key=api_key)

def generate_email(company_data_path: str, embeddings_path: str):
    # Load company data
    with open(company_data_path, "r", encoding="utf-8") as f:
        company_data = json.load(f)

    company_name = company_data.get("company_name", "Unknown").strip()
    source_text = extract_company_text(company_data)
    template = get_template()
    similar_email = retrieve_similar_email(source_text, embeddings_path)

    # Strongly formatted user prompt
    user_prompt = f"""
You are given three blocks of text below. Use them to adapt the email as instructed.

===
[COMPANY NAME]
{company_name}
===
[COMPANY INFO]
{source_text}
===
[TEMPLATE EMAIL]
{similar_email}
===
[TASK]
Adapt the TEMPLATE EMAIL to target the company described in COMPANY NAME and COMPANY INFO.

Rules:
- DO NOT write a new email.
- KEEP the EXACT SAME structure, paragraph breaks, tone, and flow.
- Only swap out company-specific parts using COMPANY INFO and use the company name "{company_name}" in all places.
- NEVER guess company names based on the description.
- NEVER include "Here is the adapted email:"
- NEVER include placeholders like [Your Company].
- Maintain same paragraph count.
- DO NOT add or remove sentences.
- DO NOT add praise or extra opinions.
- Only one final call to action like:
  - "Would you be up for a conversation next week?"
  - "I'd love to hear more about [company/topic]. Would you be free for a quick chat?"
- Output ONLY the subject line and email body.
- Generate a unique and engaging subject line that does NOT start with “Exploring” or similar generic verbs
- Use company-specific context to make the subject relevant

Output format:
Subject: [your subject line]

[email body only, no header or explanation]
"""

    system_prompt = """You are an expert email writer. Adapt the provided TEMPLATE EMAIL using the COMPANY INFO and COMPANY NAME.

Rules:
- Match the template exactly in structure and tone.
- Only change company-specific details.
- Do not invent or generalize anything.
- No placeholders like [Your Company]
- Never include introductory phrases like "Here is the adapted email:"
- End with only ONE call-to-action from the approved list.
- Subject lines must NOT begin with vague verbs like “Exploring”, “Discovering”, “Learning about”, “Understanding”, etc.
- Subject lines should be relevant, natural, and specific to the company’s work or industry.
- Vary the subject style to avoid repetition. Good examples:
   - “How rcg advertising and media elevates brand impact”
   - “Let’s talk brand strategy and media agility”
   - “Helping brands thrive across traditional and digital platforms”


Output only the subject and the email body. No extra content.
"""

    # Generate email
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ],
        temperature=0.2,
        top_p=0.85
    )

    result = response.choices[0].message.content.strip()

    # Remove any leading "Here is the adapted email:" just in case
    if result.lower().startswith("here is the adapted email"):
        result = result.split("\n", 1)[-1].strip()

    # Remove any leftover placeholders
    result = result.replace("[Your Company]", "").replace("  ", " ").strip()

    # Save final output
    with open("data/final_email.txt", "w", encoding="utf-8") as f:
        f.write(result)

    print("✅ Generated email saved to final_email.txt")

    # Extract subject line
    lines = result.splitlines()
    subject_line = lines[0]
    if subject_line.lower().startswith("subject:"):
        subject_line = subject_line.split(":", 1)[1].strip()
        email_body = "\n".join(lines[1:]).strip()
    else:
        email_body = "\n".join(lines).strip()

    return {
        "company": company_name,
        "subject": subject_line,
        "email": email_body
    }

if __name__ == "__main__":
    generate_email("data/company_data.json", "data/email_embeddings.json")
