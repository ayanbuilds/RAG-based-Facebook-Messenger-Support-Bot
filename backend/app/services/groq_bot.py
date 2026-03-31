# from groq import Groq
# from groq import BadRequestError
# from app.core.config import settings

# client = Groq(api_key=settings.GROQ_API_KEY)

# SYSTEM = """You are the official customer support assistant for our company Facebook page.

# Rules:
# - Be polite, short, and clear.
# - Answer only about the company: services, working hours, processes, policies, contact info.
# - If you are unsure or the info is missing, say you will connect the user to a human assistant.
# - Do not invent facts.
# """

# FALLBACK_REPLY = (
#     "Thanks for reaching out. I am unable to generate a response right now. "
#     "A human assistant will get back to you shortly."
# )

# def build_reply(user_text: str) -> str:
#     if not settings.GROQ_API_KEY:
#         return FALLBACK_REPLY

#     try:
#         res = client.chat.completions.create(
#             model=settings.GROQ_MODEL,
#             messages=[
#                 {"role": "system", "content": SYSTEM},
#                 {"role": "user", "content": user_text},
#             ],
#             temperature=0.2,
#             max_tokens=180,
#         )
#         return res.choices[0].message.content.strip() or FALLBACK_REPLY

#     except BadRequestError as e:
#         # Most common: model decommissioned / invalid model name
#         print(f"[Groq BadRequestError] {e}")
#         return FALLBACK_REPLY
#     except Exception as e:
#         print(f"[Groq Error] {e}")
#         return FALLBACK_REPLY


# edit 2
from groq import Groq
from groq import BadRequestError
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM = """You are the official customer support assistant for our company.

You MUST follow these rules:
- Answer using ONLY the provided CONTEXT.
- If the answer is not in the CONTEXT, say: "I do not have that information. A human assistant will help you."
- Keep replies short and clear.
- Do not invent facts or provide information outside the CONTEXT.
"""

FALLBACK_REPLY = (
    "I do not have that information. A human assistant will help you."
)

def build_reply(user_text: str, context_chunks: list[str]) -> str:
    """
    Generate a reply based on user text and retrieved context chunks.
    
    Args:
        user_text: The user's question/message
        context_chunks: List of relevant context strings retrieved from knowledge base
        
    Returns:
        AI-generated reply or fallback message
    """
    if not settings.GROQ_API_KEY:
        return FALLBACK_REPLY

    # Join context chunks with separator
    context = "\n\n---\n\n".join(context_chunks).strip()
    
    # If no context provided, return fallback
    if not context:
        return FALLBACK_REPLY

    try:
        res = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{user_text}\n\nAnswer:"}
            ],
            temperature=0.2,
            max_tokens=220,
        )
        return res.choices[0].message.content.strip() or FALLBACK_REPLY

    except BadRequestError as e:
        # Most common: model decommissioned / invalid model name
        print(f"[Groq BadRequestError] {e}")
        return FALLBACK_REPLY
    except Exception as e:
        print(f"[Groq Error] {e}")
        return FALLBACK_REPLY