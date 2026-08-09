#!/usr/bin/env python3
"""
fetch_images.py — 從 Wikimedia Commons 採購公版圖片
對每個角色搜尋圖片，攞 license 資料，只揀 public domain / PD-1923，
下載 thumb 落 docs/assets/img/<slug>.jpg，並輸出 license 記錄。
"""
import requests, json, sys
from pathlib import Path

UA = {'User-Agent': 'VideoGenCart/1.0 (nkyang10@gmail.com)'}
API = 'https://commons.wikimedia.org/w/api.php'
OUT = Path(__file__).resolve().parent.parent / 'docs' / 'assets' / 'img'
OUT.mkdir(parents=True, exist_ok=True)

# (character slug, 搜尋關鍵字, 標題必須包含嘅關鍵字)
QUERIES = {
    'mickey-1928': ('Steamboat Willie Mickey Mouse', 'Mickey'),
    'minnie-1928': ('Mickey and Minnie Mouse Steamboat Willie', 'Minnie'),
    'pluto-1930': ('Pluto dog Disney 1930', 'Pluto'),
    'betty-boop-1930': ('Betty Boop First Version', 'Betty'),
    'popeye-1929': ('First Popeye Strip East Liverpool Review', 'Popeye'),
    'felix-early': ('Felix 1919 Feline Follies', 'Felix'),
    'oswald-1927': ('Oswald the Lucky Rabbit 1927', 'Oswald'),
    'pooh-1926': ('Winnie-the-Pooh 1926 A.A. Milne', 'Winnie'),
    # 新批次 — 1930 前公版經典
    'buster-brown': ('Buster Brown comic strip Outcault', 'Buster'),
    'little-nemo': ('Little Nemo Slumberland Winsor McCay', 'Nemo'),
    'krazy-kat': ('Krazy Kat Ignatz Herriman', 'Krazy'),
    'katzenjammer-kids': ('Katzenjammer Kids Hans Fritz Dirks', 'Katzenjammer'),
    'mutt-jeff': ('Mutt and Jeff Bud Fisher comic', 'Mutt'),
    'happy-hooligan': ('Happy Hooligan comic strip Opper', 'Hooligan'),
    'olive-oyl': ('Olive Oyl Segar Thimble Theatre', 'Olive'),
    # 第三批 — 更多 1930 前公版經典
    'yellow-kid': ('The Yellow Kid Hogan Alley Outcault', 'Yellow'),
    'andy-gump': ('Andy Gump The Gumps Sidney Smith', 'Gump'),
    'jiggs': ('Bringing Up Father Jiggs McManus', 'Jiggs'),
    'skippy': ('Skippy comic strip Percy Crosby', 'Skippy'),
    'polly-pals': ('Polly and Her Pals Cliff Sterrett', 'Polly'),
    'barney-google': ('Barney Google Spark Plug DeBeck', 'Barney'),
    'buck-rogers': ('Buck Rogers 1929 comic strip', 'Buck'),
    # 新品牌 — 自由授權原創角色（CC0/CC-BY/CC-BY-SA）
    'sintel': ('Sintel Blender open movie', 'Sintel'),
    'big-buck-bunny': ('Big Buck Bunny Blender', 'Buck'),
    'koro': ('Caminandes Koro llama', 'Caminandes'),
    'zora-snep': ('Zora the Snep fursona', 'Zora'),
    'routhwick-tanuki': ("Routhwick's OC Left tanuki", 'Routhwick'),
    'lexi': ('Sleeps-Darkly Lexi four arms', 'Lexi'),
    # 第四批 — 開放源碼吉祥物 + 更多原創角色
    'oti': ('Caminandes Oti penguin', 'Oti'),
    'wapuu': ('Wapuu WordPress mascot', 'Wapuu'),
    'kiki': ('Kiki Cyber Human Krita mascot', 'Kiki'),
    'theophilus': ('Theophilus Harvett character', 'Theophilus'),
    'duskako': ('Duskako', 'Duskako'),
    'xenia': ('Xenia the Linux Vixen', 'Xenia'),
    'eggbert': ('Eggbert Finds Love', 'Eggbert'),
    'sodabytes': ('Illustrated example kemono furry', 'kemono'),
}

# 只接受圖片副檔名（排除 .webm/.ogg 等影片）
IMG_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

# License keywords that indicate public domain
PD_KEYWORDS = ['public domain', 'pd-1923', 'pd-us', 'pd-old', 'pd-expired',
               'pd-art', 'pd-old-70', 'public domain in the united states',
               'copyright expired', 'pd-self']

# CC 自由授權 keyword（CC0 / CC-BY / CC-BY-SA 都允許自由使用）
CC_KEYWORDS = ['cc0', 'cc-by', 'cc by', 'cc-by-sa', 'creative commons attribution',
               'creativecommons']

def is_free(lic):
    l = (lic or '').lower()
    if is_pd(l): return True
    return any(k in l for k in CC_KEYWORDS)

