#!/bin/bash
# Rebuild 10 batch7 videos from v2 finals:
#   - Per-video outro trim (kills CTA/brand wall — varies per render timeline)
#   - Trim first 0.3s dead-air
#   - drawbox black-mask top 110px (kills "SHORT-FORM REEL" header + "01/08" counter)
#   - Add 0.3s kick drum SFX (60Hz sine decay) at t=0.05 over existing bgm-v3 audio
#   - Audio duck first 0.4s to make room for kick
#   - Loudness normalize -16 LUFS
#
# Source: social-media-assets/videos-v2/tier1/final/<name>_final.mp4
# Output: skynetjoe-batch7-content/videos/<NN>-<hook>.mp4

set -euo pipefail
SRC="/c/Users/info/OneDrive/Desktop/GITHUB/social-media-assets/videos-v2/tier1/final"
OUT="/c/Users/info/OneDrive/Desktop/GITHUB/skynetjoe-batch7-content/videos"
TMP="/c/Users/info/OneDrive/Desktop/GITHUB/skynetjoe-batch7-content/videos/_tmp"
mkdir -p "$TMP"

# Mapping: v2-source | batch7-name | outro-trim-seconds (probed per video)
declare -a MAP=(
  "100_percent_ai_code|01-replaced-5k-developer|7"
  "saas_idea_worthless|02-saas-idea-worthless|19"
  "five_apps_this_week|03-build-saas-in-48-hours|9"
  "claude_vs_cursor|04-claude-vs-cursor|11"
  "stop_writing_code|05-stop-writing-code|6"
  "vibe_coding_no_bs|06-vibe-coding-no-bs|9"
  "zero_dollar_stack|07-zero-dollar-tech-stack|9"
  "gohighlevel_97|08-gohighlevel-97-month|9"
  "audit_your_stack|09-audit-your-tech-stack|14"
  "junior_devs_not_dead|10-junior-devs-not-dead|12"
)

# Pre-generate kick drum SFX (60Hz sine, 0.3s decay, mono->stereo)
KICK="$TMP/kick.wav"
ffmpeg -y -f lavfi -i "sine=frequency=60:duration=0.3,volume='exp(-t*8)':eval=frame,aformat=channel_layouts=stereo" \
  -ac 2 -ar 44100 "$KICK" 2>/dev/null
echo "kick SFX generated: $(ls -lh "$KICK" | awk '{print $5}')"

OK=0; FAIL=0
TRIM_START=0.3
for ENTRY in "${MAP[@]}"; do
  IFS='|' read -r SRC_NAME DST_NAME OUTRO_TRIM <<< "$ENTRY"
  SRC_FILE="$SRC/${SRC_NAME}_final.mp4"
  DST_FILE="$OUT/${DST_NAME}.mp4"

  if [ ! -f "$SRC_FILE" ]; then
    echo "MISSING: $SRC_FILE"
    FAIL=$((FAIL+1))
    continue
  fi

  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SRC_FILE")
  ACTUAL_DUR=$(awk "BEGIN { printf \"%.2f\", $DUR - $OUTRO_TRIM - $TRIM_START }")
  echo
  echo "--- $DST_NAME"
  echo "    src: $SRC_NAME (${DUR}s)  outro-trim: ${OUTRO_TRIM}s  ->  output ${ACTUAL_DUR}s"

  ffmpeg -y -i "$SRC_FILE" -i "$KICK" -filter_complex "
    [0:v]trim=start=${TRIM_START}:duration=${ACTUAL_DUR},setpts=PTS-STARTPTS,
      drawbox=x=0:y=0:w=1080:h=110:color=black:t=fill
    [v];
    [0:a]atrim=start=${TRIM_START}:duration=${ACTUAL_DUR},asetpts=PTS-STARTPTS,
      volume='if(lt(t,0.4),0.55+(t/0.4)*0.45,1.0)':eval=frame
    [aducked];
    [1:a]adelay=50|50,apad=whole_dur=${ACTUAL_DUR},volume=1.3
    [akick];
    [aducked][akick]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,
      loudnorm=I=-16:TP=-1:LRA=11
    [a]
  " -map "[v]" -map "[a]" \
    -c:v libx264 -preset medium -crf 24 -pix_fmt yuv420p -r 30 \
    -c:a aac -b:a 128k -ac 2 \
    -movflags +faststart \
    "$DST_FILE" 2>"$TMP/ff_${DST_NAME}.log"

  if [ -f "$DST_FILE" ] && [ -s "$DST_FILE" ]; then
    SZ=$(ls -lh "$DST_FILE" | awk '{print $5}')
    echo "    OK -> $SZ"
    OK=$((OK+1))
  else
    echo "    FAIL — see $TMP/ff_${DST_NAME}.log"
    FAIL=$((FAIL+1))
  fi
done

echo
echo "============================================"
echo " DONE — ok: $OK / fail: $FAIL"
echo "============================================"
