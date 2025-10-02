print("🚀 Flask app is starting... (debug check)")
import os
import json
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from langdetect import detect, LangDetectException

# ----------------- Flask Setup -----------------
app = Flask(__name__)
CORS(app)

# ----------------- Paths -----------------
KB_PATH = "knowledge_base.json"
DB_PATH = "chat_logs.db"

# ----------------- Database Init -----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_text TEXT,
                  detected_lang TEXT,
                  response_text TEXT,
                  intent TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
init_db()

# ----------------- Load Knowledge Base -----------------
with open(KB_PATH, "r", encoding="utf-8") as f:
    KB = json.load(f)

# ----------------- Utility Functions -----------------
def log_query(user_text, detected_lang, response_text, intent):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_text, detected_lang, response_text, intent) VALUES (?, ?, ?, ?)",
              (user_text, detected_lang, response_text, intent))
    conn.commit()
    conn.close()

def detect_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

# ✅ Updated function: gives specific info (symptoms / prevention / advice) if user asks
def kb_lookup(query):
    q = query.lower()
    for key in KB:
        if key in q:
            data = KB[key]

            if "symptom" in q:
                return key, f"**{key.title()} Symptoms:** {data['symptoms']}"
            elif "prevention" in q:
                return key, f"**{key.title()} Prevention:** {data['prevention']}"
            elif "advice" in q or "treatment" in q:
                return key, f"**{key.title()} Advice:** {data['advice']}"
            else:
                # Default full info
                resp = (f"**{key.title()}**\n"
                        f"Symptoms: {data['symptoms']}\n"
                        f"Prevention: {data['prevention']}\n"
                        f"Advice: {data['advice']}")
                return key, resp

    return None, None

# ----------------- Routes -----------------
@app.route("/")
def home():
    return "✅ Flask is running correctly!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_text = data.get("text", "").strip()

    if not user_text:
        return jsonify({"error": "No input text provided."}), 400

    detected_lang = detect_language(user_text)
    intent, kb_resp = kb_lookup(user_text)

    if kb_resp:
        response_text = kb_resp
        intent_label = intent
    else:
        response_text = ("Sorry, I don't have specific information on that. "
                         "Please consult a health provider or ask about dengue, malaria, or covid.")
        intent_label = "fallback"

    log_query(user_text, detected_lang, response_text, intent_label)
    return jsonify({
        "query": user_text,
        "detected_lang": detected_lang,
        "intent": intent_label,
        "response": response_text
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "public_health_chatbot_backend"})

# ----------------- Run Server -----------------
if __name__ == "__main__":
    print("✅ Entered main block, about to run Flask server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
