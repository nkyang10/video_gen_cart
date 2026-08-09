# 🎬 Video Gen Cart — 自由創作卡通素材庫

收集網上**現屬公版（Public Domain）/ 自由使用**、過去受歡迎嘅卡通人物同素材，方便自由創作者隨時攞嚟用，**唔使擔心版權問題**。

放上去嘅嘢，就係一切可以用嚟做 **AI 創意**嘅素材：圖片、場景、文字、性格、對話、設定……所有關於人物嘅嘢都齊全。

## 📚 分類結構

```
劇集品牌（Brand）
 └── 角色（Character）
      ├── 出處 / 首次登場
      ├── 版權狀態（邊個版本公版、邊部分仲受保護、trademark）
      ├── 性格 / 人設
      ├── 外觀描述（AI 圖片 prompt 用）
      ├── 經典對白 / 口頭禪
      ├── 場景 / 設定
      └── AI 創意用法提示
```

## ⚖️ 版權誠實性守則（Core Rule）

呢個 project 嘅成敗，完全建基於**版權狀態記錄要誠實、可驗證**。每個角色都必須明確寫：

1. **邊個版本屬公版**（例如 1928 年早期版本）
2. **邊部分仲受保護**（例如後來嘅演變版本、電影、商標）
3. **Trademark 仍然有效**（公版唔等於可以濫用品牌商標）
4. **司法管轄區**（公版狀態唔同國家唔同，以美國為主要基準）

**絕不**將仍受版權保護嘅角色列做「自由使用」。如果唔確定，會標明「需自行核實」。

## 🚀 使用方式

### 睇網站
推上去之後，瀏覽 `https://nkyang10.github.io/video_gen_cart/`

### 本地 build
```bash
python3 scripts/generate.py     # Markdown → docs/ 靜態網站
python3 -m http.server 8080 --directory docs/
# 瀏覽 http://localhost:8080
```

### 加新角色
喺 `data/brands/<brand>/<character>.md` 新增一個 Markdown 檔（跟 template），再行 `python3 scripts/generate.py`。

## 📁 目錄結構

```
data/brands/<brand>/
  ├── brand.md            # 品牌 / 劇集資料
  └── <character>.md      # 每個角色一個檔
scripts/
  └── generate.py         # Markdown → 靜態網站 generator
docs/                     # 生成出嚟嘅網站（GitHub Pages 用）
```

## 🛡️ 免責聲明

本 project 只提供整理後嘅公版資訊，唔係法律意見。使用前請自行核實你所屬司法管轄區嘅版權法律，特別係 trademark、角色演變版本、以及衍生作品嘅授權。
