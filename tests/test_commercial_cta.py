"""Fail-closed bilingual commercial messaging check for the SEPA site.

A correction to CTA text is source-only until the approved large public rollout.
Does not write generated pages, run external sync, or contact production.
"""
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "site" / "site_content.py"
labels = runpy.run_path(str(SOURCE))["T"]

for lang in ("es", "en"):
    text = labels[lang]["cta_p"]
    assert text and "Cryptopocket" in text
    assert len(text) < 450, f"Unbounded marketing claim: {lang}"
    assert not re.search(r"(?i)(?:iban\\s+virtual|virtual\\s+ibans?|iban\\s+accounts|cuentas?\\s+virtual)", text), (
        f"Unapproved account/IBAN offer in {lang} CTA"
    )
    assert "on/off-ramp" in text, f"Missing verified B2B exchange positioning: {lang}"
    assert "API" in text, f"Missing API-first B2B positioning: {lang}"
    if lang == "es":
        assert "canje" in text and "euros" in text
    else:
        assert "conversion" in text and "euro" in text

# The CTA string is a global template. It may be edited only in a specifically
# approved 35k-page rollout, not in an ordinary daily SEPA delta.
generator = (ROOT / "site" / "build_site.py").read_text(encoding="utf-8")
assert 'cta_p' in generator, "SEPA builder no longer uses reviewed CTA source"
print("PASS: both SEPA CTA languages accurately describe regulated exchange/API; no virtual-IBAN claim")
