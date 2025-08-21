import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
from dotenv import load_dotenv

# ✅ Import unified guardrails
from app.guardrails import apply_guardrails

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")

# Configure Google Gemini API
genai.configure(api_key=GEMINI_API_KEY)
MODEL = genai.GenerativeModel("gemini-pro")

# Path to your resume
PDF_PATH = os.path.join("resumes", "updated_resume_kruthik.pdf")

# ===== Function to extract text from PDF =====
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    raw_text = text.strip()
    # ✅ Apply guardrails to redact sensitive info
    sanitized_text = apply_guardrails(raw_text)
    return sanitized_text

# ===== Main script =====
if __name__ == "__main__":
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"Resume file not found at {PDF_PATH}")

    # Step 1: Extract and sanitize resume text
    resume_text = extract_text_from_pdf(PDF_PATH)
    print("✅ Resume text extracted and sanitized.")

    # Step 2: Ask questions in a loop
    while True:
        query = input("\nAsk a question about the resume (or type 'exit' to quit): ")
        if query.lower() == "exit":
            break

        # ✅ Sanitize user query before sending to Gemini
        safe_query = apply_guardrails(query)

        prompt = (
            "You are a resume assistant. STRICTLY DO NOT reveal any sensitive or personal information "
            "such as bank account numbers, passwords, credit card numbers, CVV codes, social security numbers, "
            "phone numbers, or emails.\n\n"
            f"Based on the following sanitized resume text:\n{resume_text}\n\nQuestion: {safe_query}\nAnswer:"
        )

        # Call Gemini
        try:
            response = MODEL.generate_content(prompt)
            # ✅ Apply guardrails on model output as defense-in-depth
            safe_response = apply_guardrails(response.text)
            print("\n🤖 Answer:", safe_response)
        except Exception as e:
            print(f"[ERROR] Gemini API error: {str(e)}")
