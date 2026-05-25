"""Patch ghl-batch7-content-engine.csv:
1. Strip "Comment KEYWORD"/"DM KEYWORD" ManyChat-style CTAs from content column.
2. Replace followUpComment with per-post direct PDF GitHub raw URL based on keyword tag.

Reads:  ghl-batch7-content-engine.csv
Writes: ghl-batch7-content-engine.FINAL.csv  (sibling, original preserved)
"""
import csv, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SRC = Path("C:/Users/info/OneDrive/Desktop/GITHUB/ghl-batch7-content-engine.csv")
OUT = Path("C:/Users/info/OneDrive/Desktop/GITHUB/ghl-batch7-content-engine.FINAL.csv")

PDF_BASE = "https://raw.githubusercontent.com/waseemnasir2k26/skynetjoe-batch7-content/main/pdfs"
KW_TO_PDF = {
    "VIBECODE":  f"{PDF_BASE}/vibe-coding-starter-kit.pdf",
    "BLUEPRINT": f"{PDF_BASE}/ai-automation-blueprint.pdf",
    "PRICING":   f"{PDF_BASE}/agency-pricing-cheatsheet.pdf",
    "STACK":     f"{PDF_BASE}/ai-tools-stack-2026.pdf",
    "PLAYBOOK":  f"{PDF_BASE}/ai-replacement-playbook.pdf",
}
KW_TO_LABEL = {
    "VIBECODE":  "Vibe Coding Starter Kit",
    "BLUEPRINT": "AI Automation Blueprint",
    "PRICING":   "Agency Pricing Cheatsheet",
    "STACK":     "AI Tools Stack 2026",
    "PLAYBOOK":  "AI Replacement Playbook",
}
KEYWORDS = sorted(KW_TO_PDF.keys(), key=len, reverse=True)
KW_PATTERN = re.compile(r"\b(" + "|".join(KEYWORDS) + r")\b")

# ManyChat CTA sentence patterns to strip from content
CTA_PATTERNS = [
    # "Comment KEYWORD and I'll send you ..."
    re.compile(r"(?im)^[ \t]*comment\s+\"?(?:VIBECODE|BLUEPRINT|PRICING|STACK|PLAYBOOK)\"?[^\n]*?(?:\.|$)\s*\n?"),
    # "DM me KEYWORD" / "DM KEYWORD"
    re.compile(r"(?im)^[ \t]*dm(?:\s+me)?\s+\"?(?:VIBECODE|BLUEPRINT|PRICING|STACK|PLAYBOOK)\"?[^\n]*?(?:\.|$)\s*\n?"),
    # "comment KEYWORD and I'll DM..."
    re.compile(r"(?im)comment\s+\"?(?:VIBECODE|BLUEPRINT|PRICING|STACK|PLAYBOOK)\"?[^\n]*?(?:and\s+I[''`]ll\s+(?:DM|send)[^\n]*?(?:\.|$))", re.DOTALL),
]

CLEAN_CLOSER = "Free toolkit linked in the first comment ↓"

def detect_keyword(content: str, tags: str, followup: str) -> str | None:
    """Highest-priority keyword found across the 3 fields."""
    for src in (content, followup, tags.upper()):
        m = KW_PATTERN.search(src)
        if m:
            return m.group(1)
    return None

def strip_manychat_cta(content: str) -> str:
    out = content
    for pat in CTA_PATTERNS:
        out = pat.sub("", out)
    # tidy: collapse 3+ newlines to 2
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out

def main():
    with SRC.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    hdr_row = rows[1]
    cols = {n: i for i, n in enumerate(hdr_row)}
    c_content = cols["content"]
    c_tags    = cols["tags (comma-separated)"]
    c_follow  = cols["followUpComment"]
    c_video   = cols["videoUrls (comma-separated)"]

    patched = 0
    keyword_swapped = 0
    cta_stripped = 0

    for i, row in enumerate(rows):
        if i < 2: continue  # header rows
        if len(row) <= c_follow: continue
        original_content = row[c_content]
        original_follow = row[c_follow]

        kw = detect_keyword(original_content, row[c_tags], original_follow)

        # Strip ManyChat-style CTA from content
        new_content = strip_manychat_cta(original_content)
        if new_content != original_content:
            cta_stripped += 1
            # Append clean closer if the post body now ends abruptly before hashtags
            if "↓" not in new_content and "comment" not in new_content.lower():
                # Insert CLEAN_CLOSER before the first hashtag block, else append
                m = re.search(r"\n(#\w)", new_content)
                if m:
                    idx = m.start()
                    new_content = new_content[:idx] + "\n\n" + CLEAN_CLOSER + new_content[idx:]
                else:
                    new_content = new_content + "\n\n" + CLEAN_CLOSER
            row[c_content] = new_content

        # Swap followUpComment to PDF link if keyword detected
        if kw:
            label = KW_TO_LABEL[kw]
            url = KW_TO_PDF[kw]
            row[c_follow] = f"Free {label} (no signup, no email): {url}"
            keyword_swapped += 1

        patched += 1

    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(rows)

    print(f"Rows processed: {patched}")
    print(f"Keyword-bound followUpComment swapped: {keyword_swapped}")
    print(f"ManyChat CTA stripped from content: {cta_stripped}")
    print(f"Output: {OUT}")

if __name__ == "__main__":
    main()
