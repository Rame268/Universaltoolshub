from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import io
import os
import re
from datetime import timedelta

app = Flask(__name__)
# Use a simple secret key for session. Replace with your own long random key for production.
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-please")
app.permanent_session_lifetime = timedelta(days=30)

# Limits
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB upload limit

# Utility functions
def count_words_char_sentences(text: str):
    text_stripped = text.strip()
    # Words: split on whitespace
    words = re.findall(r"\b\w[\w'-]*\b", text_stripped, flags=re.UNICODE)
    word_count = len(words)
    char_count = len(text_stripped)
    # Sentences: count ., ?, ! and newline blocks — naive but serviceable
    sentences = re.findall(r'[^\s].*?[\.!?](?:\s|$)', text_stripped, flags=re.UNICODE)
    sentence_count = len(sentences)
    return word_count, char_count, sentence_count

# ---------- Routes ----------

@app.route("/")
def index():
    return render_template("index.html")

# Uppercase tool (client-side JS also available)
@app.route("/uppercase", methods=["GET", "POST"])
def uppercase():
    result = ""
    if request.method == "POST":
        text = request.form.get("text", "")
        result = text.upper()
    return render_template("uppercase.html", result=result)

# Word counter - supports AJAX or form POST
@app.route("/wordcounter", methods=["GET", "POST"])
def wordcounter():
    data = {}
    if request.method == "POST":
        text = request.form.get("text", "")
        w, c, s = count_words_char_sentences(text)
        data = {"words": w, "chars": c, "sentences": s, "text": text}
        return jsonify(data)
    return render_template("wordcounter.html")

# PDF to Text
@app.route("/pdf2text", methods=["GET", "POST"])
def pdf2text():
    extracted = ""
    filename = None
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file and file.filename.endswith(".pdf"):
            # Read in-memory
            try:
                reader = PdfReader(file.stream)
                pages_text = []
                for p in reader.pages:
                    pages_text.append(p.extract_text() or "")
                extracted = "\n\n".join(pages_text).strip()
            except Exception as e:
                extracted = f"[Error reading PDF: {e}]"
    return render_template("pdf2text.html", extracted=extracted)

@app.route("/pdf2text/download", methods=["POST"])
def pdf2text_download():
    text = request.form.get("extracted_text", "")
    if not text:
        return redirect(url_for("pdf2text"))
    buffer = io.BytesIO()
    buffer.write(text.encode("utf-8"))
    buffer.seek(0)
    return send_file(buffer,
                     as_attachment=True,
                     download_name="extracted.txt",
                     mimetype="text/plain")

# Habit tracker stored in session
@app.route("/habit", methods=["GET"])
def habit():
    session.permanent = True
    habits = session.get("habits", [])
    return render_template("habit.html", habits=habits)

@app.route("/habit/add", methods=["POST"])
def habit_add():
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Empty name"}), 400
    habits = session.get("habits", [])
    # Each habit: {id, name, done}
    new_id = max([h["id"] for h in habits], default=0) + 1
    habits.append({"id": new_id, "name": name, "done": False})
    session["habits"] = habits
    return jsonify({"ok": True, "habits": habits})

@app.route("/habit/toggle/<int:hid>", methods=["POST"])
def habit_toggle(hid):
    habits = session.get("habits", [])
    for h in habits:
        if h["id"] == hid:
            h["done"] = not h.get("done", False)
            break
    session["habits"] = habits
    return jsonify({"ok": True, "habits": habits})

@app.route("/habit/delete/<int:hid>", methods=["POST"])
def habit_delete(hid):
    habits = session.get("habits", [])
    habits = [h for h in habits if h["id"] != hid]
    session["habits"] = habits
    return jsonify({"ok": True, "habits": habits})

# Quotes
QUOTES = [
    "The best way out is always through. — Robert Frost",
    "Simplicity is the ultimate sophistication. — Leonardo da Vinci",
    "Don't watch the clock; do what it does. Keep going. — Sam Levenson",
    "Do one thing every day that scares you. — Eleanor Roosevelt",
    "Less talking. More doing. — Nobody who wasted time actually succeeded",
    "Progress, not perfection.",
    "If you are tired of starting over, stop giving up.",
    "Discipline is choosing between what you want now and what you want most."
]

@app.route("/quotes")
def quotes():
    return render_template("quotes.html", quotes=QUOTES)

# Static convenience: simple health check
@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
  
