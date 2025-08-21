# 🚧 Guard Rail NER Project  

![GitHub](https://img.shields.io/github/license/Kruthik-JP/guard_rail_NER)  
![Python](https://img.shields.io/badge/Python-3.10-blue)  
![PyTorch](https://img.shields.io/badge/PyTorch-2.1-red)  

A **Secure AI Chatbot and NER system** for guard rail data and sensitive document handling.  
This project ensures **all new uploaded data, including PDFs and sensitive info (PAN, Aadhaar, etc.), is automatically protected** using NER and PII handling, making it safe against instruction-breaking inputs.  

---

## 🔍 Project Overview  
The **Guard Rail NER system** is designed to:  
- Provide a **secure chatbot** with advanced Guardrails applied at multiple stages:  
  - Data Extraction  
  - Pre-Embedding  
  - Pre-API  
  - Pre-LLM  
- Automatically protect sensitive information using **NER and PII handling**.  
- Detect and classify entities from guard rail–related documents and structured/unstructured text.  
- Ensure safety against **malicious or instruction-breaking inputs** during processing.  

---

## 🛠 Features  
- ✅ Secure chatbot framework with **multi-layer Guardrails**.  
- ✅ Automatic detection & masking of **sensitive information** (PAN, Aadhaar, etc.).  
- ✅ Advanced **NER pipeline** for entity extraction & classification.  
- ✅ Preprocessing, segmentation, and **safe embeddings** for LLM inputs.  
- ✅ Cloud-ready deployment for **multi-user secure access**.  
- ✅ Easily extendable to **new datasets and documents**.  

---



---

## 💻 Installation & Setup  

1. **Clone the repository**  
```bash
git clone https://github.com/Kruthik-JP/guard_rail_NER.git
cd guard_rail_NER

##2. ** Create a virtual environment**

python -m venv venv
venv\Scripts\activate    # For Windows
# or
source venv/bin/activate # For Linux/Mac

3. Install dependencies

pip install -r requirements.txt

4. Run the project

python main.py


⚙️ Scripts

preprocess.py – Preprocess uploaded documents and safe embedding.

train.py – Train models for entity extraction and classification.

predict.py – Predict entities and protect sensitive data.

evaluate.py – Evaluate model accuracy and data protection metrics.


📊 Model & Guardrail Details

NER Models – Entity extraction and PII detection.

Pre-Embedding Guardrails – Filters and masks sensitive data before embedding.

Pre-API Guardrails – Validates requests & prevents unsafe API calls.

Pre-LLM Guardrails – Ensures instruction-following safety.

Secure Pipeline – Data flow:

Upload → Processing → Embedding → LLM Input (Protected)




📝 Contribution Guidelines
Fork the repository.

Create a new branch for your feature/fix:

bash
Copy
Edit
git checkout -b feature-name
Commit your changes:

bash
Copy
Edit
git commit -m "Add feature/fix description"
Push and create a Pull Request.

📧 Author
Kruthik JP

GitHub: Kruthik-JP

Email:kruthikjp.ai@gmail.com


📌 References

Guardrails AI – Framework for adding safety layers to LLM applications.

Microsoft Presidio – Open-source tool for detecting and anonymizing PII.

spaCy – Industrial-strength NLP library for NER.

Hugging Face Transformers – Pretrained models for token classification & NER.

FAISS – Vector similarity search library for fast embedding retrieval.

Chroma DB – Open-source embedding database for document storage & retrieval.

LangChain + Google Generative AI – For embeddings and secure chatbot integration.

FastAPI – Modern Python framework for building APIs and chatbot backends.

Docker – Containerization and deployment.


## 📁 File Structure  

GUARD_RAIL_NER/
│
├── app/                                # Core application code
│   ├── __pycache__/                     # Python cache files
│   ├── resumes/                         # Uploaded resumes/documents
│   ├── static/                          # Static assets for frontend
│   │   └── style.css                    # CSS styling for chatbot UI
│   ├── templates/                       # Frontend templates (Jinja2/FastAPI)
│   │   └── index.html                   # Main HTML page for chatbot interface
│   ├── __init__.py                      # Marks app/ as a package
│   ├── chroma_client.py                 # ChromaDB client (vector database)
│   ├── embedder.py                      # Embedding functions for documents
│   ├── faiss_index.index                # FAISS vector DB index (local storage)
│   ├── gemini_client.py                 # Google Gemini API client
│   ├── guardrails.py                    # Guardrails (security & PII filtering)
│   ├── main.py                          # Main FastAPI application entry
│   ├── pdf_utils.py                     # PDF parsing & text extraction utils
│   └── resume_texts.pkl                 # Pre-processed & serialized resume data
│
├── data/                                # Data handling layer
│   └── resumes/                         # Resume dataset (raw files)
│       └── read_resume.py               # Script to parse/process resumes
│
├── resumes/                             # (Optional) Folder for uploads
│
├── venv/                                # Python virtual environment
│
├── .env                                 # Environment variables (API keys, DB config)
├── Dockerfile                           # Containerization config for deployment
├── faiss_index.index                    # Root-level FAISS index (global DB)
├── rebuild                              # (Possibly a build/output directory)
├── requirements.txt                     # Python dependencies
└── resume_texts.pkl                     # Root-level pickle file (resume data)

✅ Observations:

You have two copies of:

faiss_index.index (one in app/, one in root)

resume_texts.pkl (one in app/, one in root)
👉 Better to keep only one (maybe in data/) for cleaner structure.

main.py is the entry point → runs FastAPI backend.

templates/index.html + static/style.css → gives you a basic UI for chatbot/resume upload.

guardrails.py + pdf_utils.py + pii detection (if added later) → are your security & data processing layers.

chroma_client.py + faiss_index.index + embedder.py → form your vector database + embedding pipeline.
