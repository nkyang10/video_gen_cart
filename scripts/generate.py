#!/usr/bin/env python3
"""
Video Gen Cart — Markdown → 靜態網站 generator
讀取 data/brands/<brand>/ 入面嘅 brand.md + <character>.md，
生成 docs/ 靜態網站（brand → character 兩層瀏覽）。
"""
import re, sys, html, json
from pathlib import Path
import markdown
import frontmatter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "brands"
OUT = ROOT / "docs"

# ---------- Design tokens (casual-professional editorial) ----------
CSS = """\
:root {
  --paper: #f7f4ef;
  --ink: #2b2b28;
  --muted: #6b6a63;
  --forest: #3e5c4b;
  --terracotta: #c05f3c;
  --border: #e2dcd0;
  --card: #ffffff;
  --tag-bg: #efe9dd;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC",
               "PingFang TC", "Microsoft JhengHei", sans-serif;
  background: var(--paper);
  color: var(--ink);
  line-height: 1.7;
  padding-bottom: 60px;
}
.wrap { max-width: 960px; margin: 0 auto; padding: 0 22px; }
header.site {
  border-bottom: 1px solid var(--border);
  padding: 26px 0 18px;
  margin-bottom: 30px;
  background: #fffdf9;
}
header.site .wrap { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
header.site h1 { font-size: 1.5rem; letter-spacing: 0.02em; }
header.site h1 a { color: var(--ink); text-decoration: none; }
header.site h1 span { color: var(--terracotta); }
header.site .sub { color: var(--muted); font-size: 0.85rem; }
nav.brand-tabs { display: flex; gap: 8px; flex-wrap: wrap; margin: 18px 0 6px; }
nav.brand-tabs a {
  padding: 6px 14px; border-radius: 8px; border: 1px solid var(--border);
  background: #fff; color: var(--ink); text-decoration: none; font-size: 0.9rem;
}
nav.brand-tabs a:hover { border-color: var(--forest); }
nav.brand-tabs a.active { background: var(--forest); color: #fff; border-color: var(--forest); }
.breadcrumb { color: var(--muted); font-size: 0.85rem; margin-bottom: 14px; }
.breadcrumb a { color: var(--forest); text-decoration: none; }
h1.page { font-family: "Noto Serif TC", Georgia, serif; font-size: 1.9rem; margin-bottom: 6px; }
h2 { font-family: "Noto Serif TC", Georgia, serif; color: var(--forest);
     font-size: 1.25rem; margin: 34px 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
h3 { color: var(--ink); font-size: 1.05rem; margin: 20px 0 8px; }
p { margin: 8px 0; }
ul, ol { margin: 8px 0 8px 24px; }
li { margin: 4px 0; }
blockquote { border-left: 3px solid var(--terracotta); background: #fffdf9;
             padding: 8px 14px; margin: 10px 0; color: var(--ink); border-radius: 0 6px 6px 0; }
a { color: var(--forest); }
.meta-table { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 0.92rem; }
.meta-table td { padding: 7px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
.meta-table td:first-child { width: 34%; color: var(--muted); font-weight: 600; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
.badge.pd { background: #dcebdd; color: #2c5e3a; }
.badge.cc { background: #dfe7f5; color: #2c4a7c; }
.badge.partial { background: #f5e8d3; color: #8a5a1e; }
.badge.verify { background: #f4dcd9; color: #963a2e; }
.lic-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.character-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; margin-top: 18px; }
.character-card {
  background: var(--card); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px; text-decoration: none; color: var(--ink); display: block;
  transition: transform .12s ease, box-shadow .12s ease;
}
.character-card:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.07); border-color: var(--forest); }
.character-card .name { font-family: "Noto Serif TC", Georgia, serif; font-weight: 700; font-size: 1.05rem; }
.character-card .thumb { width: 100%; height: 120px; overflow: hidden; border-radius: 8px; margin-bottom: 10px; background: #eee7db; }
.character-card .thumb img { width: 100%; height: 100%; object-fit: cover; }
.character-card .zh { color: var(--muted); font-size: 0.85rem; margin-left: 6px; }
.character-card .desc { color: var(--muted); font-size: 0.85rem; margin-top: 6px; }
.character-card .badge { margin-top: 10px; }
.copyright-box { background: #f2efea; border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; margin: 18px 0; }
.copyright-box h3 { color: var(--terracotta); margin-top: 0; font-size: 0.95rem; text-transform: uppercase; letter-spacing: .04em; }
.copyright-box ul { margin-left: 20px; }
.char-hero { display: flex; gap: 22px; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; }
.char-hero img { width: 280px; max-width: 100%; height: auto; border-radius: 10px; border: 1px solid var(--border); background:#fff; }
.char-hero .captions { flex: 1; min-width: 220px; font-size: 0.85rem; color: var(--muted); }
.char-hero .captions p { margin: 4px 0; }
.img-credit { font-size: 0.75rem; color: var(--muted); margin-top: 6px; line-height: 1.5; }
.img-credit a { color: var(--forest); }
.footer-note { color: var(--muted); font-size: 0.8rem; margin-top: 50px; padding-top: 16px; border-top: 1px solid var(--border); }
.hero { background: #fffdf9; border: 1px solid var(--border); border-radius: 12px; padding: 26px; margin-bottom: 28px; }
.hero h2 { border: none; margin-top: 0; font-size: 1.5rem; }
.hero p { color: var(--muted); max-width: 70ch; }
.stat-row { display: flex; gap: 22px; flex-wrap: wrap; margin-top: 14px; }
.stat { font-size: 0.9rem; }
.stat b { color: var(--forest); font-size: 1.2rem; }
/* 配角 / 路人互動面板 */
.support-panel { margin-top: 22px; display: grid; gap: 10px; }
.support-item { background: var(--card); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.support-item summary {
  cursor: pointer; padding: 13px 18px; list-style: none; display: flex; align-items: center; gap: 12px;
  font-weight: 600; color: var(--ink); transition: background .12s ease; user-select: none;
}
.support-item summary::-webkit-details-marker { display: none; }
.support-item summary:hover { background: #f3efe6; }
.support-item summary .caret { color: var(--terracotta); transition: transform .18s ease; margin-left: auto; }
.support-item[open] summary .caret { transform: rotate(90deg); }
.support-item summary .sup-name { font-family: "Noto Serif TC", Georgia, serif; font-size: 1.05rem; }
.support-item summary .sup-type { font-size: .72rem; color: var(--forest); background: var(--tag-bg); padding: 2px 10px; border-radius: 20px; font-weight: 600; }
.support-item summary .sup-zh { color: var(--muted); font-size: .85rem; font-weight: 400; }
.support-body { padding: 4px 18px 16px; border-top: 1px solid var(--tag-bg); }
.support-body .sup-relation { margin: 10px 0 4px; color: var(--forest); font-size: .88rem; font-weight: 600; }
.support-body p, .support-body ul { font-size: .92rem; margin: 6px 0; }
.support-body .sup-label { color: var(--terracotta); font-weight: 700; font-size: .8rem; letter-spacing: .03em; margin-top: 10px; text-transform: uppercase; }
.support-body blockquote { font-size: .9rem; }
.support-hint { color: var(--muted); font-size: .85rem; margin-top: 6px; }
/* 參考圖庫（動畫用多角度） */
.gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-top: 18px; }
.gallery figure { background: var(--card); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin: 0; }
.gallery figure img { width: 100%; height: 170px; object-fit: cover; display: block; background: #fff; }
.gallery figcaption { padding: 8px 12px; font-size: .82rem; color: var(--ink); }
.gallery figcaption .g-angle { font-weight: 700; color: var(--forest); }
.gallery figcaption .g-meta { color: var(--muted); font-size: .72rem; margin-top: 3px; }
.gallery-hint { color: var(--muted); font-size: .85rem; margin-top: 8px; }
"""

