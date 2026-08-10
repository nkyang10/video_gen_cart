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
try:
    from PIL import Image as _PILImage
    _HAS_PIL = True
except ImportError:
    _PILImage = None
    _HAS_PIL = False

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "brands"
OUT = ROOT / "docs"

# ---------- 分類系統（scaled catalog：78 brands → 6 個頂層分類） ----------
CATEGORIES = [
    {"slug": "japanese", "name": "日式動漫 · 浮世繪",
     "desc": "浮世繪大師、日本妖怪、動漫設計圖與背景、和風藝術"},
    {"slug": "comics", "name": "公版卡通 · 連環漫畫",
     "desc": "黃金年代報紙漫畫、默片動畫、童話與公版角色"},
    {"slug": "art", "name": "世界名畫 · 藝術風格",
     "desc": "大師名畫、藝術運動、雕塑版畫、科幻藝術"},
    {"slug": "world", "name": "世界文化 · 地標 · 自然",
     "desc": "古文明、地標建築、動物植物、自然史、服飾"},
    {"slug": "scenes", "name": "場景 · 道具 · 角色原型",
     "desc": "背景、職業角色、道具武器、節慶、動態手勢"},
    {"slug": "opensource", "name": "開源 · 素材包",
     "desc": "開源吉祥物、CC0 原創角色、免費素材來源"},
]

# slug → 分類（明確、deterministic）
BRAND_CATEGORY = {
    "japanese-anime-backgrounds": "japanese", "japanese-anime-design-sheets": "japanese",
    "japanese-anime-extra-sources": "japanese", "japanese-anime-style-reference": "japanese",
    "japanese-art-collection": "japanese", "japanese-theme-illustrations": "japanese",
    "japanese-yokai": "japanese", "ukiyoe-nouveau-fantasy-markets": "japanese",
    "wildlife-ukiyoe-childrens-mood": "japanese", "regional-architecture-japan-celestials": "japanese",
    "vintage-comic-strips": "comics", "pd-animation-1920s30s": "comics",
    "pd-childrens-book-illustrators": "comics", "pd-golden-age-superheroes": "comics",
    "pd-literature-folklore": "comics", "fairy-tales-mythology": "comics",
    "international-pd-characters": "comics", "winnie-the-pooh": "comics", "disney-silent": "comics",
    "barney-google": "comics", "buck-rogers": "comics", "buster-brown": "comics",
    "felix-the-cat": "comics", "fleischer-betty-boop": "comics", "happy-hooligan": "comics",
    "jiggs": "comics", "katzenjammer-kids": "comics", "krazy-kat": "comics",
    "little-nemo": "comics", "mutt-jeff": "comics", "olive-oyl": "comics", "oswald": "comics",
    "polly-pals": "comics", "popeye": "comics", "skippy": "comics", "andy-gump": "comics",
    "yellow-kid": "comics",
    "art-movements-mythical-cuisine": "art", "cityscapes-historical-scenes": "art",
    "egyptian-greek-roman-antiquity": "art", "global-art-traditions-props-science": "art",
    "historical-props-golden-age": "art", "marine-masterpieces-astronomy": "art",
    "master-paintings-cities-marine": "art", "master-paintings-natural-wonders-mythical": "art",
    "masterpieces-cities-archetypes-feasts": "art", "masterpieces-cities-fauna-mythical": "art",
    "realism-postimpressionism-masterpieces": "art", "scifi-art-dramatic-scenes": "art",
    "non-western-mythology": "art", "retro-modern-instruments-marine-cities": "art",
    "ancient-civilizations-performance-scripts": "world", "ancient-traditions-interiors-flora": "world",
    "costumes-landscapes-work-animals-props": "world", "dance-instruments-crafts-festivals": "world",
    "flags-interiors-landmarks-biomes": "world", "global-cultural-traditions-landmarks": "world",
    "landmarks-exotic-fauna-japanese-culture": "world", "maya-landmarks-american-natural-history": "world",
    "natural-history-chinese-culture-architecture": "world", "regional-landmarks-global-fauna-art": "world",
    "sculpture-engraving-fauna-sports": "world", "textiles-heraldry-ships-weapons": "world",
    "vehicles-landmarks": "world", "world-architecture-flora-cuisine-weather": "world",
    "world-costumes-asian-folk-art": "world", "anthropomorphic-animals": "world",
    "genre-life-trades-legendary-heroes": "scenes", "motion-emotion-hands-silhouette": "scenes",
    "musicians-scientists-performing": "scenes", "occupations-monsters": "scenes",
    "props-weapons": "scenes",
    "open-source-mascots": "opensource", "oss-software-mascots": "opensource",
    "cc0-original-characters": "opensource", "free-asset-sources": "opensource",
    "blender-open-movies": "opensource", "animation-backgrounds-general": "opensource",
}

