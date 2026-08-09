#!/usr/bin/env python3
"""
fetch_gallery.py — 為每個角色採購多角度參考圖（動畫用）
從 Wikimedia Commons + Openverse (CC) 兩個來源攞圖。
對每個角色攞 gallery/<slug>/*.jpg 多張，並輸出 gallery_manifest.json。
"""
import requests, json, re, html as _html
from pathlib import Path

UA = {'User-Agent': 'VideoGenCart/1.0 (nkyang10@gmail.com)'}
CM_API = 'https://commons.wikimedia.org/w/api.php'
OV_API = 'https://api.openverse.org/v1/images/'
ROOT = Path(__file__).resolve().parent.parent
GALLERY = ROOT / 'docs' / 'assets' / 'gallery'
GALLERY.mkdir(parents=True, exist_ok=True)
IMG_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

PD_KEYWORDS = ['public domain', 'pd-1923', 'pd-us', 'pd-old', 'pd-expired',
               'pd-art', 'pd-old-70', 'copyright expired', 'pd-self']

# slug -> [ (搜尋詞, 角度/場景描述), ... ]
GALLERY_QUERIES = {
    'mickey-1928': [
        ('Steamboat Willie Mickey', '汽船威利', '首部短片'),
        ('Mickey Mouse 1928 Plane Crazy', '飛機狂想曲', '早期造型'),
        ('Mickey Mouse cartoon cels', '賽璐璐', '動畫製作'),
    ],
    'minnie-1928': [
        ('Minnie Mouse Steamboat Willie', '汽船威利', '首部短片'),
        ('Minnie Mouse 1928', '早期造型', '默片'),
    ],
    'pluto-1930': [
        ('Pluto Disney 1930', '早期 Pluto', '獵犬'),
        ('Pluto dog cartoon', 'Pluto', '造型'),
    ],
    'betty-boop-1930': [
        ('Betty Boop Dizzy Dishes', '迪齊餐碟', '首登場'),
        ('Betty Boop 1930', '早期 Betty', 'Fleischer'),
    ],
    'popeye-1929': [
        ('Popeye Thimble Theatre 1929', '大力水手', '報紙漫畫'),
        ('Popeye comic strip Segar', 'Segar 原創', '連環畫'),
    ],
    'felix-early': [
        ('Felix the Cat 1919', '菲力貓', '早期'),
        ('Felix the Cat Feline Follies', '首登場', '默片'),
    ],
    'oswald-1927': [
        ('Oswald the Lucky Rabbit 1927', '幸運兔奧斯華', '首登場'),
        ('Oswald Lucky Rabbit cartoon', '奧斯華', '造型'),
    ],
    'pooh-1926': [
        ('Winnie-the-Pooh 1926 Milne', '小熊維尼', '原著'),
        ('E.H. Shepard Pooh illustration', 'Shepard 插圖', '原插圖'),
    ],
    'buster-brown': [
        ('Buster Brown Outcault comic', '巴斯特布朗', '報紙漫畫'),
        ('Buster Brown and Tige', '巴斯特與泰格', '同狗'),
        ('Buster Brown shoe mascot', 'Buster Brown 鞋', '廣告'),
    ],
    'little-nemo': [
        ('Little Nemo McCay', '小尼莫', '夢境'),
        ('Little Nemo Slumberland comic', '夢境國度', '全版漫畫'),
        ('Winsor McCay comic', '麥凱作品', '藝術家'),
    ],
    'krazy-kat': [
        ('Krazy Kat Herriman comic', '瘋貓', '沙漠漫畫'),
        ('Ignatz Mouse Krazy Kat', '伊格納茨', '老鼠'),
        ('Herriman Krazy Kat Coconino', 'Coconino', '沙漠'),
    ],
    'katzenjammer-kids': [
        ('Katzenjammer Kids comic', '凱曾加默小孩', '報紙漫畫'),
        ('Hans and Fritz Katzenjammer', '漢斯與弗里茨', '主角'),
        ('Rudolph Dirks comic strip', '迪克斯', '作者'),
    ],
    'mutt-jeff': [
        ('Mutt and Jeff comic Fisher', '馬特與傑夫', '報紙漫畫'),
        ('Bud Fisher cartoon', '費舍', '作者'),
        ('Mutt Jeff comic strip 1910', 'Mutt & Jeff', '連環畫'),
    ],
    'happy-hooligan': [
        ('Happy Hooligan Opper comic', '開心流浪漢', '報紙漫畫'),
        ('Frederick Opper comic strip', '奧珀', '作者'),
        ('Happy Hooligan 1900', '開心流浪漢', '早期'),
    ],
    'olive-oyl': [
        ('Olive Oyl Segar comic', '奧麗芙', '報紙漫畫'),
        ('Thimble Theatre Segar', '蓑衣劇院', '原作'),
        ('Olive Oyl Popeye', '奧麗芙', '造型'),
    ],
    'yellow-kid': [
        ('Yellow Kid Outcault comic', '黃孩子', '首個漫畫'),
        ('Hogan Alley Yellow Kid', '後巷', '場景'),
        ('Richard Outcault cartoon', '奧特考特', '作者'),
    ],
    'andy-gump': [
        ('Andy Gump The Gumps comic', '安迪古普', '報紙漫畫'),
        ('The Gumps Sidney Smith', '古普一家', '連載'),
    ],
    'jiggs': [
        ('Bringing Up Father Jiggs comic', '傑格斯', '報紙漫畫'),
        ('McManus Bringing Up Father', '麥克曼努斯', '作者'),
        ('Maggie and Jiggs', '瑪姬與傑格斯', '夫妻'),
    ],
    'skippy': [
        ('Skippy Percy Crosby comic', '斯基皮', '報紙漫畫'),
        ('Skippy comic strip 1920s', '斯基皮', '連載'),
    ],
    'polly-pals': [
        ('Polly Her Pals Sterrett comic', '波莉', 'Art Deco'),
        ('Cliff Sterrett comic', '斯特雷特', '作者'),
    ],
    'barney-google': [
        ('Barney Google comic DeBeck', '巴尼古高', '報紙漫畫'),
        ('Spark Plug horse cartoon', '蒙馬', '馬'),
        ('Billy DeBeck comic strip', '德貝克', '作者'),
    ],
    'buck-rogers': [
        ('Buck Rogers comic strip', '巴克羅渣士', '科幻漫畫'),
        ('Buck Rogers 25th century', '25 世紀', '未來'),
        ('Nowlan Buck Rogers', '諾蘭', '作者'),
    ],
    # 新角色 — 自由授權原創角色
    'sintel': [
        ('Sintel Blender open movie', '辛特', '開放電影'),
        ('Sintel character design', '辛特設定', '角色'),
    ],
    'big-buck-bunny': [
        ('Big Buck Bunny Blender', '大公雞兔', '開放電影'),
        ('Big Buck Bunny character', '大公雞兔', '角色'),
    ],
    'koro': [
        ('Caminandes Koro llama', '可樂', '開放電影'),
        ('Caminandes llama', '可樂', '羊駝'),
    ],
    'zora-snep': [('Zora the Snep fursona', '佐拉', '雪豹 fursona')],
    'routhwick-tanuki': [("Routhwick's OC tanuki", '羅思威克', '狸貓角色')],
    'lexi': [('Sleeps-Darkly Lexi four arms', '萊克希', '四臂女孩')],
    # 第四批 — 開放源碼吉祥物 + 更多原創角色
    'oti': [('Caminandes Oti penguin', '奧提', '企鵝'), ('Caminandes episode', '卡米南德斯', '開放電影')],
    'wapuu': [('Wapuu WordPress mascot', '哇普', '吉祥物')],
    'kiki': [('Kiki Cyber Human Krita', '琪琪', 'Krita 吉祥物')],
    'theophilus': [('Theophilus Harvett character', '西奧菲勒斯', '舞台角色')],
    'duskako': [('Duskako', '暮光之狐', 'fursona')],
    'xenia': [('Xenia the Linux Vixen', '希妮雅', 'Linux 狐')],
    'sodabytes': [('kemono furry illustration', '獸人', 'Kemono 範例')],
}

