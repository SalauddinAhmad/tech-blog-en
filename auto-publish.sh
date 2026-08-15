#!/bin/bash
# ═══════════════════════════════════════════════════
# 🇬🇧 Tech Intelligence English — Auto-Publish
# রিপোর্ট (English) → কভার + পোস্ট → GitHub
# ═══════════════════════════════════════════════════
set -e

BLOG_DIR="/Users/salaudinahmad/Documents/A/Agent_Work/Agent_Autometion/tech-blog-en"
TOOLS_DIR="$BLOG_DIR/tools"
TODAY=$(date +%Y-%m-%d)
TODAY_EN=$(date '+%d %B %Y')
DRY_RUN=false
[ "$1" = "--dry-run" ] && DRY_RUN=true && shift
REPORT_FILE="${1:-/Users/salaudinahmad/Documents/A/Agent_Work/Agent_Autometion/tech-blog/latest-report-en.md}"

echo "📝 EN Auto-publishing for $TODAY_EN..."

extract_en() { sed -n "/$2/,/^## /p" "$1" | sed '$d' | sed '/^---$/d'; }

create_post() {
    local CATEGORY="$1" TITLE="$2" CONTENT="$3" SLUG="$4"
    /Users/salaudinahmad/.venvs/pillow-raqm/bin/python "$TOOLS_DIR/generate-cover.py" --title "$TITLE" --category "$CATEGORY" --lang en \
        --date "$TODAY_EN" --out "$BLOG_DIR/static/images/cover-${CATEGORY}-${TODAY}.png" --bg-cache "$BLOG_DIR/static/images/ai-bg" || true
    # AUDIT FX-04: WebP/AVIF pipeline — PNG stays the base; the cover partial
    # (<picture>) serves webp + responsive 768w/480w variants. Tools optional:
    #   brew install webp libavif   (or: sudo apt-get install -y webp libavif-bin)
    COVER_PNG="$BLOG_DIR/static/images/cover-${CATEGORY}-${TODAY}.png"
    if command -v cwebp >/dev/null 2>&1 && [ -f "$COVER_PNG" ]; then
        cwebp -q 80 "$COVER_PNG" -o "${COVER_PNG%.png}.webp" >/dev/null 2>&1 || true
        cwebp -q 80 -resize 768 403 "$COVER_PNG" -o "${COVER_PNG%.png}-768w.webp" >/dev/null 2>&1 || true
        cwebp -q 80 -resize 480 252 "$COVER_PNG" -o "${COVER_PNG%.png}-480w.webp" >/dev/null 2>&1 || true
    else
        echo "⚠️  cwebp not found — webp variants skipped (brew install webp)"
    fi
    if command -v avifenc >/dev/null 2>&1 && [ -f "$COVER_PNG" ]; then
        avifenc -q 40 -s 4 "$COVER_PNG" -o "${COVER_PNG%.png}.avif" >/dev/null 2>&1 || true
    fi
    mkdir -p "$BLOG_DIR/content/posts/${CATEGORY}/${SLUG}"
    cat > "$BLOG_DIR/content/posts/${CATEGORY}/${SLUG}/index.md" << MDEOF
---
title: "${TITLE}"
date: ${TODAY}T10:00:00+06:00
draft: false
slug: "${SLUG}"
categories: ["${CATEGORY}"]
tags: ["ai", "technology", "english", "daily-report", "seo"]
description: "${TITLE}"
summary: "${TITLE} — Auto-generated daily report with cover image."
cover:
  image: "/images/cover-${CATEGORY}-${TODAY}.png"
  alt: "${TITLE}"
---

${CONTENT}

---
*📅 ${TODAY_EN} • Tech Intelligence English*
MDEOF
    echo "✅ EN ${CATEGORY}: /${SLUG}/"
}

found=false
if [ -f "$REPORT_FILE" ]; then
    C=$(extract_en "$REPORT_FILE" 'Tech Intelligence')
    if [ -n "$C" ]; then
        create_post "tech-intelligence" "Daily Tech Intelligence — ${TODAY_EN}" "$C" "daily-tech-intelligence-${TODAY}"
        found=true
    fi
    C=$(extract_en "$REPORT_FILE" 'Adaptability')
    if [ -n "$C" ]; then
        create_post "adaptability" "Daily Adaptability Intelligence — ${TODAY_EN}" "$C" "daily-adaptability-intelligence-${TODAY}"
        found=true
    fi
    C=$(extract_en "$REPORT_FILE" 'Prayer Times')
    if [ -n "$C" ]; then
        create_post "prayer-times" "Today's Prayer Times — ${TODAY_EN}" "$C" "prayer-times-${TODAY}"
        found=true
    fi
fi

[ "$found" = "false" ] && echo "⚠️  No EN report found" && exit 1
echo "📊 EN posts generated!"

if [ "$DRY_RUN" = "true" ]; then echo "🔍 Dry-run — push skipped."; exit 0; fi

cd "$BLOG_DIR"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "⚠️  Not a git repo. Instructions in README."
    exit 1
fi
git add content/ static/images/
if git diff --cached --quiet; then
    echo "No changes."
else
    git commit -m "📝 EN Auto-post: ${TODAY}"
    git push origin main && echo "🚀 EN Pushed — deploy running!"
fi