def search_images(query, limit=15):
    params = {
        'action':'query','format':'json',
        'generator':'search','gsrsearch':query,'gsrnamespace':6,'gsrlimit':limit,
        'prop':'imageinfo','iiprop':'url|extmetadata|size','iiurlwidth':600,
    }
    r = requests.get(API, params=params, headers=UA, timeout=40)
    d = r.json()
    results = []
    for pid, p in d.get('query',{}).get('pages',{}).items():
        ii = p.get('imageinfo',[{}])[0]
        em = ii.get('extmetadata',{})
        lic = (em.get('LicenseShortName',{}).get('value','') or '')
        lic_url = em.get('LicenseUrl',{}).get('value','')
        art = em.get('Artist',{}).get('value','')[:80] or ''
        title = p.get('title','')
        results.append({
            'title': title,
            'license': lic,
            'license_url': lic_url,
            'artist': art,
            'url': ii.get('url',''),
            'thumb': ii.get('thumburl',''),
            'width': ii.get('width',0), 'height': ii.get('height',0),
            'desc': (em.get('ImageDescription',{}).get('value','') or '')[:150],
        })
    return results

def is_pd(lic):
    l = lic.lower()
    return any(k in l for k in PD_KEYWORDS)

def main():
    manifest = {}
    # 保留已有 manifest（只加新嘅）
    if (OUT.parent / 'image_manifest.json').exists():
        import json as _j
        try: manifest = _j.loads((OUT.parent / 'image_manifest.json').read_text(encoding='utf-8'))
        except: manifest = {}
    # 特定檔名 fallback（當一般搜尋揾唔到，直接指定一個已知 PD 檔）
    SPECIFIC_FILES = {
        'happy-hooligan': 'File:Happy Hooligan 1905-04-09.jpg',
        'skippy': 'File:Skippy No. 1.jpg',
        'yellow-kid': 'File:Yellow Kid 1896-3-15.jpg',
    }

    def fetch_file_by_title(fname):
        p = {'action':'query','format':'json','titles':fname,'prop':'imageinfo',
             'iiprop':'url|extmetadata','iiurlwidth':600}
        d = requests.get(API, params=p, headers=UA, timeout=40).json()
        for pid, pg in d.get('query',{}).get('pages',{}).items():
            if 'missing' in pg: continue
            ii = pg.get('imageinfo',[{}])[0]; em = ii.get('extmetadata',{})
            return {
                'title': pg.get('title',''),
                'license': em.get('LicenseShortName',{}).get('value',''),
                'license_url': em.get('LicenseUrl',{}).get('value',''),
                'artist': em.get('Artist',{}).get('value','')[:80] or '',
                'url': ii.get('url',''), 'thumb': ii.get('thumburl',''),
                'width': ii.get('width',0), 'height': ii.get('height',0),
            }
        return None

    for slug, (query, title_hint) in QUERIES.items():
        if slug in manifest:
            print(f'⏭ {slug}: 已存在，skip')
            continue
        # 指定檔名優先（當 SPECIFIC_FILES 有指定，直接用，唔行 generic search）
        if slug in SPECIFIC_FILES:
            chosen = fetch_file_by_title(SPECIFIC_FILES[slug])
            if chosen:
                ext = '.jpg'
                out_path = OUT / f"{slug}{ext}"
                out_path.write_bytes(requests.get(chosen['thumb'] or chosen['url'], headers=UA, timeout=60).content)
                chosen['file'] = out_path.name
                manifest[slug] = chosen
                print(f"✓ {slug}: {chosen.get('license','')} | {chosen.get('title','')[:50]}")
                continue
        try:
            results = search_images(query)
        except Exception as e:
            print(f'✗ {slug}: API error {e}')
            continue
        # 揀第一張「標題含角色名 + 公版 + 圖片檔」圖片
        chosen = None
        for r in results:
            if (title_hint.lower() in r['title'].lower()
                    and is_free(r['license']) and r['thumb']
                    and r['title'].lower().endswith(IMG_EXTS)):
                chosen = r; break
        if not chosen:
            # fallback: 揀有 thumb 嘅圖片檔（記錄埋非PD）
            chosen = next((r for r in results if r['thumb'] and r['title'].lower().endswith(IMG_EXTS)), None)
        if not chosen:
            # 特定檔名 fallback
            if slug in SPECIFIC_FILES:
                chosen = fetch_file_by_title(SPECIFIC_FILES[slug])
        if not chosen:
            print(f'△ {slug}: 無圖片')
            continue
        ext = '.jpg'
        dest = OUT / f'{slug}{ext}'
        try:
            img = requests.get(chosen['thumb'], headers=UA, timeout=40)
            dest.write_bytes(img.content)
            manifest[slug] = {
                'file': dest.name,
                'title': chosen['title'],
                'license': chosen['license'],
                'license_url': chosen['license_url'],
                'artist': chosen['artist'],
                'source_url': chosen['url'],
                'width': chosen['width'], 'height': chosen['height'],
                'pd': is_free(chosen['license']),
            }
            flag = 'FREE' if is_free(chosen['license']) else '⚠非自由'
            print(f'✓ {slug}: {flag} | {chosen["license"]} | {chosen["title"][:50]}')
        except Exception as e:
            print(f'✗ {slug}: download error {e}')
    # save manifest
    (OUT.parent / 'image_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\nSaved manifest → {OUT.parent}/image_manifest.json')

if __name__ == '__main__':
    main()
