# app/gemini_client.py
import os
import requests
from typing import Dict, Any

# ✅ Import unified guardrails
from app.guardrails import apply_guardrails

GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_ENDPOINT_ENV = "GEMINI_ENDPOINT"

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv(GEMINI_API_KEY_ENV)
        self.endpoint = os.getenv(GEMINI_ENDPOINT_ENV, "https://api.example-gemini.com/v1/generate")

    def generate_response(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> Dict[str, Any]:
        # ✅ Sanitize prompt before sending
        safe_prompt = apply_guardrails(prompt)

        if not self.api_key:
            # Return mock response for local testing
            return {"content": f"[MOCK GEMINI RESPONSE]\n\nPrompt received:\n{safe_prompt[:1000]}"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"prompt": safe_prompt, "max_tokens": max_tokens, "temperature": temperature}

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Extract response content
            if "output" in data:
                content = data["output"]
            elif "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("text") or data["choices"][0].get("message", "")
            else:
                content = str(data)

            # ✅ Apply guardrails to model output as defense-in-depth
            safe_content = apply_guardrails(content)
            return {"content": safe_content}

        except requests.RequestException as e:
            return {"content": f"[ERROR] Gemini API request failed: {str(e)}"}
        except Exception as e:
            return {"content": f"[ERROR] Unexpected error: {str(e)}"}