PAGE_FOOT = f"""\
<div class="wrap">
  <div class="footer-note">
    Video Gen Cart — 公版卡通素材庫。本網站資料只供參考，唔係法律意見；使用前請自行核實你所在地嘅版權 / 商標法例。
  </div>
</div>
"""

MD = markdown.Markdown(extensions=["tables", "fenced_code", "nl2br"])

# 圖片 manifest（fetch_images.py 生成）
IMAGES = {}
_manifest_path = ROOT / "docs" / "assets" / "image_manifest.json"
if _manifest_path.exists():
    import json as _json
    IMAGES = _json.loads(_manifest_path.read_text(encoding="utf-8"))

# 參考圖庫 manifest（fetch_gallery.py 生成）— slug -> [ {file, angle, scene, license, ...} ]
GALLERY = {}
_gallery_path = ROOT / "docs" / "assets" / "gallery_manifest.json"
if _gallery_path.exists():
    import json as _json
    GALLERY = _json.loads(_gallery_path.read_text(encoding="utf-8"))

def strip_leading_h1(text):
    """移除內容檔最頂嘅 '#' 標題（因為頁面標題已顯示品牌/角色名）。"""
    lines = (text or "").splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].lstrip().startswith("# "):
        lines.pop(0)
    return "\n".join(lines)

