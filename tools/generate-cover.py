#!/Users/salaudinahmad/.venvs/pillow-raqm/bin/python
"""
🎨 Blog Cover Image Generator v2 — AI Style
Usage:
  python3 generate-cover.py --title "..." --category tech-intelligence --date "১২ আগস্ট ২০২৬" --out /path/cover.png [--style ai|template] [--fresh-bg]

--style ai (default): Seedream AI background (free) + text overlay
--style template: old gradient background
AI backgrounds cached in static/images/ai-bg/ — reuse unless --fresh-bg
"""
import argparse, os, ssl, time, json, hashlib, urllib.request, urllib.error
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
FONTS = {
    "bn": "tools/fonts/HindSiliguri-Regular.ttf",
    "en": "/System/Library/Fonts/HelveticaNeue.ttc",
}
FONTS_BOLD = {
    "bn": "tools/fonts/HindSiliguri-Bold.ttf",
    "en": "/System/Library/Fonts/HelveticaNeue.ttc",
}
FONTS_SEMI = {
    "bn": "tools/fonts/HindSiliguri-SemiBold.ttf",
    "en": "/System/Library/Fonts/HelveticaNeue.ttc",
}
DEFAULT_LANG = "bn"

# ── Seedream API (free, AutoGLM) ──
SD_APP_ID = "100003"
SD_APP_KEY = "38d2391985e2369a5fb8227d8e6cd5e5"
SD_URL = "https://autoglm-api.autoglm.ai/agentdr/v1/assistant/skills/generate-image-seedream"
TOKEN_URL = "http://127.0.0.1:18432/get_token"

# AI background prompts per category (no text — we overlay it ourselves)
AI_PROMPTS = {
    "tech-intelligence": {
        "bn": "Abstract futuristic technology banner background, dark navy and emerald green, glowing circuit board traces, soft bokeh light particles, depth of field, premium minimal design, wide composition, no text, no letters",
        "en": "Abstract futuristic technology banner background, dark indigo and violet, glowing circuit board traces, soft bokeh light particles, depth of field, premium minimal design, wide composition, no text, no letters",
    },
    "adaptability": {
        "bn": "Abstract growth and adaptability banner background, dark teal and emerald green, organic flowing fluid shapes, soft light particles, elegant premium minimal, wide composition, no text, no letters",
        "en": "Abstract growth and adaptability banner background, dark indigo and violet, organic flowing fluid shapes, soft light particles, elegant premium minimal, wide composition, no text, no letters",
    },
    "prayer-times": {
        "bn": "Elegant Islamic abstract banner background, deep green and gold, soft crescent moon glow, stars and light particles, peaceful premium minimal, wide composition, no text, no letters",
        "en": "Elegant Islamic abstract banner background, deep indigo and gold, soft crescent moon glow, stars and light particles, peaceful premium minimal, wide composition, no text, no letters",
    },
    "default": {
        "bn": "Abstract premium banner background, dark navy and teal, smooth gradients, soft light particles, minimal elegant, wide composition, no text, no letters",
        "en": "Abstract premium banner background, dark indigo and violet, smooth gradients, soft light particles, minimal elegant, wide composition, no text, no letters",
    },
}

THEMES = {
    "tech-intelligence": {"bg": [(10, 30, 60), (0, 120, 90)], "accent": (0, 200, 150),
                          "badge": {"bn": "🤖 টেক ইন্টেলিজেন্স", "en": "🤖 TECH INTELLIGENCE"}},
    "adaptability":      {"bg": [(40, 10, 60), (120, 40, 120)], "accent": (200, 120, 255),
                          "badge": {"bn": "🧠 অ্যাডাপ্টাবিলিটি", "en": "🧠 ADAPTABILITY"}},
    "prayer-times":      {"bg": [(10, 50, 40), (0, 100, 80)], "accent": (80, 220, 180),
                          "badge": {"bn": "🕌 নামাজের সময়", "en": "🕌 PRAYER TIMES"}},
    "default":           {"bg": [(20, 20, 40), (0, 100, 150)], "accent": (100, 200, 255),
                          "badge": {"bn": "📰 ব্লগ পোস্ট", "en": "📰 BLOG POST"}},
}

_ctx = None
def ssl_ctx():
    global _ctx
    if _ctx is None:
        _ctx = ssl.create_default_context()
        _ctx.check_hostname = False
        _ctx.verify_mode = ssl.CERT_NONE
    return _ctx

def seedream_bg(prompt, cache_path):
    """Generate AI background via Seedream. Returns local cached path."""
    if cache_path and os.path.exists(cache_path):
        print(f"♻️  AI background cached: {cache_path}")
        return cache_path
    with urllib.request.urlopen(TOKEN_URL) as r:
        token = r.read().decode().strip()
    if not token.lower().startswith("bearer "):
        token = f"Bearer {token}"
    ts = str(int(time.time()))
    sign = hashlib.md5(f"{SD_APP_ID}&{ts}&{SD_APP_KEY}".encode()).hexdigest()
    headers = {"Authorization": token, "Content-Type": "application/json",
               "X-Auth-Appid": SD_APP_ID, "X-Auth-TimeStamp": ts, "X-Auth-Sign": sign}
    req = urllib.request.Request(SD_URL, data=json.dumps({"query": prompt}).encode(),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ssl_ctx(), timeout=180) as resp:
            res = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Seedream HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")
    if res.get("code") != 0:
        raise RuntimeError(f"Seedream error: {res}")
    url = res["data"]["image_url"]
    print(f"🎨 AI background generated ({len(url)} chars url)")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with urllib.request.urlopen(url, context=ssl_ctx(), timeout=180) as r:
        data = r.read()
    with open(cache_path, "wb") as f:
        f.write(data)
    print(f"💾 AI background saved: {cache_path}")
    return cache_path