def brand_category(b):
    return BRAND_CATEGORY.get(b["slug"], "art")

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
/* ---------- Scaled catalog: 分類導航 ---------- */
nav.cat-nav {
  display: flex; gap: 4px; flex-wrap: wrap; margin: 16px 0 4px;
  padding-top: 12px; border-top: 1px solid var(--border);
}
nav.cat-nav a {
  padding: 7px 14px; border-radius: 8px; border: 1px solid transparent;
  color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 600;
  transition: all .12s ease;
}
nav.cat-nav a:hover { color: var(--forest); background: #f2eee4; }
nav.cat-nav a.active { color: var(--forest); background: #e9f0e9; border-color: var(--border); }
nav.cat-nav .cat-count { color: var(--terracotta); font-weight: 700; font-size: .78rem; margin-left: 3px; }
/* 分類英雄 / 區塊 */
.cat-hero { background: #fffdf9; border: 1px solid var(--border); border-radius: 12px; padding: 22px 26px; margin-bottom: 26px; }
.cat-hero h1.page { margin-bottom: 6px; }
.cat-hero p { color: var(--muted); max-width: 72ch; }
.cat-block { margin-bottom: 34px; }
.cat-block-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.cat-block-head h2 { margin-top: 0; border: none; }
.cat-block-head .cat-desc { color: var(--muted); font-size: .9rem; }
.cat-block-head .cat-jump { color: var(--forest); font-size: .85rem; text-decoration: none; font-weight: 600; }
/* 搜尋 */
.searchbar { max-width: 640px; margin: 20px 0 6px; position: relative; }
.searchbar input {
  width: 100%; padding: 13px 18px 13px 44px; border: 1px solid var(--border);
  border-radius: 12px; font-size: 1rem; background: #fff; color: var(--ink);
  outline: none; transition: border-color .12s ease, box-shadow .12s ease;
}
.searchbar input:focus { border-color: var(--forest); box-shadow: 0 0 0 3px rgba(62,92,75,.12); }
.searchbar .search-icon {
  position: absolute; left: 15px; top: 50%; transform: translateY(-50%);
  color: var(--muted); font-size: 1.05rem; pointer-events: none;
}
.search-hint { color: var(--muted); font-size: .82rem; margin: 8px 2px 0; }
/* 分類品牌卡（有縮圖） */
.brand-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-top: 16px; }
.brand-card {
  display: flex; gap: 14px; align-items: stretch; background: var(--card);
  border: 1px solid var(--border); border-radius: 12px; padding: 14px;
  text-decoration: none; color: var(--ink); transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}
.brand-card:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.07); border-color: var(--forest); }
.brand-card .b-thumb {
  width: 84px; min-width: 84px; height: 84px; border-radius: 9px; overflow: hidden;
  background: #eee7db; display: flex; align-items: center; justify-content: center;
}
.brand-card .b-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.brand-card .b-thumb .noimg { color: var(--muted); font-size: 1.5rem; }
.brand-card .b-body { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.brand-card .b-name { font-family: "Noto Serif TC", Georgia, serif; font-weight: 700; font-size: 1rem; line-height: 1.35; }
.brand-card .b-zh { color: var(--muted); font-size: .8rem; }
.brand-card .b-desc { color: var(--muted); font-size: .82rem; margin-top: 5px; flex: 1; }
.brand-card .b-meta { display: flex; align-items: center; gap: 8px; margin-top: 9px; flex-wrap: wrap; }
.brand-card .b-count { color: var(--terracotta); font-weight: 700; font-size: .82rem; }
.brand-card .lic-row { display: flex; gap: 4px; flex-wrap: wrap; }
/* 過濾隱藏（搜尋用） */
.filter-hidden { display: none !important; }
.no-result { display: none; color: var(--muted); padding: 24px; text-align: center; }

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
/* ---------- Lightbox ---------- */
.lightbox { display: none; position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,.88); cursor: zoom-out; }
.lightbox.open { display: flex; align-items: center; justify-content: center; }
.lightbox img { max-width: 92vw; max-height: 92vh; object-fit: contain; background: #000; border-radius: 6px; box-shadow: 0 8px 40px rgba(0,0,0,.6); }
.lightbox .lb-cap { position: absolute; bottom: 18px; left: 0; right: 0; text-align: center; color: #ddd; font-size: .85rem; padding: 0 20px; }
.lightbox .lb-close { position: absolute; top: 14px; right: 22px; color: #fff; font-size: 2rem; line-height: 1; cursor: pointer; }
a.zoom { display: inline-block; cursor: zoom-in; }
.gallery figure img { cursor: zoom-in; }
"""

PAGE_FOOT = f"""\
<div class="wrap">
  <div class="footer-note">
    Video Gen Cart — 公版卡通素材庫。本網站資料只供參考，唔係法律意見；使用前請自行核實你所在地嘅版權 / 商標法例。
  </div>
</div>
<div class="lightbox" id="lightbox" aria-hidden="true"><span class="lb-close" id="lb-close">&times;</span><img src="" alt="" id="lb-img"><div class="lb-cap" id="lb-cap"></div></div>
<script>
(function(){{
  var lb=document.getElementById('lightbox'), img=document.getElementById('lb-img'), cap=document.getElementById('lb-cap');
  function open(src,alt){{ img.src=src; img.alt=alt; cap.textContent=alt; lb.classList.add('open'); lb.setAttribute('aria-hidden','false'); }}
  function close(){{ lb.classList.remove('open'); img.src=''; lb.setAttribute('aria-hidden','true'); }}
  document.addEventListener('click', function(e){{
    var t=e.target.closest('a.zoom, .gallery figure img, .char-hero img');
    if(t && t.tagName!=='IMG'){{ t=e.target; }}
    if(t && t.tagName==='IMG' && (t.closest('a.zoom') || t.closest('.gallery') || t.closest('.char-hero'))){{
      e.preventDefault(); var src=t.getAttribute('data-full')||t.currentSrc||t.src;
      open(src, t.getAttribute('alt')||'');
    }}
  }});
  lb.addEventListener('click', function(e){{ if(e.target===lb||e.target.id==='lb-close') close(); }});
  document.addEventListener('keydown', function(e){{ if(e.key==='Escape') close(); }});
}})();
</script>
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

def brand_card(b, prefix=""):
    """有縮圖嘅品牌卡（scaled catalog 首頁/分類頁用）。"""
    thumb = IMAGES.get(b["slug"], {}).get("file")
    if not thumb:
        for c in characters.get(b["slug"], []):
            thumb = IMAGES.get(c["slug"], {}).get("file")
            if thumb: break
    n = len(characters.get(b["slug"], []))
    thumb_html = (f'<div class="b-thumb"><img src="{prefix}assets/img/{html.escape(_thumb_for(thumb))}" alt="" loading="lazy"></div>'
                  if thumb else '<div class="b-thumb"><span class="noimg">🎞</span></div>')
    return f'''<a class="brand-card" href="{prefix}brands/{b["slug"]}/index.html">
  {thumb_html}
  <div class="b-body">
    <div class="b-name">{html.escape(b["name"])}</div>
    <div class="b-zh">{html.escape(b.get("brand_zh",""))}</div>
    <div class="b-desc">{html.escape(str(b.get("era",""))) }</div>
    <div class="b-meta">
      <span class="b-count">{n} 角色</span>
      <span class="lic-row">{brand_license_badges(b)}</span>
    </div>
  </div>
</a>'''

# Client-side 搜尋：篩選所有 .brand-card（data-search 含品牌+角色名）
SEARCH_JS = """<script>
(function(){
  var box=document.getElementById('brand-search');
  if(!box) return;
  box.addEventListener('input', function(){
    var q=box.value.trim().toLowerCase();
    var cards=document.querySelectorAll('.brand-card');
    var any=false;
    cards.forEach(function(c){
      var holder=c.parentElement;
      var hay=(holder&&holder.getAttribute('data-search')||'').toLowerCase();
      var show=!q||hay.indexOf(q)!==-1;
      holder.classList.toggle('filter-hidden', !show);
      if(show) any=true;
    });
    var blocks=document.querySelectorAll('.cat-block');
    blocks.forEach(function(bl){
      var hasVisible=[].some.call(bl.querySelectorAll('.brand-card'), function(c){return !c.parentElement.classList.contains('filter-hidden');});
      bl.classList.toggle('filter-hidden', !hasVisible && q!=='');
      if(hasVisible) any=true;
    });
    var nr=document.getElementById('no-result');
    if(nr) nr.style.display = q && !any ? 'block' : 'none';
  });
})();
</script>"""

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

def _cat_nav(active_cat=None, prefix=""):
    """分類導航（scaled catalog 用）— 6 個頂層分類 + 角色數統計。"""
    links = [f'<a href="{prefix}index.html" class="{"" if active_cat != "all" else "active"}">全部 <span class="cat-count">{len(brands)}</span></a>']
    for cat in CATEGORIES:
        n = _cat_brand_count(cat["slug"])
        cls = "active" if active_cat == cat["slug"] else ""
        links.append(f'<a href="{prefix}category/{cat["slug"]}.html" class="{cls}">{html.escape(cat["name"])} <span class="cat-count">{n}</span></a>')
    return f'<nav class="cat-nav">{"".join(links)}</nav>'

def _cat_brand_count(slug):
    return sum(1 for b in brands.values() if brand_category(b) == slug)

def header(title, active_brand=None, page_zh="", jsonld=None, prefix="", active_cat=None):
    """統一導航 header。prefix 係由當前頁面到 site root 嘅相對路徑：
    根頁 = ''（空），品牌/角色頁 = '../../'。所有連結經 prefix 保證正確。"""
    # 若喺品牌/角色頁，highlight 對應分類
    if active_cat is None and active_brand and active_brand in brands:
        active_cat = brand_category(brands[active_brand])
    nav = _cat_nav(active_cat=active_cat, prefix=prefix)
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

def _zh_suffix(c, in_card=True):
    """若 character_zh 同 name 唔同先輸出中文名，避免重複。"""
    zh = (c.get("character_zh") or "").strip()
    if not zh or zh == (c.get("name") or "").strip():
        return ""
    return f'<span class="zh">{html.escape(zh)}</span>'

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
              <div><span class="name">{html.escape(c["name"])}</span>{_zh_suffix(c)}</div>
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
    body.append(f'<h1 class="page">{html.escape(c["name"])} {_zh_suffix(c)}</h1>')
    # 角色圖片 + 來源
    # 角色頁面圖像：先睇角色 slug，冇就 fallback 到品牌 slug
    img = IMAGES.get(slug) or IMAGES.get(brand["slug"])
    if img:
        full = img["file"]
        src = _thumb_for(full)
        body.append(f'''<div class="char-hero"><a class="zoom" href="../../assets/img/{html.escape(full)}" data-full="../../assets/img/{html.escape(full)}"><img src="../../assets/img/{html.escape(src)}" alt="{html.escape(c["name"])}" loading="lazy"></a>
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
              <img src="../../assets/gallery/{html.escape(_gallery_thumb(g.get("file","")))}" data-full="../../assets/gallery/{html.escape(g.get("file",""))}" alt="{html.escape(g.get("title",""))}" loading="lazy">
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

def _ensure_thumbs():
    """為所有主圖 + gallery 圖生成 thumbnail（webp，寬 ~480px），加速首屏載入。"""
    if not _HAS_PIL:
        return  # 冇 PIL 環境跳過 thumbnail 生成（HTML 用原圖，唔 crash）
    assert _PILImage is not None
    import os
    Image = _PILImage
    # 主圖
    for slug, e in IMAGES.items():
        f = e.get("file", "")
        if not f: continue
        full = OUT / "assets" / "img" / f
        if not full.exists(): continue
        thumb_dir = OUT / "assets" / "img" / "thumbs"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        tf = thumb_dir / (os.path.splitext(f)[0] + ".jpg")
        if tf.exists(): continue
        try:
            im = Image.open(full)
            im.thumbnail((480, 480))
            im.convert("RGB").save(tf, "JPEG", quality=80)
        except Exception:
            pass
    # gallery 圖
    gdir = OUT / "assets" / "gallery"
    gthumb = OUT / "assets" / "gallery" / "thumbs"
    if gdir.exists():
        gthumb.mkdir(parents=True, exist_ok=True)
        for f in os.listdir(gdir):
            if f == "thumbs": continue
            full = gdir / f
            tf = gthumb / (os.path.splitext(f)[0] + ".jpg")
            if tf.exists(): continue
            try:
                im = Image.open(full)
                im.thumbnail((480, 480))
                im.convert("RGB").save(tf, "JPEG", quality=80)
            except Exception:
                pass

def _thumb_for(f):
    """若存在 thumbnail 就返回 thumbs 路徑，否則原圖。"""
    import os
    base = os.path.splitext(f)[0]
    tf = OUT / "assets" / "img" / "thumbs" / (base + ".jpg")
    if tf.exists():
        return f"thumbs/{base}.jpg"
    return f

def _gallery_thumb(f):
    import os
    base = os.path.splitext(f)[0]
    tf = OUT / "assets" / "gallery" / "thumbs" / (base + ".jpg")
    if tf.exists():
        return f"thumbs/{base}.jpg"
    return f

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

def page_category(cat):
    """分類索引頁：列出該分類下所有品牌（有縮圖 + 即時搜尋）。"""
    members = sorted([b for b in brands.values() if brand_category(b) == cat["slug"]],
                     key=lambda x: x["name"].lower())
    total_chars = sum(len(characters.get(b["slug"], [])) for b in members)
    body = [f'<div class="wrap"><div class="breadcrumb"><a href="../index.html">全部品牌</a> › {html.escape(cat["name"])}</div>']
    body.append(f'<div class="cat-hero"><h1 class="page">{html.escape(cat["name"])} <span style="color:var(--muted);font-size:1rem;font-weight:400">{len(members)} 品牌 · {total_chars} 角色</span></h1>')
    body.append(f'<p>{html.escape(cat["desc"])}</p></div>')
    body.append(f'''<div class="searchbar"><span class="search-icon">⌕</span>
      <input type="text" id="brand-search" placeholder="搜尋品牌 / 角色名… (e.g. 北齋, 妖怪, Popeye)" autocomplete="off"></div>
      <div class="search-hint">搜尋會即時篩選以下品牌（比對品牌名＋旗下角色名）。</div>''')
    body.append('<div class="wrap"><div class="brand-grid">')
    for b in members:
        search_terms = b["name"] + " " + b.get("brand_zh", "") + " " + \
                       " ".join(c.get("name", "") for c in characters.get(b["slug"], []))
        body.append(f'<div data-search="{html.escape(search_terms)}">{brand_card(b, "../")}</div>')
    body.append('</div><div class="no-result" id="no-result">搵唔到符合嘅品牌 / 角色。</div></div>')
    body.append('</div>')
    return "".join(body)

def build():
    load()
    OUT.mkdir(parents=True, exist_ok=True)
    _ensure_thumbs()  # 先生成 thumbnail，HTML 先會引用 thumbs/
    total_chars = sum(len(v) for v in characters.values())
    # ---- index（分類分區 + 搜尋） ----
    idx = [header("全部品牌", active_cat="all")]
    idx.append('<div class="wrap"><div class="hero"><h2>自由創作卡通素材庫</h2>')
    idx.append('<p>收集網上現屬公版 / 自由使用、過去受歡迎嘅卡通人物同素材，方便自由創作者攞嚟做 AI 創意。以「分類 → 品牌 → 角色」三層瀏覽，每項齊備圖片、場景、文字、性格、對話等素材。</p>')
    idx.append(f'<div class="stat-row"><div class="stat"><b>{len(brands)}</b> 個品牌</div><div class="stat"><b>{total_chars}</b> 個角色</div><div class="stat"><b>{len(CATEGORIES)}</b> 個分類</div></div>')
    idx.append('</div>')
    idx.append(f'''<div class="searchbar"><span class="search-icon">⌕</span>
      <input type="text" id="brand-search" placeholder="搜尋品牌 / 角色名… (e.g. 北齋, 妖怪, Popeye)" autocomplete="off"></div>
      <div class="search-hint">搜尋會即時篩選以下分類同品牌（比對品牌名＋旗下角色名）。</div>''')
    # 每個分類一個區塊
    for cat in CATEGORIES:
        members = sorted([b for b in brands.values() if brand_category(b) == cat["slug"]],
                         key=lambda x: x["name"].lower())
        if not members: continue
        cchars = sum(len(characters.get(b["slug"], [])) for b in members)
        idx.append('<div class="wrap cat-block">')
        idx.append(f'''<div class="cat-block-head">
          <h2>{html.escape(cat["name"])} <span style="font-size:.85rem;color:var(--muted);font-weight:400">({len(members)} 品牌 · {cchars} 角色)</span></h2>
          <span class="cat-desc">{html.escape(cat["desc"])}</span>
          <a class="cat-jump" href="category/{cat["slug"]}.html">查看全部 →</a></div>''')
        idx.append('<div class="brand-grid">')
        for b in members:
            search_terms = b["name"] + " " + b.get("brand_zh", "") + " " + \
                           " ".join(c.get("name", "") for c in characters.get(b["slug"], []))
            idx.append(f'<div data-search="{html.escape(search_terms)}">{brand_card(b)}</div>')
        idx.append('</div></div>')
    idx.append('<div class="wrap no-result" id="no-result">搵唔到符合嘅品牌 / 角色。</div>')
    idx.append(PAGE_FOOT + SEARCH_JS)
    (OUT / "index.html").write_text("".join(idx), encoding="utf-8")
    # ---- category pages ----
    cdir = OUT / "category"
    cdir.mkdir(parents=True, exist_ok=True)
    for cat in CATEGORIES:
        htmlout = header(f'{cat["name"]}', active_cat=cat["slug"], prefix="../") \
                  + page_category(cat) + PAGE_FOOT + SEARCH_JS
        (cdir / f'{cat["slug"]}.html').write_text(htmlout, encoding="utf-8")
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
