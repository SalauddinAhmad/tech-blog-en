# 🇬🇧 Tech Intelligence English — Blog Site (all in English)

**Daily reports → English cover images → English blog posts → GitHub Pages auto-deploy**

🎨 Modern creative professional design (PaperMod + custom CSS) • Mobile-first • SEO-ready

---

## 🌐 Two separate blog sites

| Site | Language | Repo | URL |
|---|---|---|---|
| **Tech Intelligence English** | 🇬🇧 English (everything in English) | `tech-blog-en` | https://salauddinahmad.github.io/tech-blog-en/ |
| **Tech Intelligence বাংলা** | 🇧🇩 Bengali (everything in Bengali) | `tech-blog` | https://salauddinahmad.github.io/tech-blog/ |

Not mixed — **two completely separate sites**, each with its own design and content.

---

## 📁 Structure (English site)

```
tech-blog-en/
├── config.toml                  # English site config + SEO
├── auto-publish.sh              # report → cover + post → git push
├── tools/generate-cover.py      # English cover generator (--lang en)
├── assets/css/extended/custom.css  # 🎨 Creative design (purple/blue theme)
├── .github/workflows/deploy.yml # GitHub Actions
├── content/posts/<category>/<slug>/index.md
├── static/images/               # English cover images
└── (reads ../tech-blog/latest-report-en.md)
```

---

## ⚡ Setup — 3 steps

1. **Create GitHub repo:** `tech-blog-en` (Public)
   - Settings → Pages → Source: **GitHub Actions**
   - Settings → Actions → Workflow permissions: **Read and write**
2. **Push:**
   ```bash
   cd /Users/salaudinahmad/Documents/A/Agent_Work/Agent_Autometion/tech-blog-en
   git init && git add . && git commit -m "🚀 EN blog" && git branch -M main
   git remote add origin https://github.com/SalauddinAhmad/tech-blog-en.git && git push -u origin main
   ```
3. **Test:**
   ```bash
   ./auto-publish.sh --dry-run
   ```

The 10:15 AM cron auto-publishes to both sites daily. 🎉

---

## 🔍 SEO (auto Google)

- SEO-friendly slug URLs: `/posts/daily-tech-intelligence-2026-08-12/`
- sitemap.xml (daily) + robots.txt — auto
- canonical + Open Graph + JSON-LD
- Unique meta description per post
- Mobile-first — Google ranking bonus

---

*Powered by Flux 🧞*
