"""
Unified Guardrails System (Updated)
- Allows names/person entities (not blocked)
- Redacts only sensitive data (emails, phone, CGPA, marks, accounts, etc.)
- Never fully blocks queries, always returns sanitized response
"""
#guard rail
import logging
from typing import Dict, Any
from presidio_analyzer import AnalyzerEngine
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)

# ==========================
# 🔹 Configuration
# ==========================
PII_DETECTION_CONFIG = {
    'thresholds': {
        'semantic_similarity': 0.75,
        'risk_score': 0.5,
        'presidio_confidence': 0.7
    },
    # 🚨 PERSON/NAME deliberately excluded
    'entities': [
        "CREDIT_CARD", "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN",
        "BANK_ACCOUNT", "IBAN_CODE", "IFSC_CODE", "PAN_NUMBER",
        "AADHAAR_NUMBER", "LOCATION", "URL"
    ],
    'sensitive_topics': [
        "bank account", "credit card", "debit card", "ifsc code", "cvv",
        "social security number", "ssn", "pan card", "aadhaar", "passport",
        "routing number", "account number", "pin", "password", "otp",
        "salary", "compensation", "ctc", "package", "banking details",
        "net banking", "upi id", "paytm", "google pay", "phonepe",
        "linkedin", "github",
        # 🚨 Education-related sensitive data
        "cgpa", "marks", "gpa", "grade", "percentage"
    ],
    'high_risk_entities': [
        "CREDIT_CARD", "US_SSN", "BANK_ACCOUNT", "AADHAAR_NUMBER",
        "PAN_NUMBER", "IFSC_CODE", "EMAIL_ADDRESS", "PHONE_NUMBER", "URL"
    ],
    'redaction_patterns': {
        'EMAIL_ADDRESS': '[EMAIL_REDACTED]',
        'PHONE_NUMBER': '[PHONE_REDACTED]',
        'US_SSN': '[SSN_REDACTED]',
        'CREDIT_CARD': '[CARD_REDACTED]',
        'BANK_ACCOUNT': '[ACCOUNT_REDACTED]',
        'IFSC_CODE': '[IFSC_REDACTED]',
        'PAN_NUMBER': '[PAN_REDACTED]',
        'AADHAAR_NUMBER': '[AADHAAR_REDACTED]',
        'URL': '[LINK_REDACTED]',
        # 🚨 Custom redactions for education
        'CGPA': '[CGPA_REDACTED]',
        'MARKS': '[MARKS_REDACTED]',
        'GPA': '[GPA_REDACTED]',
        'PERCENTAGE': '[PERCENTAGE_REDACTED]'
    }
}

DETECTION_MODES = {
    'strict': {
        'semantic_threshold': 0.6,
        'risk_threshold': 0.3,
        'block_on_pii': False
    },
    'moderate': {
        'semantic_threshold': 0.75,
        'risk_threshold': 0.5,
        'block_on_pii': False
    },
    'lenient': {
        'semantic_threshold': 0.85,
        'risk_threshold': 0.7,
        'block_on_pii': False
    }
}
DEFAULT_DETECTION_MODE = 'moderate'