def strip_html(s):
    return _html.unescape(re.sub(r'<[^>]+>', '', s or '')).strip()

def search_commons(query, limit=8):
    params = {
        'action':'query','format':'json',
        'generator':'search','gsrsearch':query,'gsrnamespace':6,'gsrlimit':limit,
        'prop':'imageinfo','iiprop':'url|extmetadata|size','iiurlwidth':600,
    }
    try:
        d = requests.get(CM_API, params=params, headers=UA, timeout=40).json()
    except Exception:
        return []
    out = []
    for pid, p in d.get('query',{}).get('pages',{}).items():
        ii = p.get('imageinfo',[{}])[0]
        em = ii.get('extmetadata',{})
        lic = em.get('LicenseShortName',{}).get('value','') or ''
        out.append({
            'source':'commons', 'title': p.get('title',''),
            'license': lic,
            'license_url': em.get('LicenseUrl',{}).get('value',''),
            'artist': strip_html(em.get('Artist',{}).get('value',''))[:80],
            'url': ii.get('url',''), 'thumb': ii.get('thumburl',''),
            'width': ii.get('width',0), 'height': ii.get('height',0),
        })
    return out

def search_openverse(query, limit=8, licenses='cc0,pdm,by'):
    params = {'q': query, 'page_size': limit, 'license': licenses}
    try:
        d = requests.get(OV_API, params=params, headers={'User-Agent':'VideoGenCart/1.0'}, timeout=40).json()
    except Exception:
        return []
    out = []
    for r in d.get('results', []):
        url = r.get('url','')
        if not url or not url.lower().endswith(IMG_EXTS):
            continue
        lic = r.get('license','')
        out.append({
            'source':'openverse', 'title': r.get('title',''),
            'license': lic, 'license_version': r.get('license_version',''),
            'license_url': r.get('license_url',''),
            'artist': (r.get('creator','') or '')[:80],
            'creator_url': r.get('creator_url',''),
            'url': url, 'thumb': url,
            'width': r.get('width',0), 'height': r.get('height',0),
            'foreign_landing_url': r.get('foreign_landing_url',''),
        })
    return out

