# app/pdf_utils.py
import fitz  # PyMuPDF
from typing import List
from .guardrails import apply_guardrails

def extract_text_from_pdf(path: str) -> str:
    """Extract raw text from all pages of a PDF file."""
    doc = fitz.open(path)
    text_chunks = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text:
            text_chunks.append(text)
        print(f"[DEBUG] Page {i} extracted {len(text)} characters")
    doc.close()
    raw = "\n".join(text_chunks)
    print(f"[DEBUG] Total extracted text length: {len(raw)} characters")
    return raw

def sanitize_text(text: str) -> str:
    """Clean and redact sensitive info from text using unified guardrails."""
    # Normalize line breaks and spaces
    t = text.replace('\r\n', '\n').replace('\r', '\n')
    t = "\n\n".join([p.strip() for p in t.split('\n') if p.strip()])  # collapse multiple empty lines
    t = ' '.join(t.split())  # normalize spaces

    # ✅ Apply unified guardrails (Presidio + Semantic) instead of old regex redact
    t = apply_guardrails(t)
    return t

def segment_text(text: str, max_chunk_chars: int = 800) -> List[str]:
    """Split text into chunks of max ~800 chars, breaking by paragraphs."""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    chunks = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 1 <= max_chunk_chars:
            current = f"{current}\n{p}" if current else p
        else:
            if current:
                chunks.append(current.strip())
            if len(p) > max_chunk_chars:
                # Split long paragraph into smaller chunks
                for i in range(0, len(p), max_chunk_chars):
                    chunks.append(p[i:i+max_chunk_chars].strip())
                current = ""
            else:
                current = p
    if current:
        chunks.append(current.strip())
    print(f"[DEBUG] Segmented into {len(chunks)} chunks")
    return chunks
