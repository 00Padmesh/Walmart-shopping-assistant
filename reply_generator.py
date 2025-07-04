import json
from mistralai import Mistral
from config import MISTRAL_API_KEY, MISTRAL_MODEL

client = Mistral(api_key=MISTRAL_API_KEY)

SYSTEM_PROMPT = """
You are a friendly, concise shopping assistant.

Given a user's query and a list of real products, generate a short, helpful, natural-language reply that:

- Explains what was found or compared
- Highlights brands, categories, or price/rating filters if mentioned
- Suggests top picks if possible
- Encourages follow-ups like “Want to refine this further?”

NEVER list product details — that will be displayed separately.
NEVER hallucinate or mention products you don’t see.
Keep your reply short and focused.
"""

def generate_reply(user_query, products, action):
    try:
        examples = [
            {
                "title": p.get("title"),
                "price": p.get("price"),
                "rating": p.get("rating"),
            } for p in products[:3]  # Use top 3 for context
        ]

        prompt = {
            "query": user_query,
            "action": action,
            "products": examples
        }

        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(prompt)}
            ]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("❌ Reply generation failed:", e)
        return "Here are the results. Let me know if you'd like to refine them!"