def is_pd(lic):
    l = (lic or '').lower()
    if any(k in l for k in PD_KEYWORDS): return True
    if l.startswith(('cc0','cc-by','cc by','pdm','by','by-sa')): return True
    if any(k in l for k in ['creative commons', 'creativecommons', 'cc by-sa']): return True
    return False

def main():
    manifest = {}
    if (GALLERY.parent / 'gallery_manifest.json').exists():
        manifest = json.loads((GALLERY.parent / 'gallery_manifest.json').read_text(encoding='utf-8'))
    for slug, queries in GALLERY_QUERIES.items():
        if slug in manifest and len(manifest[slug]) >= 4:
            print(f'⏭ {slug}: 已有 {len(manifest[slug])} 張，skip')
            continue
        existing_titles = {f['title'] for f in manifest.get(slug, [])}
        found = list(manifest.get(slug, []))
        for q, angle, desc in queries:
            # Commons 優先，每個 query 攞多張（唔止一張）
            cm_n = 0
            for r in search_commons(q):
                if (r['thumb'] and r['title'].lower().endswith(IMG_EXTS)
                        and is_pd(r['license']) and r['title'] not in existing_titles
                        and r['title'] not in [f['title'] for f in found]):
                    found.append({**r, 'angle': angle, 'scene': desc, 'file': ''})
                    existing_titles.add(r['title'])
                    cm_n += 1
                    if cm_n >= 3: break
            # Openverse 補充
            ov_n = 0
            for r in search_openverse(q):
                if (r['title'] not in existing_titles
                        and r['title'] not in [f['title'] for f in found]
                        and is_pd(r['license']) and r['url'].lower().endswith(IMG_EXTS)):
                    found.append({**r, 'angle': angle, 'scene': desc, 'file': ''})
                    existing_titles.add(r['title'])
                    ov_n += 1
                    if ov_n >= 2: break
        # 下載（重新下載，因為 file 欄留空）
        local = []
        for i, r in enumerate(found[:8]):
            url = r.get('thumb') or r.get('url')
            if not url: continue
            try:
                img = requests.get(url, headers=UA, timeout=50)
                if img.status_code != 200 or len(img.content) < 2000:
                    continue
                fname = f'{slug}-{i+1}.jpg'
                (GALLERY / fname).write_bytes(img.content)
                r = {**r, 'file': fname}
            except Exception as e:
                print(f'  ✗ {slug} 圖{i}: {e}')
            local.append(r)
        manifest[slug] = local
        print(f'✓ {slug}: {len(local)} 張參考圖' + ('（⚠ 得少量）' if len(local) < 3 else ''))
    (GALLERY.parent / 'gallery_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\nSaved → {GALLERY.parent}/gallery_manifest.json')

if __name__ == '__main__':
    main()
