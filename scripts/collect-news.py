#!/usr/bin/env python3
"""Live Tech News Collector — stdlib only (no pip dependencies).
Fetches RSS feeds, classifies topics, scores importance, and writes data/live-news.json.
"""

import hashlib
import json
import os
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# ── Config ──────────────────────────────────────────────────────────────────

BDT = timezone(timedelta(hours=6))

FEEDS = [
    ("TechCrunch", "https://techcrunch.com/feed/", "crunch"),
    ("TheVerge", "https://www.theverge.com/rss/index.xml", "verge"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index", "ars"),
    ("Hacker News", "https://hnrss.org/frontpage", "hn"),
    ("BBC", "https://feeds.bbci.co.uk/news/technology/rss.xml", "bbc"),
    ("Wired", "https://www.wired.com/feed/rss", "wired"),
]

SOURCE_WEIGHT = {
    "TechCrunch": 3, "TheVerge": 3, "Ars Technica": 4,
    "BBC": 4, "Wired": 3, "Hacker News": 2,
}
RELIABILITY = {
    "TechCrunch": 4, "TheVerge": 4, "Ars Technica": 5,
    "BBC": 5, "Wired": 4, "Hacker News": 3,
}

# ── Topic Classification ────────────────────────────────────────────────────

TOPIC_KEYWORDS = {
    "AI/ML": [
        "ai", "artificial intelligence", "gpt", "llm", "machine learning",
        "neural", "deeplearn", "deep learning", "deepmind", "openai",
        "gemini", "claude", "qwen", "copilot", "chatbot", "diffusion",
        "transformer", "stable diffusion", "midjourney", "generative",
        "tensorflow", "pytorch", "hugging face", "anthropic", "mistral",
        "llama", "open source model", "foundation model", "multimodal",
        "ai model", "language model", "vision model", "reinforcement learning",
        "nlp", "natural language", "computer vision", "autonomous",
        "self-driving", "tesla bot", "robot", "robotics", "agi",
    ],
    "Security": [
        "hack", "vulnerability", "breach", "ransomware", "malware",
        "phishing", "cyber", "security", "zero-day", "exploit",
        "cve", "encryption", "firewall", "patch", "bug bounty",
        "data leak", "privacy", "gdpr", "surveillance", "spyware",
        "backdoor", "trojan", "ddos", "penetration", "threat",
    ],
    "Cloud/DevOps": [
        "cloud", "aws", "azure", "gcp", "kubernetes", "k8s", "docker",
        "devops", "terraform", "serverless", "lambda", "s3",
        "container", "microservice", "ci/cd", "github actions",
        "jenkins", "ansible", "puppet", "infrastructure",
        "orchestration", "deployment", "scaling", "load balancer",
        "cdn", "edge computing", "paas", "saas",
    ],
    "Mobile": [
        "iphone", "ios", "android", "ipad", "samsung", "pixel",
        "mobile", "smartphone", "app store", "play store",
        "huawei", "xiaomi", "oneplus", "oppo", "vivo",
        "foldable", "5g", "6g", "wireless charging",
    ],
    "Web/JavaScript": [
        "javascript", "typescript", "react", "vue", "angular", "svelte",
        "node.js", "nodejs", "next.js", "nuxt", "deno", "bun",
        "web", "html", "css", "tailwind", "webpack", "vite",
        "npm", "yarn", "frontend", "backend", "api", "rest",
        "graphql", "webassembly", "wasm", "browser", "chromium",
        "firefox", "safari", "web standard",
    ],
    "Hardware": [
        "chip", "processor", "cpu", "gpu", "nvidia", "amd", "intel",
        "apple silicon", "m1", "m2", "m3", "m4", "macbook",
        "laptop", "desktop", "pc", "motherboard", "ram",
        "ssd", "hard drive", "display", "monitor", "vr headset",
        "ar headset", "meta quest", "vision pro", "apple watch",
        "wearable", "hardware", "semiconductor", "fabrication",
        "qualcomm", "arm", "risc-v",
    ],
    "Startups": [
        "startup", "funding", "series a", "series b", "seed round",
        "venture", "ipo", "acquisition", "acquires", "acquired",
        "unicorn", "valuation", "investor", "fundraising",
        "y combinator", "yc", "incubator", "accelerator",
    ],
    "Open Source": [
        "open source", "open-source", "opensource", "linux", "github",
        "gitlab", "mozilla", "apache", "free software", "gpl",
        "mit license", "contribution", "contributor", "repository",
        "fork", "pull request", "community", "wordpress", "blender",
    ],
    "Regulation": [
        "regulation", "regulate", "law", "lawsuit", "court", "antitrust",
        "fda", "fcc", "ftc", "eu", "congress", "legislation",
        "compliance", "ban", "banned", "policy", "government",
        "doj", "investigation", "fine", "settlement", "monopoly",
        "copyright", "patent", "trademark", "trade commission",
    ],
}

TOPIC_ICON = {
    "AI/ML": "\U0001f916", "Security": "\U0001f512", "Cloud/DevOps": "\u2601\ufe0f",
    "Mobile": "\U0001f4f1", "Web/JavaScript": "\U0001f310", "Hardware": "\U0001f4bb",
    "Startups": "\U0001f680", "Open Source": "\U0001f513", "Regulation": "\u2696\ufe0f",
    "Other": "\U0001f4f0",
}

IMPORTANCE_KEYWORDS = {
    "launch": 2, "released": 2, "hack": 3, "vulnerability": 3,
    "ceo": 1, "billion": 2, "open source": 1, "acqui": 2,
    "shut down": 3, "bankrupt": 3, "record": 1, "breakthrough": 2,
    "disclose": 2, "outage": 2, "data breach": 3,
}

OUTPUT_PATH = "data/live-news.json"
MAX_ITEMS = 50
TIMEOUT = 15
HOURS_CUTOFF = 24


def _ssl_context():
    """Create SSL context; fall back to unverified if certs missing."""
    try:
        ctx = ssl.create_default_context()
        # Quick check if certs exist
        ctx.load_verify_locations(cafile=ssl.get_default_verify_paths().openssl_cafile)
        return ctx
    except (ssl.SSLError, OSError, FileNotFoundError, TypeError):
        print("[WARN] No system CA certs found; using unverified SSL (ok for CI)")
        return ssl._create_unverified_context()


_SSL_CTX = _ssl_context()


def fetch_feed(url, timeout=TIMEOUT):
    """Fetch RSS XML, return parsed ElementTree root or None."""
    req = urllib.request.Request(url, headers={"User-Agent": "TechNewsBot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return ET.fromstring(resp.read())
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None


def parse_rss(root):
    """Parse RSS 2.0 items. Also handle Atom feeds."""
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        desc = (item.findtext("description") or "").strip()
        desc = re.sub(r"<[^>]+>", " ", desc).strip()
        desc = re.sub(r"\s+", " ", desc)
        if title and link:
            items.append({"title": title, "link": link, "pubDate": pub_date, "description": desc})
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            pub_date = (entry.findtext("atom:published", namespaces=ns) or
                        entry.findtext("atom:updated", namespaces=ns) or "").strip()
            desc_raw = (entry.findtext("atom:summary", namespaces=ns) or
                        entry.findtext("atom:content", namespaces=ns) or "").strip()
            desc = re.sub(r"<[^>]+>", " ", desc_raw).strip()
            desc = re.sub(r"\s+", " ", desc)
            if title and link:
                items.append({"title": title, "link": link, "pubDate": pub_date, "description": desc})
    return items


def parse_date(datestr):
    """Parse various date formats to UTC datetime."""
    if not datestr:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(datestr, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def classify_topic(title, description):
    """Return best-matching topic based on keyword count."""
    text = (title + " " + description).lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[topic] = score
    if not scores:
        return "Other"
    return max(scores, key=scores.get)


def calc_importance(title, description, source):
    """Calculate 0-10 importance score."""
    text = (title + " " + description).lower()
    score = SOURCE_WEIGHT.get(source, 2)
    for kw, bonus in IMPORTANCE_KEYWORDS.items():
        if kw in text:
            score += bonus
    if len(title) > 60:
        score += 1
    return min(score, 10)


def make_id(url):
    return hashlib.sha256(url.encode()).hexdigest()[:12]


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    output_path = os.path.join(repo_root, OUTPUT_PATH)

    all_items = []
    seen_urls = set()
    any_success = False

    for source_name, feed_url, source_icon in FEEDS:
        print(f"[*] Fetching {source_name}...")
        root = fetch_feed(feed_url)
        if root is None:
            continue
        any_success = True
        items = parse_rss(root)
        count = 0
        for item in items:
            url = item["link"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            dt = parse_date(item["pubDate"])
            if dt is None:
                continue
            now = datetime.now(timezone.utc)
            age = now - dt
            if age.total_seconds() > HOURS_CUTOFF * 3600:
                continue
            topic = classify_topic(item["title"], item["description"])
            importance = calc_importance(item["title"], item["description"], source_name)
            reliability = RELIABILITY.get(source_name, 3)
            summary_en = item["description"][:120]
            if len(item["description"]) > 120:
                summary_en += "..."
            all_items.append({
                "id": make_id(url),
                "title": item["title"],
                "link": url,
                "source": source_name,
                "sourceIcon": source_icon,
                "pubDate": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "description": item["description"],
                "topic": topic,
                "topicIcon": TOPIC_ICON.get(topic, "\U0001f4f0"),
                "importance": importance,
                "reliability": reliability,
                "summary_bn": "",
                "summary_en": summary_en,
            })
            count += 1
        print(f"    -> {count} items (total unique so far: {len(all_items)})")

    if not any_success:
        print("[WARN] All feeds failed. Preserving existing data.")
        return

    all_items.sort(key=lambda x: (-x["importance"], x["pubDate"]))
    all_items = all_items[:MAX_ITEMS]

    now_bdt = datetime.now(BDT)
    output = {
        "lastUpdated": now_bdt.strftime("%Y-%m-%dT%H:%M:%S+06:00"),
        "news": all_items,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Wrote {len(all_items)} items to {output_path}")
    print(f"     lastUpdated: {output['lastUpdated']}")


if __name__ == "__main__":
    main()
