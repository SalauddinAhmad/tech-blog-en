#!/usr/bin/env python3
"""Auto-publish daily blog posts from live-news.json — English version."""

import json, os, subprocess
from datetime import datetime, timezone, timedelta

BDT = timezone(timedelta(hours=6))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(REPO_ROOT, "data", "live-news.json")
CONTENT_DIR = os.path.join(REPO_ROOT, "content", "posts")
IMAGES_DIR = os.path.join(REPO_ROOT, "static", "images")
TODAY = datetime.now(BDT).strftime("%Y-%m-%d")
MONTHS = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

CATEGORY_MAP = {
    "AI/ML": ("ai-ml", "AI / ML", "🤖"), "Security": ("security", "Security", "🔒"),
    "Cloud/DevOps": ("cloud-devops", "Cloud / DevOps", "☁️"), "Mobile": ("mobile", "Mobile", "📱"),
    "Web/JavaScript": ("web-javascript", "Web / JS", "🌐"), "Hardware": ("hardware", "Hardware", "💻"),
    "Startups": ("startups", "Startups", "🚀"), "Open Source": ("open-source", "Open Source", "🔓"),
    "Regulation": ("regulation", "Regulation", "⚖️"), "Other": ("other", "Other", "📰"),
}

def en_date():
    d = datetime.now(BDT)
    return f"{MONTHS[d.month]} {d.day}, {d.year}"

def generate_cover(category, title, out_path):
    script = os.path.join(REPO_ROOT, "tools", "generate-cover.py")
    cat_slug, cat_en, cat_icon = CATEGORY_MAP.get(category, ("other", "Other", "📰"))
    cmd = ["python3", script, "--title", f"{cat_icon} {title}", "--category", cat_slug,
           "--lang", "en", "--date", en_date(), "--out", out_path, "--style", "template"]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  Cover: {out_path}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (1200, 630))
        draw = ImageDraw.Draw(img)
        for y in range(630):
            draw.line([(0,y),(1200,y)], fill=(20,0,50, int(20*y/630), 0, 0))
        draw.rectangle([(0,0),(1200,8)], fill=(184,0,0))
        draw.rectangle([(0,590),(1200,630)], fill=(184,0,0))
        img.save(out_path, "PNG")

def build_content(cat_en, cat_icon, items):
    lines = [f"# {cat_icon} {cat_en} — Today's Tech News", "", f"*{en_date()} — Auto-curated*", "", "---", ""]
    for i, item in enumerate(items[:10], 1):
        lines.append(f"## {i}. {item.get('title','')}")
        lines.append(f"**Source:** [{item.get('source','')}]({item.get('link','')})")
        summary = item.get("summary_en","") or item.get("description","")[:120]
        lines.append(f"{summary}"); lines.append("---"); lines.append("")
    lines.append(f"*{en_date()} • Tech Intelligence EN • Auto-curated report*")
    return "\n".join(lines)

def main():
    if not os.path.exists(DATA_PATH): print("No data"); return
    with open(DATA_PATH) as f: data = json.load(f)
    items = data.get("news", [])
    if not items: print("No news"); return
    print(f"Auto-publishing for {en_date()}...")
    topics = {}
    for item in items: topics.setdefault(item.get("topic","Other"), []).append(item)
    for topic, titems in topics.items():
        cat_slug, cat_en, cat_icon = CATEGORY_MAP.get(topic, ("other", "Other", "📰"))
        post_dir = os.path.join(CONTENT_DIR, cat_slug, f"daily-{cat_slug}-{TODAY}")
        if os.path.exists(post_dir): continue
        os.makedirs(post_dir, exist_ok=True)
        generate_cover(topic, cat_en, os.path.join(IMAGES_DIR, f"cover-{cat_slug}-{TODAY}.png"))
        content = build_content(cat_en, cat_icon, titems)
        with open(os.path.join(post_dir, "index.md"), "w") as f:
            f.write(f'---\ntitle: "{cat_en} — {en_date()}"\ndate: {TODAY}T10:00:00+06:00\ndraft: false\nslug: "daily-{cat_slug}-{TODAY}"\ncategories: ["{cat_slug}"]\ntags: ["ai", "technology", "daily-report", "seo"]\ncover:\n  image: "/images/cover-{cat_slug}-{TODAY}.png"\n  alt: "{cat_en} — {en_date()}"\n---\n\n{content}\n')
        print(f"  {cat_slug} done")
    # Digest
    digest_dir = os.path.join(CONTENT_DIR, "tech-intelligence", f"daily-tech-intelligence-{TODAY}")
    if not os.path.exists(digest_dir):
        os.makedirs(digest_dir, exist_ok=True)
        generate_cover("AI/ML", f"Tech Intelligence — {en_date()}", os.path.join(IMAGES_DIR, f"cover-tech-intelligence-{TODAY}.png"))
        top = sorted(items, key=lambda x: x.get("importance",0), reverse=True)[:15]
        content = build_content("Tech Intelligence", "🤖", top)
        with open(os.path.join(digest_dir, "index.md"), "w") as f:
            f.write(f'---\ntitle: "Tech Intelligence — {en_date()}"\ndate: {TODAY}T10:00:00+06:00\ndraft: false\nslug: "daily-tech-intelligence-{TODAY}"\ncategories: ["tech-intelligence"]\ntags: ["ai", "technology", "daily-report", "seo", "digest"]\ncover:\n  image: "/images/cover-tech-intelligence-{TODAY}.png"\n  alt: "Tech Intelligence — {en_date()}"\n---\n\n{content}\n')
        print("  digest done")
    print("Done!")

if __name__ == "__main__": main()
