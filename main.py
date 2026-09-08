from dotenv import load_dotenv
load_dotenv()  # This loads the .env file
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import os
import shutil
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# In-memory database to store complaints for the map
complaints_db = []

@app.post("/submit-voice-complaint")
async def submit_complaint(
    file: UploadFile = File(...),
    lat: float = Form(...),
    lng: float = Form(...)
):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 1. Transcribe + Translate regional audio to English via Groq Whisper
        with open(temp_file, "rb") as audio:
            translation = groq_client.audio.translations.create(
                file=(temp_file, audio.read()),
                model="whisper-large-v3",
                response_format="json"
            )
        english_text = translation.text

        # 2. Run Groq Llama AI Analysis to extract category, severity, and operator hints
        prompt = f"""
        You are an AI infrastructure analyst for a municipal corporation. 
        Analyze this translated citizen complaint: "{english_text}"

        Return a valid JSON object ONLY, with no extra markdown or text, using these exact keys:
        - "category": Choose from [Road, Garbage, Water, Drainage, Streetlight, Traffic]
        - "issue": Specific issue description (e.g., "Large Pothole", "Overflowing Drain")
        - "severity": Choose from [Critical, High, Medium, Low]
        - "priority_score": Integer from 0 to 100 based on public safety impact
        - "location_hint": Landmark or specific location mention
        - "recommended_action": Actionable hint for the municipal operator on what work to do first
        """

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        ai_response_text = completion.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        ai_data = json.loads(ai_response_text)

        # 3. Create enriched record for the map
        record = {
            "id": len(complaints_db) + 1,
            "complaint": english_text,
            "category": ai_data.get("category", "Road"),
            "issue": ai_data.get("issue", "General Issue"),
            "severity": ai_data.get("severity", "Medium"),
            "priority_score": ai_data.get("priority_score", 50),
            "location_hint": ai_data.get("location_hint", "GPS Location"),
            "recommended_action": ai_data.get("recommended_action", "Inspect site"),
            "latitude": lat,
            "longitude": lng,
            "status": "Pending"
        }
        complaints_db.append(record)

        return {"status": "success", "data": record}

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

@app.get("/all-complaints")
async def get_complaints():
    return complaints_db