def pd_badge(status):
    if isinstance(status, bool):
        return '<span class="badge pd">✔ 公版</span>' if status else '<span class="badge verify">❌ 非公版</span>'
    s = (status or "").lower()
    if "公版" in s or "pd" in s or "yes" in s:
        return '<span class="badge pd">✔ 公版</span>'
    if "部分" in s or "partial" in s:
        return '<span class="badge partial">⚠ 部分公版</span>'
    return '<span class="badge verify">❓ 需核實</span>'

def license_badge(cm):
    """顯示具體授權碼：公版 / CC0 / CC-BY / CC-BY-SA。"""
    if cm.get("license_type") == "cc":
        lic = str(cm.get("license", "") or "")
        # 抽授權碼（e.g. 'CC-BY 4.0' → 'CC-BY'，'CC0 1.0' → 'CC0'）
        code = lic.split()[0] if lic else "CC"
        return f'<span class="badge cc">{html.escape(code)}</span>'
    if cm.get("public_domain"):
        return '<span class="badge pd">✔ 公版</span>'
    return '<span class="badge verify">❓ 需核實</span>'

def _license_code(cm):
    """抽角色嘅授權碼（供品牌聚合用）：'公版' / 'CC0' / 'CC-BY' / 'CC-BY-SA'。"""
    if cm.get("license_type") == "cc":
        lic = str(cm.get("license", "") or "")
        return lic.split()[0] if lic else "CC"
    if cm.get("public_domain"):
        return "公版"
    return "需核實"

def brand_license_badges(b):
    """聚合品牌旗下所有角色出現過嘅授權碼（去重），顯示晒出嚟。"""
    seen, out = [], []
    for c in characters.get(b["slug"], []):
        code = _license_code(c)
        if code and code not in seen:
            seen.append(code)
            if code == "公版":
                out.append('<span class="badge pd">✔ 公版</span>')
            elif code in ("CC0", "CC-BY", "CC-BY-SA", "CC", "CC-BY-ND", "CC-BY-NC"):
                out.append(f'<span class="badge cc">{html.escape(code)}</span>')
            else:
                out.append('<span class="badge verify">❓ 需核實</span>')
    return " ".join(out)

def render_md(text):
    MD.reset()
    return MD.convert(text or "")

def header(title, active_brand=None, page_zh="", jsonld=None, prefix=""):
    """統一導航 header。prefix 係由當前頁面到 site root 嘅相對路徑：
    根頁 = ''（空），品牌/角色頁 = '../../'。所有連結經 prefix 保證正確。"""
    brand_links = []
    for brand in sorted(brands.values(), key=lambda b: b["name"].lower()):
        cls = "active" if active_brand and brand["slug"] == active_brand else ""
        brand_links.append(f'<a href="{prefix}brands/{brand["slug"]}/" class="{cls}">{html.escape(brand["name"])}</a>')
    nav = f'<nav class="brand-tabs">{"".join(brand_links)}</nav>'
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — Video Gen Cart</title>
{ld}<style>{CSS}</style></head><body>
<header class="site"><div class="wrap">
  <h1><a href="{prefix}index.html">Video Gen Cart <span>自由創作卡通素材庫</span></a></h1>
  <div class="sub">公版 / 自由使用卡通人物 · AI 創意素材</div>
