from groq import Groq
import streamlit as st


GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# Create Groq client
client = Groq(api_key=GROQ_API_KEY)


def generate_captions(persona_name, persona_style, outfit_description=""):
    prompt = f"""
You are helping an adult content creator write seductive, flirty, or dominant captions for OnlyFans or spicy Twitter.

Persona: {persona_name}
Persona Style: {persona_style}
Photo description: {outfit_description if outfit_description else "Not specified"}

Generate 3 different captions:
- One flirty/teasing 💋
- One kinkier/suggestive 🔥
- One focused on upsell/promo 💼

Keep captions under 25 words, engaging, seductive, and aligned with the persona’s tone. Use emojis sparingly but effectively. Add hashtags if fitting.
"""
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
            temperature=1.0,
            max_tokens=300
        )
        captions = response.choices[0].message.content.strip()
    except Exception as e:
        captions = "⚠️ Failed to generate captions. Try again later."
        print(f"Error: {e}")

    return captions


# Run the test when script is executed directly
if __name__ == "__main__":
    persona_name = "Playful Domme 😈"
    persona_style = "Bold, dominant, and seductive. She loves teasing and being in control."
    outfit_description = "Wearing black leather lingerie, lying on a red velvet couch."

    captions = generate_captions(
        persona_name, persona_style, outfit_description)

    print("\nGenerated Captions:\n")
    print(captions)
