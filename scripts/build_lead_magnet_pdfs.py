"""Render 5 lead-magnet PDFs (Notion-style) from SKYNETLABS_INSTAGRAM_ENGINE.html.

Source: PDF 1..5 lm-box divs (lines ~246-511 in IG Engine HTML).
Output: skynetjoe-batch7-content/pdfs/*.pdf

Style: off-white bg, Inter sans-serif, callout boxes, table-heavy, print-friendly.
"""
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pathlib import Path
import re

SRC = Path("C:/Users/info/OneDrive/Desktop/videos/SKYNETLABS_INSTAGRAM_ENGINE.html")
OUT = Path("C:/Users/info/OneDrive/Desktop/GITHUB/skynetjoe-batch7-content/pdfs")
OUT.mkdir(parents=True, exist_ok=True)

# PDF id -> (output filename, keyword, sub-title) - drives URL + branding
PDFS = [
    ("pdf1", "vibe-coding-starter-kit.pdf",  "VIBECODE",  "The Vibe Coding Starter Kit"),
    ("pdf2", "ai-automation-blueprint.pdf",  "BLUEPRINT", "The AI Automation Blueprint"),
    ("pdf3", "agency-pricing-cheatsheet.pdf","PRICING",   "$0 to $5K Agency Pricing Cheatsheet"),
    ("pdf4", "ai-tools-stack-2026.pdf",      "STACK",     "The AI Tools Stack 2026"),
    ("pdf5", "ai-replacement-playbook.pdf",  "PLAYBOOK",  "The AI Replacement Playbook"),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #fafaf7;
    --ink: #2f3437;
    --muted: #6b6f76;
    --line: #e6e4dd;
    --accent: #2e7d54;
    --accent-bg: #eaf5ee;
    --info: #4a6b8a;
    --info-bg: #eaf0f6;
    --warn: #b5612a;
    --warn-bg: #faf0e6;
    --code-bg: #f1efe8;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ background: var(--bg); color: var(--ink); font-family: 'Inter', -apple-system, sans-serif; font-size: 11.5pt; line-height: 1.55; }}
  .page {{ padding: 48px 56px; max-width: 760px; margin: 0 auto; }}
  header.cover {{
    border-bottom: 1px solid var(--line);
    padding-bottom: 18px; margin-bottom: 28px;
  }}
  header.cover .kicker {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.5pt; color: var(--accent); letter-spacing: 1.5px; font-weight: 500;
    text-transform: uppercase; margin-bottom: 10px;
  }}
  header.cover h1 {{
    font-size: 28pt; line-height: 1.15; font-weight: 700; letter-spacing: -0.5px;
    color: var(--ink); margin-bottom: 8px;
  }}
  header.cover .subtitle {{
    font-size: 11pt; color: var(--muted); font-weight: 400;
  }}
  header.cover .byline {{
    font-size: 9.5pt; color: var(--muted); margin-top: 14px;
    font-family: 'JetBrains Mono', monospace;
  }}
  h4 {{
    font-size: 14pt; font-weight: 600; color: var(--ink);
    margin: 24px 0 10px; padding-top: 18px; border-top: 1px solid var(--line);
    letter-spacing: -0.2px;
  }}
  h4:first-of-type {{ padding-top: 0; border-top: none; margin-top: 8px; }}
  p {{ margin: 8px 0; color: var(--ink); }}
  ul, ol {{ margin: 8px 0 8px 22px; }}
  li {{ margin: 5px 0; }}
  table {{
    width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 10pt;
    border: 1px solid var(--line); border-radius: 6px; overflow: hidden;
  }}
  th, td {{
    padding: 9px 12px; border-bottom: 1px solid var(--line);
    text-align: left; vertical-align: top;
  }}
  th {{ background: var(--code-bg); color: var(--ink); font-weight: 600; font-size: 9.5pt; text-transform: uppercase; letter-spacing: 0.5px; }}
  td {{ color: var(--ink); }}
  tr:last-child td {{ border-bottom: none; }}
  /* Callouts */
  .hl {{
    background: var(--accent-bg); border-left: 3px solid var(--accent);
    padding: 12px 16px; margin: 12px 0; border-radius: 0 6px 6px 0;
    font-size: 10.5pt;
  }}
  .hl::before {{ content: "▸ "; color: var(--accent); font-weight: 700; }}
  .st {{
    background: var(--info-bg); border-left: 3px solid var(--info);
    padding: 12px 16px; margin: 12px 0; border-radius: 0 6px 6px 0;
    font-size: 10.5pt;
  }}
  .st::before {{ content: "★ "; color: var(--info); font-weight: 700; }}
  strong {{ color: var(--ink); font-weight: 600; }}
  code {{
    background: var(--code-bg); padding: 1px 6px; border-radius: 3px;
    font-family: 'JetBrains Mono', monospace; font-size: 9.5pt; color: var(--accent);
  }}
  em {{ color: var(--muted); font-style: italic; }}
  footer.foot {{
    border-top: 1px solid var(--line); margin-top: 32px; padding-top: 14px;
    font-size: 9pt; color: var(--muted); text-align: center;
    font-family: 'JetBrains Mono', monospace;
  }}
  footer.foot a {{ color: var(--accent); text-decoration: none; }}
  /* Pricing comparison block (PDF 3 inline flex) */
  .pricing-compare {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }}
  .pricing-compare > div {{ flex: 1; min-width: 240px; padding: 14px 16px; border-radius: 0 6px 6px 0; }}
  .pc-wrong {{ background: #fdecec; border-left: 3px solid #c43a3a; }}
  .pc-right {{ background: var(--accent-bg); border-left: 3px solid var(--accent); }}
  .pc-wrong strong {{ color: #c43a3a; }}
  .pc-right strong {{ color: var(--accent); }}
  @page {{ size: A4; margin: 0; }}
</style>
</head>
<body>
<div class="page">
  <header class="cover">
    <div class="kicker">SkynetLabs &middot; Lead Magnet &middot; {keyword}</div>
    <h1>{title}</h1>
    <div class="subtitle">{subtitle}</div>
    <div class="byline">by Waseem Nasir &middot; skynetjoe.com</div>
  </header>
  {body}
  <footer class="foot">
    Free toolkit by <a href="https://skynetjoe.com">skynetjoe.com</a> &middot;
    <a href="https://github.com/waseemnasir2k26">github.com/waseemnasir2k26</a> &middot;
    &copy; SKYNETLABS
  </footer>
</div>
</body>
</html>
"""

def extract_pdf_content(soup, pdf_id):
    """Pull the lm-box content for a given PDF section id."""
    sec = soup.find("div", id=pdf_id)
    if not sec:
        return None, None, None
    lm = sec.find("div", class_="lm-box")
    if not lm:
        return None, None, None
    title_el = lm.find("div", class_="pt")
    sub_el = lm.find("div", class_="ps")
    title = title_el.get_text(strip=True) if title_el else ""
    subtitle = sub_el.get_text(" | ", strip=True).split("|")[0].strip() if sub_el else ""

    # Strip cover blocks (pt + ps) and trailing trailing footer <p>
    for el in lm.find_all(["div"], class_=["pt", "ps"]):
        el.decompose()
    # Remove the closing "© SKYNETLABS" paragraph (we re-add in footer)
    last_p = lm.find_all("p")
    for p in last_p:
        if "SKYNETLABS" in p.get_text() or "@skynetjoe" in p.get_text():
            p.decompose()
    # Strip inline style="color:var(--g)" etc — they reference CSS vars not in our template
    for el in lm.find_all(True):
        if el.has_attr("style"):
            # keep .pricing-compare PDF 3 boxes — convert
            s = el["style"]
            if "min-width:220px" in s and "var(--pk)" in s:
                el["class"] = el.get("class", []) + ["pc-wrong"]
                del el["style"]
            elif "min-width:220px" in s and "var(--g)" in s:
                el["class"] = el.get("class", []) + ["pc-right"]
                del el["style"]
            elif "display:flex" in s and "gap:12px" in s:
                el["class"] = el.get("class", []) + ["pricing-compare"]
                del el["style"]
            else:
                # blanket strip — colors don't exist in our scope
                del el["style"]
    # Strip inline color on table cells — th color attrs etc
    body_html = "".join(str(c) for c in lm.children)
    return title, subtitle, body_html

def main():
    soup = BeautifulSoup(SRC.read_text(encoding="utf-8"), "html.parser")
    rendered = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        for pdf_id, fname, keyword, sub in PDFS:
            title, subtitle_raw, body = extract_pdf_content(soup, pdf_id)
            if not body:
                print(f"  SKIP {pdf_id} — no content")
                continue
            html = TEMPLATE.format(
                title=title or sub,
                subtitle=subtitle_raw or "",
                keyword=keyword,
                body=body,
            )
            tmp_html = OUT / f"_tmp_{pdf_id}.html"
            tmp_html.write_text(html, encoding="utf-8")
            page.goto(tmp_html.as_uri(), wait_until="networkidle")
            page.wait_for_timeout(400)
            out_path = OUT / fname
            page.pdf(
                path=str(out_path),
                format="A4",
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                print_background=True,
            )
            size_kb = out_path.stat().st_size / 1024
            print(f"  rendered {fname}  {size_kb:.0f} KB")
            rendered.append(fname)
            tmp_html.unlink(missing_ok=True)
        browser.close()
    print(f"\nDone. {len(rendered)} PDFs in {OUT}")

if __name__ == "__main__":
    main()
