#!/usr/bin/env python3
"""Auto-publish daily blog posts from live-news.json — English version."""

import json, os
from datetime import datetime, timezone, timedelta

BDT = timezone(timedelta(hours=6))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(REPO_ROOT, "data", "live-news.json")
CONTENT_DIR = os.path.join(REPO_ROOT, "content", "posts")
IMAGES_DIR = os.path.join(REPO_ROOT, "static", "images")
TODAY = datetime.now(BDT).strftime("%Y-%m-%d")

MONTHS = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

CATEGORY_MAP = {
    "AI/ML": ("ai-ml", "AI / ML", "🤖"),
    "Security": ("security", "Security", "🔒"),
    "Cloud/DevOps": ("cloud-devops", "Cloud / DevOps", "☁️"),
    "Mobile": ("mobile", "Mobile", "📱"),
    "Web/JavaScript": ("web-javascript", "Web / JS", "🌐"),
    "Hardware": ("hardware", "Hardware", "💻"),
    "Startups": ("startups", "Startups", "🚀"),
    "Open Source": ("open-source", "Open Source", "🔓"),
    "Regulation": ("regulation", "Regulation", "⚖️"),
    "Other": ("other", "Other", "📰"),
}

def en_date():
    d = datetime.now(BDT)
    return f"{MONTHS[d.month]} {d.day}, {d.year}"

def generate_cover(category, title, out_path):
    from PIL import Image, ImageDraw
    W, H = 1200, 630
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradients = {
        "AI/ML": ((20, 0, 50), (0, 0, 0)), "Security": ((0, 30, 0), (0, 0, 0)),
        "Cloud/DevOps": ((0, 0, 40), (0, 0, 0)), "Mobile": ((40, 0, 40), (0, 0, 0)),
        "Web/JavaScript": ((0, 20, 40), (0, 0, 0)), "Hardware": ((30, 30, 0), (0, 0, 0)),
        "Startups": ((40, 10, 0), (0, 0, 0)), "Open Source": ((0, 30, 30), (0, 0, 0)),
        "Regulation": ((30, 0, 10), (0, 0, 0)), "Other": ((20, 20, 20), (0, 0, 0)),
    }
    top, bot = gradients.get(category, ((20, 20, 20), (0, 0, 0)))
    for y in range(H):
        r = int(top[0] + (bot[0] - top[0]) * y / H)
        g = int(top[1] + (bot[1] - top[1]) * y / H)
        b = int(top[2] + (bot[2] - top[2]) * y / H)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    draw.rectangle([(0, 0), (W, 8)], fill=(184, 0, 0))
    cat_slug, cat_en, cat_icon = CATEGORY_MAP.get(category, ("other", "Other", "📰"))
    try:
        font = ImageFont = None  # Use default
    except: pass
    draw.text((40, 30), f"{cat_icon}  Tech Intelligence EN", fill=(184, 0, 0))
    draw.text((40, 200), title[:30], fill=(255, 255, 255))
    draw.text((40, 280), f"Date: {en_date()}", fill=(180, 180, 180))
    draw.rectangle([(0, H-40), (W, H)], fill=(184, 0, 0))
    draw.text((40, H-32), "salauddinahmad.github.io/tech-blog-en", fill=(255, 255, 255))
    img.save(out_path, "PNG")

def build_content(cat_en, cat_icon, items):
    lines = [f"# {cat_icon} {cat_en} — Today's Tech News", "", f"*{en_date()} — Auto-curated*", "", "---", ""]
    for i, item in enumerate(items[:10], 1):
        lines.append(f"## {i}. {item.get('title','')}")
        lines.append(f"**Source:** [{item.get('source','')}]({item.get('link','')})")
        summary = item.get("summary_en","") or item.get("description","")[:120]
        lines.append(f"{summary}")
        lines.append("---")
        lines.append("")
    lines.append(f"*{en_date()} • Tech Intelligence EN • Auto-curated report*")
    return "\n".join(lines)

def main():
    if not os.path.exists(DATA_PATH):
        print("No live-news.json"); return
    with open(DATA_PATH) as f: data = json.load(f)
    items = data.get("news", [])
    if not items: print("No news"); return
    print(f"Auto-publishing for {en_date()}...")
    topics = {}
    for item in items:
        t = item.get("topic","Other")
        topics.setdefault(t, []).append(item)
    any_created = False
    for topic, titems in topics.items():
        cat_slug, cat_en, cat_icon = CATEGORY_MAP.get(topic, ("other", "Other", "📰"))
        post_dir = os.path.join(CONTENT_DIR, cat_slug, f"daily-{cat_slug}-{TODAY}")
        if os.path.exists(post_dir): continue
        os.makedirs(post_dir, exist_ok=True)
        cover = os.path.join(IMAGES_DIR, f"cover-{cat_slug}-{TODAY}.png")
        generate_cover(topic, cat_en, cover)
        content = build_content(cat_en, cat_icon, titems)
        with open(os.path.join(post_dir, "index.md"), "w") as f:
            f.write(f"""---
title: "{cat_en} — {en_date()}"
date: {TODAY}T10:00:00+06:00
draft: false
slug: "daily-{cat_slug}-{TODAY}"
categories: ["{cat_slug}"]
tags: ["ai", "technology", "daily-report", "seo"]
description: "{cat_en} daily report — {en_date()}"
summary: "{cat_en} — {en_date()} auto-curated tech news."
cover:
  image: "/images/cover-{cat_slug}-{TODAY}.png"
  alt: "{cat_en} — {en_date()}"
---

{content}
""")
        print(f"  {cat_slug} done"); any_created = True
    # Digest
    digest_dir = os.path.join(CONTENT_DIR, "tech-intelligence", f"daily-tech-intelligence-{TODAY}")
    if not os.path.exists(digest_dir):
        os.makedirs(digest_dir, exist_ok=True)
        cover = os.path.join(IMAGES_DIR, f"cover-tech-intelligence-{TODAY}.png")
        generate_cover("AI/ML", f"Tech Intelligence — {en_date()}", cover)
        top = sorted(items, key=lambda x: x.get("importance",0), reverse=True)[:15]
        content = build_content("Tech Intelligence", "🤖", top)
        with open(os.path.join(digest_dir, "index.md"), "w") as f:
            f.write(f"""---
title: "Tech Intelligence — {en_date()}"
date: {TODAY}T10:00:00+06:00
draft: false
slug: "daily-tech-intelligence-{TODAY}"
categories: ["tech-intelligence"]
tags: ["ai", "technology", "daily-report", "seo", "digest"]
description: "Daily Tech Intelligence digest — {en_date()}"
summary: "Tech Intelligence — {en_date()} auto-curated digest."
cover:
  image: "/images/cover-tech-intelligence-{TODAY}.png"
  alt: "Tech Intelligence — {en_date()}"
---

{content}
""")
        print("  digest done")
    print("Done!")

if __name__ == "__main__": main()
