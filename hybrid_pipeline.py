import json
from groq import Groq  # Requires `pip install groq`
from prompt_template import get_template
from retrieve_email import extract_company_text, retrieve_similar_email

# 🔑 Set your key or load from env
client = Groq(api_key="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")  # Replace with your Groq key (or use os.getenv)

def generate_email(company_data_path: str, embeddings_path: str):
    with open(company_data_path, "r", encoding="utf-8") as f:
        company_data = json.load(f)

    template = get_template()
    source_text = extract_company_text(company_data)
    similar_email = retrieve_similar_email(source_text, embeddings_path)

    # Create a template-focused prompt
    company_name = company_data.get("company_name", "Unknown")
    
    # Modified system prompt to emphasize template adherence
    system_prompt = """You are an expert email writer. Your task is to adapt the PROVIDED TEMPLATE EMAIL to fit a new company while maintaining the EXACT SAME structure, tone, and format.

CRITICAL INSTRUCTIONS:
1. Use the retrieved email as your PRIMARY TEMPLATE - keep the same structure, paragraph breaks, and flow
2. Only replace company-specific details with information about the target company
3. Maintain the same conversational tone and personal touch
4. Keep the same email length and format
5. Do NOT add new sections or significantly change the structure
6. Make minimal enhancements - only improve clarity or fix obvious errors
7. Generate an appropriate email subject line
8. CRITICAL: End with a compelling, personal call-to-action that follows these patterns:
   - "I'd love to [connect/hear more/discuss] [specific topic] when you have a moment"
   - "Would you be up for a conversation next week?"
   - "I'd love to connect more and discuss [topic]. Would you be free next week?"
   - "I'd love to hear more about [company/topic] if you are available for a quick chat"
   - Make it personal, enthusiastic, and suggest a specific timeframe
9. Do NOT include "Best regards" or formal signatures
10. Output ONLY the subject line and email content - no explanations or notes"""

    # Template-focused user prompt
    user_prompt = f"""COMPANY TO TARGET: {company_name}

COMPANY INFORMATION:
{source_text}

TEMPLATE EMAIL TO ADAPT:
{similar_email}

TASK: Adapt the template email above to target {company_name}. 
- Keep the EXACT same structure and format
- Replace company-specific details with relevant information about {company_name}
- Maintain the same tone and personal style
- Keep the same paragraph structure and flow
- Generate an engaging subject line for the email
- END with a personal, enthusiastic call-to-action using patterns like:
  * "I'd love to connect and swap stories about [topic] when you have a moment"
  * "I'd love to hear more about [specific company aspect]. Would you be up for a conversation next week?"
  * "Would you be free for a quick chat next week to discuss [topic]?"
- Focus on different aspects of the company information each time for variety
- Only make minimal improvements for clarity

Output format:
Subject: [your subject line]

[email content only - no explanations]"""

    # LLM call to Groq API with template-focused approach
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4,  # Slightly higher for variety on regeneration
        top_p=0.9  # Add some randomness for different outputs
    )

    result = response.choices[0].message.content.strip()
    
    # Save the result without template comparison
    with open("final_email.txt", "w", encoding="utf-8") as f:
        f.write(result)

    print("✅ Generated email saved to final_email.txt")

if __name__ == "__main__":
    generate_email("company_data.json", "email_embeddings.json")