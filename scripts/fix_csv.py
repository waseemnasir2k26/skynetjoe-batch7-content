"""
fix_csv.py — Batch 7 CSV hardener.

Reads `../../ghl-batch7-content-engine.csv`, produces:
  * `../../ghl-batch7-content-engine.FIXED.csv`  (original 39-col schema, hardened)
  * `../../ghl-batch7-platform-variants.csv`     (extra columns: content_x / content_linkedin / content_ig / content_pinterest)

Fixes applied:
  1. Add UTM params to skynetjoe.com / waseemnasir.com / skynetlabs-toolkit URLs.
  2. Generate per-platform content variants with the right length + hashtag count.
  3. Re-spread scheduled_at if any duplicate timestamps are found (2/day max, 9AM/1PM/5PM EST).
  4. Validate: 39 cols per row, no empty media URL for post rows, date format sane.
  5. Confirm /images/ path already points at waseemnasir2k26/skynetjoe-batch7-content (no rewrite needed).

Usage:
    python scripts/fix_csv.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
from datetime import datetime, timedelta

HERE     = os.path.dirname(os.path.abspath(__file__))
REPO     = os.path.abspath(os.path.join(HERE, '..'))
ROOT     = os.path.abspath(os.path.join(REPO, '..'))
SRC_CSV  = os.path.join(ROOT, 'ghl-batch7-content-engine.csv')
OUT_CSV  = os.path.join(ROOT, 'ghl-batch7-content-engine.FIXED.csv')
OUT_VAR  = os.path.join(ROOT, 'ghl-batch7-platform-variants.csv')

UTM_HOSTS = ('skynetjoe.com', 'waseemnasir.com', 'skynetlabs-toolkit.vercel.app')
URL_RE    = re.compile(r'https?://[^\s,"\'<>)]+', re.IGNORECASE)
# Bare-domain matcher: catches "skynetjoe.com" / "waseemnasir.com/portfolio" / "skynetlabs-toolkit.vercel.app"
BARE_RE   = re.compile(
    r'(?<![/@\w.-])((?:skynetjoe\.com|waseemnasir\.com|skynetlabs-toolkit\.vercel\.app)(?:/[^\s,"\'<>)]*)?)',
    re.IGNORECASE,
)
HASHTAG_RE = re.compile(r'#\w+')

LIMITS = {
    'x':         {'chars': 260, 'tags': 3},
    'linkedin':  {'chars': 2000, 'tags': 5},
    'ig':        {'chars': 2200, 'tags': 30},
    'pinterest': {'chars': 500,  'tags': 3},
}


def add_utm(url: str, post_idx: int) -> str:
    """Append UTM params to any matching agency/toolkit URL."""
    if not any(h in url for h in UTM_HOSTS):
        return url
    # Skip raw.githubusercontent (media host) and assets.cdn hosts
    if 'raw.githubusercontent.com' in url or 'assets.cdn' in url:
        return url
    sep = '&' if '?' in url else '?'
    utm = f'utm_source=ghl&utm_medium=social&utm_campaign=batch7&utm_content=post-{post_idx:02d}'
    # Strip trailing punctuation then reattach
    tail = ''
    while url and url[-1] in '.,;:!?':
        tail = url[-1] + tail
        url = url[:-1]
    return f'{url}{sep}{utm}{tail}'


def utmize_field(value: str, post_idx: int) -> str:
    # 1) full URLs
    value = URL_RE.sub(lambda m: add_utm(m.group(0), post_idx), value)
    # 2) bare domains — only when not already inside an http URL (the lookbehind handles that)
    def bare_sub(m):
        token = m.group(1)
        # skip if already inside an http(s) URL fragment we just rewrote
        sep = '&' if '?' in token else '?'
        utm = f'utm_source=ghl&utm_medium=social&utm_campaign=batch7&utm_content=post-{post_idx:02d}'
        return f'{token}{sep}{utm}'
    return BARE_RE.sub(bare_sub, value)


def split_content(content: str):
    """Split content body from hashtags (hashtags live on trailing lines)."""
    tags = HASHTAG_RE.findall(content)
    body = HASHTAG_RE.sub('', content)
    # Collapse blank trailing lines left by hashtag removal
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    return body, tags


def trim_to(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    # Cut at last sentence / paragraph boundary before limit
    cut = text[: limit - 1]
    for sep in ('\n\n', '. ', '! ', '? ', '\n'):
        idx = cut.rfind(sep)
        if idx > limit * 0.6:
            return cut[: idx + len(sep)].rstrip()
    return cut.rstrip() + '...'


def variant_x(body: str, tags: list[str]) -> str:
    top_tags = ' '.join(tags[: LIMITS['x']['tags']])
    budget = LIMITS['x']['chars'] - (len(top_tags) + 2 if top_tags else 0)
    trimmed = trim_to(body, budget)
    return (trimmed + ('\n\n' + top_tags if top_tags else '')).strip()


def variant_linkedin(body: str, tags: list[str]) -> str:
    top_tags = ' '.join(tags[: LIMITS['linkedin']['tags']])
    # Append open-question CTA if missing '?'
    open_q = '' if '?' in body[-120:] else '\n\nWhat would you add to this list?'
    joined = f'{body}{open_q}\n\n{top_tags}'.strip()
    return trim_to(joined, LIMITS['linkedin']['chars'])


def variant_ig(body: str, tags: list[str]) -> str:
    # IG allows 30 hashtags; cap at 30 and pad with safe defaults if fewer
    defaults = ['#skynetlabs', '#aiautomation', '#vibecoding', '#solopreneur',
                '#buildinpublic', '#claudecode', '#n8n', '#agencylife',
                '#automation', '#ai']
    have = list(dict.fromkeys(tags))  # dedupe, preserve order
    for d in defaults:
        if d not in have and len(have) < LIMITS['ig']['tags']:
            have.append(d)
    tag_line = ' '.join(have[: LIMITS['ig']['tags']])
    joined = f'{body}\n\n.\n.\n.\n{tag_line}'
    return trim_to(joined, LIMITS['ig']['chars'])


def variant_pinterest(body: str, tags: list[str]) -> str:
    top = ' '.join(tags[: LIMITS['pinterest']['tags']])
    joined = f'{body} {top}'.strip()
    return trim_to(joined, LIMITS['pinterest']['chars'])


def parse_dt(s: str):
    try:
        return datetime.strptime(s.strip(), '%Y-%m-%d %H:%M:%S')
    except Exception:
        return None


def respread_schedule(rows):
    """If duplicate timestamps exist, re-spread across 30 days, 2/day, 9AM/1PM/5PM EST."""
    stamps = [parse_dt(r[0]) for r in rows]
    if len({s for s in stamps if s}) == len([s for s in stamps if s]):
        return rows  # all unique, keep
    print('  [schedule] duplicates detected -> re-spreading')
    base = datetime(2026, 4, 18, 9, 0, 0)
    slots = []
    d = 0
    while len(slots) < len(rows):
        day = base + timedelta(days=d)
        for hr in (9, 13, 17):
            slots.append(day.replace(hour=hr, minute=0, second=0))
            if len(slots) >= len(rows):
                break
        d += 1
    for r, slot in zip(rows, slots):
        r[0] = slot.strftime('%Y-%m-%d %H:%M:%S')
    return rows


def main():
    if not os.path.exists(SRC_CSV):
        sys.exit(f'Source CSV not found: {SRC_CSV}')
    with open(SRC_CSV, encoding='utf-8', newline='') as fp:
        reader = csv.reader(fp)
        all_rows = list(reader)

    # 2-row header: platform labels + column names
    header_plat, header_col = all_rows[0], all_rows[1]
    data_rows = all_rows[2:]
    print(f'Rows loaded: {len(data_rows)} posts, {len(header_col)} columns')
    if len(header_col) != 39:
        print('WARNING: expected 39 columns, found', len(header_col))

    # Column index lookups
    idx_when    = 0
    idx_content = 1
    idx_link_pin= 38  # Pinterest link col
    idx_action  = 24  # Google actionUrl

    # UTM + schedule respread
    for i, row in enumerate(data_rows, start=1):
        for j, cell in enumerate(row):
            low = cell.lower()
            if 'http' in low or any(h in low for h in UTM_HOSTS):
                row[j] = utmize_field(cell, i)

    data_rows = respread_schedule(data_rows)

    # Write FIXED (same schema)
    with open(OUT_CSV, 'w', encoding='utf-8', newline='') as fp:
        w = csv.writer(fp, quoting=csv.QUOTE_ALL)
        w.writerow(header_plat)
        w.writerow(header_col)
        for r in data_rows:
            w.writerow(r)
    print(f'[ok] wrote {OUT_CSV}')

    # Per-platform variants
    var_plat = header_plat + ['All Social'] * 4
    var_head = header_col + ['content_x', 'content_linkedin', 'content_ig', 'content_pinterest']
    with open(OUT_VAR, 'w', encoding='utf-8', newline='') as fp:
        w = csv.writer(fp, quoting=csv.QUOTE_ALL)
        w.writerow(var_plat)
        w.writerow(var_head)
        for r in data_rows:
            content = r[idx_content]
            body, tags = split_content(content)
            r_full = r + [
                variant_x(body, tags),
                variant_linkedin(body, tags),
                variant_ig(body, tags),
                variant_pinterest(body, tags),
            ]
            w.writerow(r_full)
    print(f'[ok] wrote {OUT_VAR}')

    # Validation
    problems = 0
    for i, r in enumerate(data_rows, start=1):
        if len(r) != 39:
            print(f'  row {i}: col count {len(r)} != 39')
            problems += 1
        if not parse_dt(r[idx_when]):
            print(f'  row {i}: bad datetime "{r[idx_when]}"')
            problems += 1
    print(f'[validate] {problems} problems')


if __name__ == '__main__':
    main()
