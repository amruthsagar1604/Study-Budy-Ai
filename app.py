from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
NOTES_FILE = 'notes.json'

# Gemini Client
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, indent=4, ensure_ascii=False)

@app.route('/api/notes', methods=['GET'])
def get_notes():
    return jsonify(load_notes())

@app.route('/api/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    notes = load_notes()
    note = next((n for n in notes if n['id'] == note_id), None)
    return jsonify(note) if note else jsonify({"error": "Note not found"}), 404

@app.route('/api/upload', methods=['POST'])
def upload_note():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save uploaded image
    ext = file.filename.split('.')[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Read image bytes
    with open(filepath, "rb") as img_file:
        image_bytes = img_file.read()

    # Gemini Handwritten Note Transcription
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes, 
                    mime_type=f"image/{ext}"
                ),
                "You are an expert at reading handwritten notes. Transcribe the content accurately and clearly. "
                "Use proper Markdown formatting:\n"
                "- Use # for headings\n"
                "- Use - for bullet points\n"
                "- Use numbered lists where appropriate\n"
                "- Use **bold** for important terms\n"
                "- Use LaTeX for any math formulas\n"
                "- Describe diagrams or drawings in [square brackets]\n"
                "Preserve the original structure and layout as much as possible."
            ]
        )
        extracted_text = response.text.strip() if hasattr(response, 'text') and response.text else "No text could be extracted."
    except Exception as e:
        extracted_text = f"⚠️ Transcription failed: {str(e)}"

    note = {
        "id": str(uuid.uuid4()),
        "title": file.filename.rsplit('.', 1)[0] or "Untitled Note",
        "image_path": f"/uploads/{filename}",
        "extracted_text": extracted_text,
        "created_at": datetime.now().isoformat(),
        "chat_history": []
    }

    notes = load_notes()
    notes.append(note)
    save_notes(notes)

    return jsonify(note)

@app.route('/api/chat/<note_id>', methods=['POST'])
def chat(note_id):
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    notes = load_notes()
    note = next((n for n in notes if n['id'] == note_id), None)
    if not note:
        return jsonify({"error": "Note not found"}), 404

    note['chat_history'].append({"role": "user", "content": user_message})

    system_prompt = f"""You are StudyBuddy AI - a friendly, encouraging, and smart tutor.
The following is the transcribed content from the student's handwritten notes:

{note['extracted_text']}

Help the student understand and study this material. Be clear, use bullet points, examples, and motivation when appropriate."""

    try:
        full_contents = [system_prompt] + [msg["content"] for msg in note['chat_history']]
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_contents
        )
        assistant_reply = response.text.strip() if hasattr(response, 'text') and response.text else "Sorry, I couldn't generate a response."
    except Exception as e:
        assistant_reply = f"⚠️ AI response error: {str(e)}"

    note['chat_history'].append({"role": "assistant", "content": assistant_reply})
    save_notes(notes)

    return jsonify({"reply": assistant_reply})

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    print("🚀 StudyBuddy AI with Gemini 2.5 Flash (Free Tier) is running at http://localhost:5000")
    app.run(debug=True, port=5000)