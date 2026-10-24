import re

class SecurityShield:
    def __init__(self):
        self.injection_patterns = [
            r"ignore previous instructions",
            r"system prompt",
            r"disregard all prior",
            r"you are now a",
            r"forget everything"
        ]
        self.pii_patterns = {
            "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "PHONE": r"\+?\d{10,15}"
        }

    def check_prompt_injection(self, text: str) -> bool:
        for pattern in self.injection_patterns:
            if re.search(pattern, text.lower()):
                return True
        return False

    def redact_pii(self, text: str) -> str:
        redacted = text
        for label, pattern in self.pii_patterns.items():
            redacted = re.sub(pattern, f"[{label}_REDACTED]", redacted)
        return redacted