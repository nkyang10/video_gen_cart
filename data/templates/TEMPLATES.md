# Brand Template — 劇集品牌

每個品牌一個檔：`data/brands/<brand-slug>/brand.md`

```markdown
---
brand: "品牌英文名"
brand_zh: "品牌中文名"
slug: "brand-slug"
type: "卡通系列 | 漫畫系列 | 動畫電影 | 漫畫報紙連載"
country: "出品國家"
era: "1920s | 1930s | ..."
creator: "原創作者"
original_publisher: "原發行商"
first_appearance_year: 1928
status: "公版 | 部分公版 | 需核實"
---

# 品牌描述

一兩段介紹呢個品牌係咩、點解受歡迎、文化地位。

## 版權狀態（Brand Level）

- **公版判定**：成個系列大部分作品已入公版，但部分後期作品可能仍受保護。
- **Trademark**：商標仍然有效，注意使用限制。
- **司法管轄區**：美國基準（public domain），其他地區需自行核實。

## 旗下公版角色

- [[角色A]] — 一句簡介
- [[角色B]] — 一句簡介
```

---

# Character Template — 角色

每個角色一個檔：`data/brands/<brand-slug>/<character-slug>.md`

```markdown
---
character: "角色英文名"
character_zh: "角色中文名"
slug: "character-slug"
brand: "所屬品牌 slug"
role: "主角 | 配角 | 反派 | ..."
first_appearance: "首次登場作品 + 年份"
creator: "原作者"
public_domain: true          # 是否屬公版
public_domain_jurisdiction: "US"
public_domain_version: "1928 年早期版本"   # 邊個版本公版
protected_portion: "1928 之後嘅演變版本、商標、電影"  # 邊部分仲受保護
trademark: "商標仍然有效，限制使用"
verified: "2026-08-09"       # 核實日期
---

# 角色名（中文名）

## 出處
首次登場作品、年份、原作者、發行商。

## 版權狀態
- **公版**：✔️ / ❌
- **公版版本**：...
- **受保護部分**：...
- **Trademark**：...
- **核實**：日期 + 依據

## 性格 / 人設
- 性格特質（列點）
- 動機 / 目標
- 人際關係（同其他角色）

## 外觀描述（AI 圖片 Prompt 用）
精確描述外表，方便生圖。包含：身形、服裝、標誌性特徵、常見表情。

## 經典對白 / 口頭禪
> 「經典台詞」
> 「另一句」

## 場景 / 設定
- 常見場景
- 時代背景
- 世界觀

## AI 創意用法
- 適合作咩類型創作
- prompt 組合建議
- 注意事項
```