# ==========================
# 🔹 Advanced PII Detector
# ==========================
class AdvancedPIIDetector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analyzer = self._setup_presidio()
        self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.sensitive_embeddings = self._load_sensitive_embeddings()

    def _setup_presidio(self):
        try:
            return AnalyzerEngine()
        except Exception as e:
            logger.warning(f"Presidio init failed: {e}")
            return None

    def _load_sensitive_embeddings(self):
        embeddings = self.semantic_model.encode(
            self.config['sensitive_topics'], convert_to_tensor=True
        )
        return {'topics': self.config['sensitive_topics'], 'embeddings': embeddings}

    def detect_pii_with_presidio(self, text: str):
        if not self.analyzer:
            return []
        try:
            results = self.analyzer.analyze(
                text=text,
                entities=self.config['entities'],  # PERSON excluded
                language="en"
            )
            return [
                {
                    'entity_type': r.entity_type,
                    'start': r.start,
                    'end': r.end,
                    'score': r.score,
                    'text': text[r.start:r.end]
                } for r in results
            ]
        except Exception as e:
            logger.error(f"Presidio failed: {e}")
            return []

    def detect_semantic_pii(self, text: str):
        try:
            text_embedding = self.semantic_model.encode(text, convert_to_tensor=True)
            sims = util.cos_sim(text_embedding, self.sensitive_embeddings['embeddings'])
            max_sim = sims.max().item()
            if max_sim > self.config['thresholds']['semantic_similarity']:
                idx = sims.argmax().item()
                topic = self.config['sensitive_topics'][idx]
                return {
                    'detected': True,
                    'similarity': max_sim,
                    'matched_topic': topic
                }
            return {'detected': False, 'similarity': max_sim}
        except Exception as e:
            logger.error(f"Semantic detection failed: {e}")
            return {'detected': False, 'similarity': 0.0}

    def analyze_text(self, text: str):
        presidio = self.detect_pii_with_presidio(text)
        semantic = self.detect_semantic_pii(text)
        detections = presidio
        return {
            'contains_pii': bool(detections or semantic['detected']),
            'presidio_detections': presidio,
            'semantic_detection': semantic,
            'all_detections': detections,
            'risk_score': self._calculate_risk(detections, semantic)
        }

    def _calculate_risk(self, detections, semantic):
        score = len(detections) * 0.3
        if semantic['detected']:
            score += semantic['similarity'] * 0.5
        for d in detections:
            if d['entity_type'] in self.config['high_risk_entities']:
                score += 0.4
        return min(score, 1.0)

    def redact_pii(self, text: str, analysis: Dict[str, Any]):
        """Redact PII + sensitive topics (cgpa, marks, etc.)"""
        redacted = text
        # Presidio detections
        detections = analysis['presidio_detections']
        detections.sort(key=lambda x: x['start'], reverse=True)
        for d in detections:
            repl = self.config['redaction_patterns'].get(
                d['entity_type'], f"[{d['entity_type']}_REDACTED]"
            )
            redacted = redacted[:d['start']] + repl + redacted[d['end']:]
        # Semantic detections like CGPA/marks
        if analysis['semantic_detection'].get('detected'):
            topic = analysis['semantic_detection'].get('matched_topic', '').upper()
            if "CGPA" in topic:
                redacted = redacted.replace("CGPA", "[CGPA_REDACTED]")
            elif "MARKS" in topic:
                redacted = redacted.replace("marks", "[MARKS_REDACTED]")
            elif "GPA" in topic:
                redacted = redacted.replace("GPA", "[GPA_REDACTED]")
            elif "PERCENTAGE" in topic:
                redacted = redacted.replace("%", "[PERCENTAGE_REDACTED]")
        return redacted


# ==========================
# 🔹 Guardrails API
# ==========================
detector = AdvancedPIIDetector(PII_DETECTION_CONFIG)

def apply_guardrails(text: str, mode: str = DEFAULT_DETECTION_MODE) -> str:
    """Sanitize text before use (embedding, indexing, LLM, etc.)"""
    analysis = detector.analyze_text(text)
    if analysis['contains_pii']:
        return detector.redact_pii(text, analysis)
    return text


# ==========================
# 🔹 Advanced Guardrails Wrapper
# ==========================
class AdvancedGuardrails:
    def analyze_content(self, text: str):
        analysis = detector.analyze_text(text)
        return {
            "safe": True,  # 🚨 always safe after redaction
            "metadata": {
                "presidio_detections": analysis['presidio_detections'],
                "semantic_detection": analysis['semantic_detection'],
                "pii_types": [d['entity_type'] for d in analysis['presidio_detections']]
            },
            "risk_score": analysis['risk_score']
        }

advanced_guardrails = AdvancedGuardrails()
