from groq import Groq
import streamlit as st


GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# Create Groq client
client = Groq(api_key=GROQ_API_KEY)


def generate_dm_reply(persona_name, persona_prompt, user_message):
    prompt = f"""
You are roleplaying as an {persona_name} persona on OnlyFans. You're flirty, seductive, and creative with words.

Persona prompt:
{persona_prompt}

A fan sent you this DM:
"{user_message}"

Write a sexy, teasing response in character.
Keep it short, fun, and engaging.
"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
        temperature=0.9,
        max_tokens=200
    )

    reply = response.choices[0].message.content.strip()
    return reply  # ✅ added return


def generate_mass_dm(persona_name, persona_prompt, campaign_theme):
    prompt = f"""
You are a seductive OnlyFans model with the persona: {persona_name}

Persona style:
{persona_prompt}

Generate a short, seductive mass message promoting a new content drop.
Theme: {campaign_theme}

Make it teasing, slightly explicit but still classy. No links or banned words.
"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
        temperature=0.9,
        max_tokens=200
    )

    reply = response.choices[0].message.content.strip()
    return reply  # ✅ added return