</div>{nav}</header>
"""

def page_brand_index(brand):
    """品牌頁：列出旗下角色。"""
    slug = brand["slug"]
    chars = characters.get(slug, [])
    body = [f'<div class="wrap"><div class="breadcrumb"><a href="../../index.html">全部品牌</a> › {html.escape(brand["name"])}</div>']
    body.append(f'<h1 class="page">{html.escape(brand["name"])} <span style="color:var(--muted);font-size:1rem;font-weight:400">{html.escape(brand.get("brand_zh",""))}</span></h1>')
    body.append('<table class="meta-table">')
    for label, key in [("出品", "country"), ("年代", "era"), ("原創作者", "creator"), ("原發行商", "original_publisher"),
                       ("首次登場", "first_appearance_year"), ("類型", "type")]:
        v = brand.get(key)
        if v: body.append(f'<tr><td>{label}</td><td>{html.escape(str(v))}</td></tr>')
    body.append(f'<tr><td>版權狀態</td><td>{brand_license_badges(brand)} {html.escape(str(brand.get("status","")))}</td></tr>')
    body.append('</table>')
    body.append(render_md(strip_leading_h1(brand["content"])))
    # character grid
    body.append(f'<h2>旗下公版角色 <span style="font-size:.85rem;color:var(--muted);font-weight:400">({len(chars)})</span></h2>')
    if chars:
        body.append('<div class="character-grid">')
        for c in chars:
            thumb = IMAGES.get(c["slug"], {}).get("file") or IMAGES.get(slug, {}).get("file")
            thumb_html = f'<div class="thumb"><img src="../../assets/img/{html.escape(thumb)}" alt=""></div>' if thumb else ''
            body.append(f'''<a class="character-card" href="{c["slug"]}.html">
              {thumb_html}
              <div><span class="name">{html.escape(c["name"])}</span><span class="zh">{html.escape(c.get("character_zh",""))}</span></div>
              <div class="desc">{html.escape(c.get("role",""))}</div>
              {license_badge(c)}
            </a>''')
        body.append('</div>')
    else:
        body.append('<p style="color:var(--muted)">暫未有角色記錄。</p>')
    # 配角 / 路人互動參考面板
    sup = brand.get("supporting", [])
    if sup:
        body.append(f'<h2>配角 / 路人 <span style="font-size:.85rem;color:var(--muted);font-weight:400">({len(sup)}) — 點擊展開互動參考</span></h2>')
        body.append('<div class="support-panel">')
        for s in sup:
            body.append('<details class="support-item">')
            body.append(f'''<summary>
              <span class="caret">▶</span>
              <span class="sup-name">{html.escape(s.get("name",""))}</span>
              <span class="sup-zh">{html.escape(s.get("name_zh",""))}</span>
              <span class="sup-type">{html.escape(s.get("type","配角"))}</span>
            </summary>''')
            body.append('<div class="support-body">')
            if s.get("relation"): body.append(f'<div class="sup-relation">🤝 {html.escape(s.get("relation",""))}</div>')
            if s.get("interaction"): body.append(f'<div class="sup-label">互動參考</div>{render_md(s["interaction"])}')
            if s.get("dialogue"): body.append(f'<div class="sup-label">互動對白</div><blockquote>{html.escape(s.get("dialogue",""))}</blockquote>')
            if s.get("scene"): body.append(f'<div class="sup-label">互動場景</div>{render_md(s["scene"])}')
            body.append('</div>')
            body.append('</details>')
        body.append('</div>')
        body.append('<div class="support-hint">💡 互動參考 = 呢個配角/路人同主角嘅相處方式、互動對白同經典情境，方便你喺 AI 創作時保持角色關係一致。</div>')
    body.append('</div>')
    return "".join(body)

def page_character(brand, c):
    slug = c["slug"]
    body = [f'<div class="wrap"><div class="breadcrumb"><a href="../../index.html">全部品牌</a> › <a href="index.html">{html.escape(brand["name"])}</a> › {html.escape(c["name"])}</div>']
    body.append(f'<h1 class="page">{html.escape(c["name"])} <span style="color:var(--muted);font-size:1rem;font-weight:400">{html.escape(c.get("character_zh",""))}</span></h1>')
    # 角色圖片 + 來源
    # 角色頁面圖像：先睇角色 slug，冇就 fallback 到品牌 slug
    img = IMAGES.get(slug) or IMAGES.get(brand["slug"])
    if img:
        body.append(f'''<div class="char-hero"><img src="../../assets/img/{html.escape(img["file"])}" alt="{html.escape(c["name"])}">
        <div class="captions">
          <p><b>{html.escape(img["title"].replace("File:",""))}</b></p>
          <p>License: <b>{html.escape(img["license"])}</b>{"（公版 ✔）" if img.get("pd") else "（⚠ 需核實）"}</p>
          {f'<p>Artist: {html.escape(img.get("artist",""))}</p>' if img.get("artist") else ""}
          <div class="img-credit">來源：<a href="{html.escape(img.get("source_url",""))}">Wikimedia Commons</a>
          {f' · <a href="{html.escape(img.get("license_url",""))}">License 詳情</a>' if img.get("license_url") else ""}</div>
        </div></div>''')
    body.append('</div>')
    # copyright box
    body.append('<div class="wrap"><div class="copyright-box"><h3>⚖️ 版權狀態</h3><ul>')
    lic_type = c.get("license_type", "pd" if c.get("public_domain") else "unknown")
    if lic_type == "cc":
        body.append(f'<li><b>授權</b>：✔️ 自由授權（{html.escape(str(c.get("license", "CC")))}）— 可自由使用，需遵守授權條款</li>')
    else:
        body.append(f'<li><b>公版</b>：{"✔️ 屬公版" if c.get("public_domain") else "❌ 唔屬公版"}（管轄區：{html.escape(str(c.get("public_domain_jurisdiction","US")))}）</li>')
    if c.get("public_domain_version"): body.append(f'<li><b>公版版本</b>：{html.escape(str(c["public_domain_version"]))}</li>')
    if c.get("protected_portion"): body.append(f'<li><b>受保護部分</b>：{html.escape(str(c["protected_portion"]))}</li>')
    if c.get("trademark"): body.append(f'<li><b>Trademark</b>：{html.escape(str(c["trademark"]))}</li>')
    if c.get("verified"): body.append(f'<li><b>核實日期</b>：{html.escape(str(c["verified"]))}</li>')
    body.append('</ul></div></div>')
    # 參考圖庫（動畫用多角度）
    gallery_items = GALLERY.get(c.get("slug")) or GALLERY.get(brand["slug"]) or []
    if gallery_items:
        body.append('<div class="wrap">')
        body.append(f'<h2>參考圖庫 <span style="font-size:.85rem;color:var(--muted);font-weight:400">({len(gallery_items)} 張，動畫參考用)</span></h2>')
        body.append('<div class="gallery">')
        for g in gallery_items:
            lic = html.escape(g.get("license",""))
            src = "Wikimedia" if g.get("source")=="commons" else "Openverse"
            body.append(f'''<figure>
              <img src="../../assets/gallery/{html.escape(g.get("file",""))}" alt="{html.escape(g.get("title",""))}" loading="lazy">
              <figcaption>
                <span class="g-angle">{html.escape(g.get("angle","") or g.get("scene",""))}</span> · {html.escape(g.get("scene",""))}
                <div class="g-meta">🪪 {lic} · 來源 {src}</div>
              </figcaption>
            </figure>''')
        body.append('</div>')
        body.append('<div class="gallery-hint">💡 參考圖庫 = 角色嘅多角度/多場景參考圖，方便你喺 AI 動畫製作時保持造型一致。</div>')
        body.append('</div>')
    body.append('<div class="wrap">' + render_md(strip_leading_h1(c["content"])) + '</div>')
    return "".join(body)

# ---------- Build ----------

def _license_field(cm):
    """統一 license 顯示（PD vs CC）。"""
    if cm.get("license_type") == "cc":
        return {"type": "CC", "code": cm.get("license", "CC")}
    status = str(cm.get("status", "") or "")
    if cm.get("public_domain"):
        return {"type": "PD", "code": "public-domain"}
    if "公版" in status or "PD" in status.upper() or "自由授權" in status or "CC0" in status:
        return {"type": "PD", "code": "public-domain"}
    return {"type": "UNKNOWN", "code": ""}

def emit_catalog_json():
    """輸出 /api/catalog.json — AI agent 一撳 load 全量結構化資料（video generation 基礎）。"""
    catalog = {
        "meta": {
            "name": "Video Gen Cart",
            "description": "公版 / 自由使用卡通人物素材庫，供 AI agent 做 video generation 基礎。",
            "brand_count": len(brands),
            "character_count": sum(len(v) for v in characters.values()),
            "generated": "2026-08-09",
            "schema_version": "1.0",
        },
        "brands": [],
    }
    for b in sorted(brands.values(), key=lambda x: x["name"].lower()):
        bc = characters.get(b["slug"], [])
        brand_entry = {
            "slug": b["slug"],
            "name": b.get("name"),
            "name_zh": b.get("brand_zh", ""),
            "type": b.get("type", ""),
            "country": b.get("country", ""),
            "era": b.get("era", ""),
            "creator": b.get("creator", ""),
            "publisher": b.get("original_publisher", ""),
            "first_appearance_year": b.get("first_appearance_year"),
            "status": b.get("status", ""),
            "license": _license_field(b),
            "characters": [],
        }
        # 配角 / 路人互動參考
        if b.get("supporting"):
            brand_entry["supporting_characters"] = [
                {"name": s.get("name"), "name_zh": s.get("name_zh", ""), "type": s.get("type", ""),
                 "relation": s.get("relation", ""), "interaction": s.get("interaction", "")}
                for s in b["supporting"]
            ]
        for c in bc:
            gallery = GALLERY.get(c.get("slug")) or GALLERY.get(b["slug"]) or []
            main_img = IMAGES.get(c.get("slug")) or IMAGES.get(b["slug"])
            char_entry = {
                "slug": c.get("slug"),
                "name": c.get("name"),
                "name_zh": c.get("character_zh", ""),
                "role": c.get("role", ""),
                "first_appearance": c.get("first_appearance", ""),
                "creator": c.get("creator", ""),
                "license": _license_field(c),
                "protected_portion": c.get("protected_portion", ""),
                "trademark": c.get("trademark", ""),
                "verified": c.get("verified", ""),
                "image": f"assets/img/{main_img['file']}" if main_img and main_img.get("file") else None,
                "reference_gallery": [
                    {"file": f"assets/gallery/{g['file']}", "angle": g.get("angle", ""),
                     "scene": g.get("scene", ""), "license": g.get("license", ""),
                     "source": g.get("source_url", "")}
                    for g in gallery if g.get("file")
                ],
                # video-generation 專用欄位
                "appearance": _extract_section(c, "外觀描述"),
                "dialogue": _extract_quote(c),
                "scene": _extract_section(c, "場景"),
                "personality": _extract_section(c, "性格"),
                "ai_usage": _extract_section(c, "AI 創意用法"),
            }
            brand_entry["characters"].append(char_entry)
        catalog["brands"].append(brand_entry)
    api_dir = OUT / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✦ catalog.json → docs/api/catalog.json ({len(brands)} brands / {sum(len(v) for v in characters.values())} characters)")

def _extract_section(cm, heading):
    """由角色 markdown content 抽指定 section 嘅純文字（畀 AI parse）。"""
    text = cm.get("content", "") or ""
    lines = text.splitlines()
    out, on = [], False
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("#") and heading in stripped:
            on = True; continue
        if on and stripped.startswith("#"):
            break
        if on and stripped and not stripped.startswith(("**", ">", "```")):
            out.append(stripped.lstrip("- "))
    return " ".join(out).strip()[:600]

def _extract_quote(cm):
    """抽角色對白（blockquote）。"""
    text = cm.get("content", "") or ""
    m = re.search(r">\s*([^\n]+)", text)
    return m.group(1).strip() if m else ""

def load():
    global brands, characters
    brands, characters = {}, {}
    for bdir in sorted(DATA.iterdir()):
        if not bdir.is_dir(): continue
        bfile = bdir / "brand.md"
        if not bfile.exists(): continue
        post = frontmatter.load(bfile)
        meta = dict(post.metadata)
        meta["slug"] = bdir.name
        meta["name"] = meta.get("name") or meta.get("brand", bdir.name)
        meta["content"] = post.content
        # 配角 / 路人互動參考（optional supporting.md）
        sfile = bdir / "supporting.md"
        if sfile.exists():
            spost = frontmatter.load(sfile)
            smeta = dict(spost.metadata)
            meta["supporting"] = smeta.get("supporting", [])
        brands[meta["slug"]] = meta
        chars = []
        for cfile in sorted(bdir.glob("*.md")):
            if cfile.name in ("brand.md", "supporting.md"): continue
            cpost = frontmatter.load(cfile)
            cm = dict(cpost.metadata)
            cm["slug"] = cfile.stem
            cm["name"] = cm.get("name") or cm.get("character", cfile.stem)
            cm["content"] = cpost.content
            cm["brand"] = meta["slug"]
            chars.append(cm)
        characters[meta["slug"]] = chars

def build():
    load()
    OUT.mkdir(parents=True, exist_ok=True)
    # index
    idx = [header("全部品牌")]
    idx.append('<div class="wrap"><div class="hero"><h2>自由創作卡通素材庫</h2>')
    idx.append('<p>收集網上現屬公版 / 自由使用、過去受歡迎嘅卡通人物同素材，方便自由創作者攞嚟做 AI 創意。以「劇集品牌 → 角色」分類，每項齊備圖片、場景、文字、性格、對話等素材。</p>')
    total_chars = sum(len(v) for v in characters.values())
    idx.append(f'<div class="stat-row"><div class="stat"><b>{len(brands)}</b> 個品牌</div><div class="stat"><b>{total_chars}</b> 個角色</div></div>')
    idx.append('</div>')
    idx.append('<h2 style="margin-left:22px">全部品牌</h2>')
    idx.append('<div class="wrap"><div class="character-grid">')
    for b in sorted(brands.values(), key=lambda x: x["name"].lower()):
        n = len(characters.get(b["slug"], []))
        idx.append(f'<a class="character-card" href="brands/{b["slug"]}/index.html">'
                   f'<div><span class="name">{html.escape(b["name"])}</span><span class="zh">{html.escape(b.get("brand_zh",""))}</span></div>'
                   f'<div class="desc">{html.escape(b.get("era",""))} · {n} 個角色</div>'
                   f'<div class="lic-row">{brand_license_badges(b)}</div></a>')
    idx.append('</div></div>')
    idx.append(PAGE_FOOT)
    (OUT / "index.html").write_text("".join(idx), encoding="utf-8")
    # brand pages
    for slug, b in brands.items():
        bdir = OUT / "brands" / slug
        bdir.mkdir(parents=True, exist_ok=True)
        htmlout = header(f'{b["name"]}', active_brand=slug, prefix="../../") + page_brand_index(b) + PAGE_FOOT
        (bdir / "index.html").write_text(htmlout, encoding="utf-8")
        for c in characters.get(slug, []):
            ld = {
                "@context": "https://schema.org",
                "@type": "CreativeWork",
                "name": c.get("name"),
                "alternateName": c.get("character_zh", ""),
                "description": f"角色資料：{c.get('role','')}。出處 {c.get('first_appearance','')}。授權 {c.get('license', '')}",
                "keywords": c.get("role", "") + ", " + c.get("brand", ""),
            }
            main_img = IMAGES.get(c.get("slug")) or IMAGES.get(b["slug"])
            if main_img and main_img.get("file"):
                ld["image"] = f"../../assets/img/{main_img['file']}"
            (bdir / f'{c["slug"]}.html').write_text(
                header(f'{c["name"]}', active_brand=slug, jsonld=ld, prefix="../../")
                + page_character(b, c) + PAGE_FOOT, encoding="utf-8")
    (OUT / ".nojekyll").touch()
    (OUT / "assets").mkdir(exist_ok=True)
    emit_catalog_json()
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    print(f"✅ Generated {len(brands)} brands, {sum(len(v) for v in characters.values())} characters → {OUT}")

if __name__ == "__main__":
    build()
