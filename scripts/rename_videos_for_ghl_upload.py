"""Rename 10 batch7 videos to NN-hook.mp4 format + update CSV placeholders.

After run:
- videos/01-replaced-5k-developer.mp4 (etc.)
- CSV placeholder [UPLOAD_TO_GHL]<old>.mp4 -> [UPLOAD_TO_GHL]<new>.mp4
"""
import csv, sys, shutil
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

VIDEOS_DIR = Path("C:/Users/info/OneDrive/Desktop/GITHUB/skynetjoe-batch7-content/videos")
CSV_PATH = Path("C:/Users/info/OneDrive/Desktop/GITHUB/ghl-batch7-content-engine.FINAL.csv")

RENAMES = [
    ("100_percent_ai_code.mp4",  "01-replaced-5k-developer.mp4"),
    ("saas_idea_worthless.mp4",  "02-saas-idea-worthless.mp4"),
    ("five_apps_this_week.mp4",  "03-build-saas-in-48-hours.mp4"),
    ("claude_vs_cursor.mp4",     "04-claude-vs-cursor.mp4"),
    ("stop_writing_code.mp4",    "05-stop-writing-code.mp4"),
    ("vibe_coding_no_bs.mp4",    "06-vibe-coding-no-bs.mp4"),
    ("zero_dollar_stack.mp4",    "07-zero-dollar-tech-stack.mp4"),
    ("gohighlevel_97.mp4",       "08-gohighlevel-97-month.mp4"),
    ("audit_your_stack.mp4",     "09-audit-your-tech-stack.mp4"),
    ("junior_devs_not_dead.mp4", "10-junior-devs-not-dead.mp4"),
]

# Rename files
renamed = 0
for old, new in RENAMES:
    src = VIDEOS_DIR / old
    dst = VIDEOS_DIR / new
    if dst.exists():
        print(f"  SKIP (already renamed): {new}")
        continue
    if not src.exists():
        print(f"  MISSING source: {old}")
        continue
    src.rename(dst)
    print(f"  {old}  ->  {new}")
    renamed += 1

print(f"\n{renamed}/10 files renamed.\n")

# Update CSV placeholders
with CSV_PATH.open(encoding="utf-8", newline="") as f:
    rows = list(csv.reader(f))
hdr = rows[1]
cols = {n: i for i, n in enumerate(hdr)}
c_video = cols["videoUrls (comma-separated)"]
swapped = 0
for r in rows[2:]:
    if len(r) <= c_video: continue
    v = r[c_video]
    for old, new in RENAMES:
        token_old = f"[UPLOAD_TO_GHL]{old}"
        token_new = f"[UPLOAD_TO_GHL]{new}"
        if token_old in v:
            r[c_video] = v.replace(token_old, token_new)
            swapped += 1
            break

with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
    csv.writer(f, quoting=csv.QUOTE_ALL).writerows(rows)
print(f"{swapped}/10 CSV placeholders updated.")
