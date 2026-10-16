import ollama


MODEL_NAME = "gemma3:4b"


def build_prompt(style_prompt: str) -> str:
    return f"""You are an expert e-commerce listing writer helping a small seller.

Write the listing in this voice/style: {style_prompt}

From the product photo, produce the following using Markdown:

## Title
One line, max 140 characters, keyword-rich, no ALL CAPS.

## Description
3 to 5 sentences, natural, in the requested voice.

## Tags
Exactly 13 tags, comma-separated, lowercase, no hashtags, no duplicates.

## Suggested Price
A realistic range in USD. Write the currency as "USD" (not "$").
Add a one-line justification.

Rules:
- Only describe what is visibly verifiable in the photo.
- Do NOT invent materials, measurements, brand names, or origin.
- If a piece of information is important but not visible in the photo,
  write "[seller to confirm]" in place of the missing detail.
- Do NOT add a "Questions for the seller" section.
- Use Markdown headings (##) and blank lines between sections.
"""


def generate_listing(image_bytes: bytes, style_prompt: str):
    """Generator that streams the model output token by token."""
    prompt = build_prompt(style_prompt)

    stream = ollama.chat(
        model=MODEL_NAME,
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image_bytes],
        }],
        options={"temperature": 0.7},
        stream=True,
    )

    for chunk in stream:
        content = chunk.get("message", {}).get("content", "")
        if content:
            yield content