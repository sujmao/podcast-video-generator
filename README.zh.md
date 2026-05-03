# Podcast Video Generator — 播客視頻生成器

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

[English](README.md)

一行命令，將文字轉換為播客視頻——TTS 語音合成 + 波形可視化 + 標題疊加，全自動一條龍。

基於 [Piper TTS](https://github.com/rhasspy/piper) 和 [ffmpeg](https://ffmpeg.org)。靈感來自 [piper-zh-en-tts](https://github.com/sujmao/piper-zh-en-tts)。

---

## Demo 演示

```bash
python podcast.py --title "Introducing Podcast Video Generator" --content "..."
```

https://github.com/sujmao/podcast-video-generator/blob/main/demo_podcast.mp4

---

## 功能

- **一行命令生成視頻** — 輸入標題和內容，直接輸出播客 MP4
- **中英雙語混輸** — 自動分段：中文走中文模型，英文走英文模型，無縫拼接
- **波形可視化** — 透過 ffmpeg 在深色背景上繪製動態音頻波形
- **標題疊加** — 播客標題居中顯示於畫面頂部
- **自動下載模型** — 首次執行自動從 HuggingFace 下載所需語音模型，後續使用本地快取
- **360p 輸出** — 640×360 H.264 視頻 + AAC 音軌，即產即用

---

## 安裝

```bash
git clone https://github.com/sujmao/podcast-video-generator.git
cd podcast-video-generator
pip install -r requirements.txt
```

**前置條件：** 需要安裝 [ffmpeg](https://ffmpeg.org/download.html) 並加入系統 PATH。

---

## 使用方法

```bash
# 單語言 — 純英文
python podcast.py --title "Morning Briefing" \
    --en-model en_US-lessac-medium \
    --content "Today we will discuss the latest developments..."

# 單語言 — 純中文
python podcast.py --title "今日新聞" \
    --cjk-model zh_CN-huayan-medium \
    --content "今天我們來聊聊人工智慧的最新進展..."

# 中英混輸（自動分段）
python podcast.py --title "AI 專題報導" \
    --content "今天我們來談談 GPT-4o 的 new features..."

# 從文字檔案讀取
python podcast.py --title "讀書心得" --content-file script.txt -o review.mp4

# 調整語速
python podcast.py --title "新聞摘要" --content "..." --speed 1.2
```

### 參數說明

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `--title` | *(必填)* | 播客標題，顯示在視頻頂部 |
| `--content` | `""` | 內容文字 |
| `--content-file` | `""` | 從 `.txt` 檔案讀取內容 |
| `--output`, `-o` | `podcast_output.mp4` | 輸出視頻路徑 |
| `--cjk-model` | `zh_CN-huayan-medium` | 中文 / CJK 段落使用的 Piper 模型 |
| `--en-model` | `en_US-lessac-medium` | 英文 / Latin 段落使用的 Piper 模型 |
| `--speed` | `1.0` | 語速（0.5–3.0） |

---

## 工作原理

```
標題 + 內容文字
       │
       ▼
  ┌─────────────┐
  │ Piper TTS    │  CJK 段落 → 中文模型
  │ 語音合成     │  Latin 段落 → 英文模型
  └──────┬───────┘
         │ WAV 音頻
         ▼
  ┌─────────────┐
  │ ffmpeg       │  showwaves → 波形可視化
  │ 視頻渲染     │  drawtext  → 標題疊加
  └──────┬───────┘
         │
         ▼
   輸出 MP4（360p）
```

---

## 推薦語音模型

| 語言 | 模型 | 大小 | 說明 |
|------|------|------|------|
| 中文 | `zh_CN-huayan-medium` | 60.3 MB | 男聲，品質較好 |
| 中文 | `zh_CN-xiao_ya-medium` | 60.3 MB | 女聲 |
| 英文（美式） | `en_US-lessac-medium` | 60.3 MB | 女聲 |
| 英文（美式） | `en_US-ryan-low` | 60.2 MB | 男聲，體積較小 |
| 英文（英式） | `en_GB-alan-low` | 60.2 MB | 英國男聲 |

完整列表：[HuggingFace Piper 模型庫](https://huggingface.co/rhasspy/piper-voices)

---

## 項目結構

```
podcast-video-generator/
├── podcast.py          # 核心生成器
├── requirements.txt    # Python 依賴
├── demo_podcast.mp4    # 示範輸出
├── models/             # 已下載的 Piper 模型（gitignore）
├── README.md           # 英文文檔
└── README.zh.md        # 中文文檔
```

---

## 致謝

- [Piper TTS](https://github.com/rhasspy/piper) — 快速、本地的神經網路語音合成
- [piper-zh-en-tts](https://github.com/sujmao/piper-zh-en-tts) — Piper 的 Gradio 圖形界面，本項目的混合語言管線靈感來源
- [ffmpeg](https://ffmpeg.org) — 視頻渲染，使用 `showwaves` + `drawtext` 濾鏡

---

## 許可協議

MIT