def crop_to_banner(path):
    """Center-crop any image to 1200x630."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    target = W / H
    if w / h > target:
        nw = int(h * target)
        x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:
        nh = int(w / target)
        y = (h - nh) // 2
        im = im.crop((0, y, w, y + nh))
    return im.resize((W, H), Image.LANCZOS)

def draw_overlay(img, theme, title, lang, date, ai_mode=True):
    """Draw badge + title + date on the background."""
    d = ImageDraw.Draw(img, "RGBA")
    LANG = lang
    fnt = lambda s, w="r": ImageFont.truetype(
        {"b": FONTS_BOLD, "s": FONTS_SEMI}.get(w, FONTS).get(LANG, FONTS[DEFAULT_LANG]), s)

    # Readability darkening (stronger for AI art)
    alpha = 120 if ai_mode else 0
    if alpha:
        dark = Image.new("RGBA", (W, H), (5, 8, 20, alpha))
        img = Image.alpha_composite(img.convert("RGBA"), dark)
        d = ImageDraw.Draw(img, "RGBA")
        # bottom-up gradient for text zone
        for y in range(H // 2, H):
            t = (y - H // 2) / (H / 2)
            a = int(90 * t)
            if a:
                d.line([(0, y), (W, y)], fill=(0, 0, 0, a))

    # Category badge
    badge_fnt = fnt(34, "s")
    badge_text = theme["badge"].get(LANG, theme["badge"]["bn"])
    btw = d.textlength(badge_text, font=badge_fnt)
    bx0, by0, bx1, by1 = 60, 56, 60 + btw + 48, 56 + 58
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=29, fill=(255,255,255,26), outline=theme["accent"], width=2)
    d.text((bx0 + 24, by0 + 10), badge_text, font=badge_fnt, fill=theme["accent"])

    # Title (wrapped, centered)
    def wrap(text, max_w, fnt_):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=fnt_) <= max_w: cur = t
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        return lines

    title_fnt = fnt(72, "b")
    lines = wrap(title, W - 160, title_fnt)[:3]
    line_h = 100
    total_h = len(lines) * line_h
    y0 = (H - total_h) // 2 + 20
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=title_fnt)
        d.text(((W - tw) / 2, y0 + i * line_h), ln, font=title_fnt, fill=(255, 255, 255, 240))

    # Accent line
    d.rounded_rectangle([(W-220)//2, y0 + total_h + 30, (W+220)//2, y0 + total_h + 38], radius=4, fill=theme["accent"])

    # Date + brand
    small_fnt = fnt(32)
    brand = "Tech Intelligence বাংলা 🇧🇩" if LANG == "bn" else "Tech Intelligence English 🇬🇧"
    bottom = f"{date}   •   {brand}" if date else brand
    tw = d.textlength(bottom, font=small_fnt)
    d.text(((W - tw) / 2, H - 100), bottom, font=small_fnt, fill=(255, 255, 255, 180))
    return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--category", default="default")
    ap.add_argument("--lang", default="bn", choices=["bn", "en"])
    ap.add_argument("--date", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--style", default="ai", choices=["ai", "template"])
    ap.add_argument("--fresh-bg", action="store_true", help="regenerate AI background (ignore cache)")
    ap.add_argument("--bg-cache", default="", help="dir to cache AI backgrounds")
    args = ap.parse_args()

    theme = THEMES.get(args.category, THEMES["default"])

    if args.style == "ai":
        cache = ""
        if args.bg_cache:
            cache = os.path.join(args.bg_cache, f"{args.category}-{args.lang}.jpg")
            if args.fresh_bg and os.path.exists(cache):
                os.remove(cache)
        prompt = AI_PROMPTS.get(args.category, AI_PROMPTS["default"]).get(args.lang, AI_PROMPTS["default"]["bn"])
        bg = seedream_bg(prompt, cache)
        img = crop_to_banner(bg)
        img = draw_overlay(img, theme, args.title, args.lang, args.date, ai_mode=True)
    else:
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        c1, c2 = theme["bg"]
        for y in range(H):
            t = y / H
            d.line([(0, y), (W, y)], fill=(int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t)))
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([W-260, -140, W+100, 220], fill=(255,255,255,14))
        od.ellipse([-120, H-180, 160, H+120], fill=(255,255,255,10))
        od.ellipse([W-420, H-260, W-160, H+10], fill=(0,0,0,26))
        img = Image.alpha_composite(img.convert("RGBA"), overlay)
        img = draw_overlay(img, theme, args.title, args.lang, args.date, ai_mode=False)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    img.convert("RGB").save(args.out, "PNG", optimize=True)
    print(f"✅ Cover saved: {args.out} ({os.path.getsize(args.out)//1024} KB)")

if __name__ == "__main__":
    main()
