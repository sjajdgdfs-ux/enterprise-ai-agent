import re
import ipaddress
from urllib.parse import urlparse

class SecurityShield:
    def __init__(self):
        # أنماط الكلمات المشبوهة لحقن الأوامر (Prompt Injection)
        self.injection_patterns = [
            r"ignore previous instructions",
            r"system prompt",
            r"disregard all prior",
            r"you are now a",
            r"forget everything",
            r"bypass security",
            r"override rule"
        ]
        # أنماط البيانات الحساسة (PII)
        self.pii_patterns = {
            "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "PHONE": r"\+?\d{10,15}"
        }

    def check_prompt_injection(self, text: str) -> bool:
        """تكتشف محاولات اختراق الأوامر ورسائل النظام"""
        for pattern in self.injection_patterns:
            if re.search(pattern, text.lower()):
                return True
        return False

    def redact_pii(self, text: str) -> str:
        """تحجب البيانات الحساسة فوراً من الرسائل"""
        redacted = text
        for label, pattern in self.pii_patterns.items():
            redacted = re.sub(pattern, f"[{label}_REDACTED]", redacted)
        return redacted

    def validate_url_ssrf(self, url_string: str) -> bool:
        """تمنع ثغرات Server-Side Request Forgery (SSRF) بحظر عناوين IP المحلية الممنوعة"""
        try:
            parsed = urlparse(url_string)
            hostname = parsed.hostname
            if not hostname:
                return False
            
            # فحص إذا كان العنوان IP خاص أو محلي أو Metadata الخاص بـ AWS/GCP
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except ValueError:
                # اسم نطاق وليس IP مباشر
                forbidden_metadata = ["169.254.169.254", "metadata.google.internal", "localhost"]
                if any(meta in hostname.lower() for meta in forbidden_metadata):
                    return False
            return True
        except Exception:
            return False