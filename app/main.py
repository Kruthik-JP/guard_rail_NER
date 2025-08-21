# app/main.py
import os
import fitz  # PyMuPDF
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai
import sys
import re

# ===== Guardrails (unified) =====
try:
    from app.guardrails import apply_guardrails, advanced_guardrails
except Exception:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from guardrails import apply_guardrails, advanced_guardrails

# ===== Load environment variables =====
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SBERT_MODEL = os.getenv("SBERT_MODEL", "all-MiniLM-L6-v2")
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env file")

# ===== Configure Gemini client =====
genai.configure(api_key=GOOGLE_API_KEY)

# ===== Paths & Constants =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESUME_FOLDER = os.path.join(BASE_DIR, "resumes")
FAISS_INDEX_FILE = os.path.join(BASE_DIR, "faiss_index.index")
TEXT_STORE_FILE = os.path.join(BASE_DIR, "resume_texts.pkl")

# ===== Flask app =====
app = Flask(__name__, template_folder="templates", static_folder="static")


# ===== Extra Guardrail: Block Academic Scores =====
def block_academic_scores(text: str) -> str:
    """
    Redacts CGPA/GPA/marks/grades from text.
    Keeps other resume info visible.
    """
    patterns = [
        r"\bCGPA[:\s]*\d+(\.\d+)?\b",
        r"\bGPA[:\s]*\d+(\.\d+)?\b",
        r"\b\d+(\.\d+)?\s*/\s*10\b",  # e.g. 8.5 / 10
        r"\b\d+(\.\d+)?\s*/\s*100\b", # e.g. 85 / 100
        r"\bmarks[:\s]*\d+%?\b",
        r"\bgrade[:\s]*[A-F][+-]?\b"
    ]
    redacted = text
    for pat in patterns:
        redacted = re.sub(pat, "[REDACTED_SCORE]", redacted, flags=re.IGNORECASE)
    return redacted


# ===== Helpers =====
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF and sanitize with guardrails."""
    text = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text.append(page.get_text())
    raw = "\n".join(text).strip()
    # ✅ Sanitize but allow names/resume details
    return apply_guardrails(raw)


def create_embeddings(texts):
    """Generate embeddings for sanitized texts."""
    model = SentenceTransformer(SBERT_MODEL)
    safe_texts = [apply_guardrails(t) for t in texts]
    embeddings = model.encode(safe_texts, convert_to_numpy=True, show_progress_bar=False)
    return model, np.array(embeddings)


def build_faiss_index():
    """Build FAISS index from resumes with guardrails."""
    if not os.path.exists(RESUME_FOLDER):
        os.makedirs(RESUME_FOLDER)
        return False

    pdf_files = [f for f in os.listdir(RESUME_FOLDER) if f.lower().endswith(".pdf")]
    if not pdf_files:
        return False

    texts = [extract_text_from_pdf(os.path.join(RESUME_FOLDER, pdf)) for pdf in pdf_files]
    model, embeddings = create_embeddings(texts)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, FAISS_INDEX_FILE)
    with open(TEXT_STORE_FILE, "wb") as f:
        pickle.dump((texts, model), f)

    return True


def search_resumes(query: str):
    """Vector search sanitized corpus."""
    if not (os.path.exists(FAISS_INDEX_FILE) and os.path.exists(TEXT_STORE_FILE)):
        return None

    index = faiss.read_index(FAISS_INDEX_FILE)
    with open(TEXT_STORE_FILE, "rb") as f:
        texts, model = pickle.load(f)

    safe_query = apply_guardrails(query)
    query_vector = model.encode([safe_query], convert_to_numpy=True, show_progress_bar=False)
    distances, indices = index.search(query_vector, k=1)

    if len(indices) == 0 or indices[0][0] == -1:
        return None

    return texts[indices[0][0]]  # Already sanitized


# ===== Routes =====
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/build_index", methods=["GET"])
def build_index_route():
    if build_faiss_index():
        return jsonify({"message": "✅ Resume index built successfully"}), 200
    return jsonify({"error": "❌ No PDFs found in resumes/ folder"}), 400


@app.route("/query", methods=["POST"])
def query_resume():
    data = request.get_json() or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Query is required"}), 400

    matched_text = search_resumes(query)
    if not matched_text:
        return jsonify({"error": "No relevant resume data found for your query."}), 404

    # ✅ Redact sensitive data but keep names & resume info
    redacted_text = apply_guardrails(matched_text)
    redacted_text = block_academic_scores(redacted_text)  # 🚨 block CGPA/GPA/marks

    # ✅ Guardrails check (soft enforcement: redact, don’t block unless high risk)
    analysis = advanced_guardrails.analyze_content(redacted_text)
    if not analysis["safe"] and analysis.get("risk_score", 0) > 0.8:
        return jsonify({
            "answer": "[❌ Query blocked: contains high-risk sensitive information]",
            "blocked_terms": analysis["metadata"].get("pii_types", []),
            "risk_score": analysis.get("risk_score", 0.0)
        }), 403

    # ✅ Prompt for Gemini
    prompt = (
        "You are a resume assistant. DO NOT reveal any sensitive personal information such as "
        "bank account numbers, passwords, credit card numbers, CVV codes, social security numbers, phone numbers, emails, or academic scores (CGPA, GPA, marks, grades).\n\n"
        f"Here is the sanitized resume text:\n{redacted_text}\n\n"
        f"Question: {apply_guardrails(query)}\nAnswer:"
    )

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        response_text = response.text or "[⚠️ No response from model]"
    except Exception as e:
        return jsonify({"error": f"Gemini API error: {str(e)}"}), 500

    # ✅ Final guardrails check + block academic scores again
    response_text = block_academic_scores(response_text)
    final_analysis = advanced_guardrails.analyze_content(response_text)
    if not final_analysis["safe"] and final_analysis.get("risk_score", 0) > 0.8:
        return jsonify({
            "answer": "[❌ Response hidden: sensitive content detected]",
            "blocked_terms": final_analysis["metadata"].get("pii_types", []),
            "risk_score": final_analysis.get("risk_score", 0.0)
        }), 403

    return jsonify({"answer": response_text})


# ===== Entrypoint =====
if __name__ == "__main__":
    if not os.path.exists(RESUME_FOLDER):
        os.makedirs(RESUME_FOLDER)
    app.run(host="0.0.0.0", port=8080, debug=True)
