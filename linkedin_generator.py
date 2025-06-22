import json
import os
from groq import Groq
from dotenv import load_dotenv
from utils.linkedin_logger import save_linkedin_message
# Load environment variables (GROQ_API_KEY must be set in .env)
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_linkedin_prompt_template() -> str:
    return """
You are an outreach assistant writing LinkedIn messages to industry professionals.
Your goal is to start a conversation or get a short meeting. Follow these strict rules:

Linkedin Message Requirements:
    1. Start by referencing a specific achievement or news item from the source.
    2. Include an insightful question about their strategy or a challenge they might face.
    3. Conclude with a prompt to discuss strategy or potential next steps.
    4. Tone must be professional and investor-like (not salesy or impressed)

    Content Rules:
    - Focus on what makes the company uniquely interesting for acquisition
    - Ask specific questions about business strategy
    - Discuss future potential rather than past accomplishments
    - NO greeting like 'Dear' or 'Hi Dr. ___'
    - NO long intro
    - NO sign-off or full name
    - DO NOT add any conversational filler or preambles like "Here is the LinkedIn message:". Output only the message itself.
    - Reference a specific project, news, or achievement from their background.
    - Never use: impressed, fascinated, admire, excited, appreciate 
    - Never mention: company culture, testimonials, diversity status
    - Keep sentences concise (readable in one breath)
    - LinkedIn has a short word limit — keep it under 60 words.
    - Keep tone friendly and professional — not salesy or too formal.
    - Do NOT use subject lines, "Dear", long intros, or email closings.
    - Never add your contact details, title, or long signature, and no need to add Best Regards at last.
    - NEVER use: "excited", "appreciate", "admire", "partnership", "collaboration", or "diversity"

Output Format:
[Your LinkedIn message only — no greetings or sign-offs]

Generate a LinkedIn message following the above rules.
"""

def extract_company_info_for_linkedin(data: dict) -> str:
    website_summary = data.get("website_summary", "")
    description = data.get("description", "")
    overview = data.get("company_overview", "")
    news_summary = data.get("news_summary", "")
    content = website_summary or overview or description
    if news_summary:
        content += f"\n\nRecent News Highlight: {news_summary}..."
    return content.strip()

def generate_linkedin_message(data: dict, tone: str = None, focus: str = None, additional_context: str = None) -> str:
    company_name = data.get("company_name", "the company")
    company_info = extract_company_info_for_linkedin(data)
    prompt_template = get_linkedin_prompt_template()

    customization_prompt = f"""
COMPANY TO TARGET: {company_name}

COMPANY INFORMATION:
{company_info}
"""
    if tone:
        customization_prompt += f"\nTONE: Must be {tone}"
    if focus:
        customization_prompt += f"\nFOCUS: The message focus should be on {focus}"
    if additional_context:
        customization_prompt += f"\nADDITIONAL CONTEXT: Incorporate this key point: {additional_context}"

    final_prompt = prompt_template + "\n" + customization_prompt

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.7,
            top_p=0.9
        )
        message = response.choices[0].message.content.strip()
        return message
    except Exception as e:
        return f"Error generating LinkedIn message: {e}"

if __name__ == "__main__":
    # Load test data
    json_path = os.path.join("data", "company_data.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError("Missing company_data.json")

    with open(json_path, "r", encoding="utf-8") as f:
        company_data = json.load(f)

    message = generate_linkedin_message(company_data)
    print("\n--- Generated LinkedIn Message ---\n")
    print(message)

    # Save to log files
    company_name = company_data.get("company_name", "Unknown Company")
    save_linkedin_message(company_name, message)
    print("\n✅ Logged to linkedin_log.csv and linkedin_log.json\n")