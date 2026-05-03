# Podcast Video Generator

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

[中文版](README.zh.md)

One command to turn text into a podcast video — TTS synthesis + waveform visualization + title overlay, all in a single pipeline.

Built on [Piper TTS](https://github.com/rhasspy/piper) and [ffmpeg](https://ffmpeg.org). Inspired by [piper-zh-en-tts](https://github.com/sujmao/piper-zh-en-tts).

---

## Demo

```
python podcast.py --title "Introducing Podcast Video Generator" --content "..."
```

[![Demo Video](demo_thumbnail.png)](https://raw.githubusercontent.com/sujmao/podcast-video-generator/main/demo_podcast.mp4)

---

## Features

- **Text → Video in one command** — input a title and content, get an MP4 podcast
- **Bilingual Chinese-English** — mixed text is auto-segmented; CJK goes to a Chinese model, Latin to an English model, then merged seamlessly
- **Waveform visualization** — ffmpeg renders an animated audio waveform on a dark background
- **Title overlay** — the podcast title is centered at the top of every frame
- **Auto model download** — required Piper voice models are downloaded on first run; subsequent runs use local cache
- **360p output** — 640×360 H.264 video + AAC audio, ready to share

---

## Installation

```bash
git clone https://github.com/sujmao/podcast-video-generator.git
cd podcast-video-generator
pip install -r requirements.txt
```

**Prerequisite:** [ffmpeg](https://ffmpeg.org/download.html) must be installed and available in `PATH`.

---

## Usage

```bash
# Single language — English only
python podcast.py --title "Morning Briefing" \
    --en-model en_US-lessac-medium \
    --content "Today we will discuss the latest developments..."

# Single language — Chinese only
python podcast.py --title "今日新聞" \
    --cjk-model zh_CN-huayan-medium \
    --content "今天我們來聊聊人工智慧的最新進展..."

# Mixed Chinese-English (auto-segmented)
python podcast.py --title "AI 專題報導" \
    --content "今天我們來談談 GPT-4o 的 new features..."

# From a text file
python podcast.py --title "Book Review" --content-file script.txt -o review.mp4

# Adjust speed
python podcast.py --title "News Summary" --content "..." --speed 1.2
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--title` | *(required)* | Podcast title displayed on the video |
| `--content` | `""` | Content text |
| `--content-file` | `""` | Read content from a `.txt` file |
| `--output`, `-o` | `podcast_output.mp4` | Output video path |
| `--cjk-model` | `zh_CN-huayan-medium` | Piper model for Chinese / CJK text |
| `--en-model` | `en_US-lessac-medium` | Piper model for English / Latin text |
| `--speed` | `1.0` | Speech speed (0.5–3.0) |

---

## How It Works

```
Title + Content Text
       │
       ▼
  ┌─────────────┐
  │ Piper TTS    │  CJK segments → Chinese model
  │ Synthesis    │  Latin segments → English model
  └──────┬───────┘
         │ WAV audio
         ▼
  ┌─────────────┐
  │ ffmpeg       │  showwaves → waveform visualization
  │ Rendering    │  drawtext  → title overlay
  └──────┬───────┘
         │
         ▼
   Output MP4 (360p)
```

---

## Recommended Voice Models

| Language | Model | Size | Notes |
|----------|-------|------|-------|
| Chinese | `zh_CN-huayan-medium` | 60.3 MB | Male, good quality |
| Chinese | `zh_CN-xiao_ya-medium` | 60.3 MB | Female |
| English (US) | `en_US-lessac-medium` | 60.3 MB | Female |
| English (US) | `en_US-ryan-low` | 60.2 MB | Male, smaller |
| English (UK) | `en_GB-alan-low` | 60.2 MB | British male |

Full list: [Piper voices on HuggingFace](https://huggingface.co/rhasspy/piper-voices)

---

## Project Structure

```
podcast-video-generator/
├── podcast.py          # The generator
├── requirements.txt    # Python dependencies
├── demo_podcast.mp4    # Sample output
├── models/             # Downloaded Piper models (gitignored)
├── README.md           # English documentation
└── README.zh.md        # Chinese documentation
```

---

## Credits

- [Piper TTS](https://github.com/rhasspy/piper) — fast, local neural text-to-speech
- [piper-zh-en-tts](https://github.com/sujmao/piper-zh-en-tts) — Gradio web UI for Piper, inspiration for the mixed-language pipeline
- [ffmpeg](https://ffmpeg.org) — video rendering with `showwaves` + `drawtext`

---

## License

MIT
