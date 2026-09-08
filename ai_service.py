import os
import json
from openai import OpenAI

# Initialize the OpenAI client pointing to Groq's infrastructure
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY", 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),
    base_url="https://api.groq.com/openai/v1"
)

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribes citizen voice notes (including regional languages like 
    Marathi or Hindi) using Groq's high-speed Whisper Large V3 model.
    """
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3", 
            file=audio_file
        )
    return transcript.text

def analyze_complaint_text(text: str) -> dict:
    """
    Sends the transcription to Groq's Llama model to extract structured 
    categories, priorities, location hints, and operator action recommendations.
    """
    prompt = f"""
    You are an AI infrastructure analyst for a municipal corporation. 
    Analyze the following citizen complaint text (which may be in a regional language or English):
    "{text}"

    Extract and return a valid JSON object ONLY, with no extra markdown blocks or conversational text, using these exact keys:
    - "category": Choose from [Road, Garbage, Water, Drainage, Streetlight, Traffic]
    - "issue": Specific issue description (e.g., "Large Pothole", "Overflowing Drain")
    - "severity": Choose from [Critical, High, Medium, Low]
    - "priority_score": Integer from 0 to 100 based on public safety impact
    - "location_hint": Extracted landmark or location description mentioned in text
    - "recommended_action": Specific instruction or hint for the municipal operator on what work to do first
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # High performance Groq model for structured extraction
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        # Clean markdown code blocks if the model wraps output
        cleaned_content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_content)
    except Exception as e:
        # Fallback dictionary if parsing encounters any issue
        return {
            "category": "Road",
            "issue": "General Infrastructure Problem",
            "severity": "Medium",
            "priority_score": 50,
            "location_hint": "Reported via GPS coordinates",
            "recommended_action": "Dispatch local inspection crew to verify issue."
        }