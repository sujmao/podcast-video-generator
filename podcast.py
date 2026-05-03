#!/usr/bin/env python3
"""
Podcast Video Generator
使用 Piper TTS 生成播客語音，透過 ffmpeg 生成帶波形可視化的視頻。

Usage:
  python podcast.py --title "標題" --content "中英混合文字..."
  python podcast.py --title "Title" --content-file script.txt -o output.mp4
"""

import argparse
import subprocess
import sys
import wave
import re
from pathlib import Path

import numpy as np
import requests
from piper import PiperVoice, SynthesisConfig

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

VOICES_JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/voices.json"
PIPER_VOICES_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

DEFAULT_CJK_MODEL = "zh_CN-huayan-medium"
DEFAULT_EN_MODEL = "en_US-lessac-medium"

# CJK character ranges for mixed-language detection
_CJK_CHARS = (
    "一-鿿㐀-䶿"
    "぀-ゟ゠-ヿ"
    "가-힯ᄀ-ᇿ"
    "　-〿"
    "！-～"
)
_CJK_TOKEN = re.compile(f"[{_CJK_CHARS}]+")
_SPLIT_RE = re.compile(f"([{_CJK_CHARS}]+|[^{_CJK_CHARS}]+)")

# Chinese font for ffmpeg drawtext (Windows) — colon escaped for ffmpeg filter syntax
FONT_PATH = "C\\:/Windows/Fonts/msyh.ttc"


def load_registry():
    """Load Piper voice registry from HuggingFace."""
    r = requests.get(VOICES_JSON_URL, timeout=30)
    r.raise_for_status()
    data = r.json()
    registry = {}
    for key, info in data.items():
        # Find the .onnx file entry (there may also be .json and MODEL_CARD entries)
        onnx_path = next((p for p in info["files"] if p.endswith(".onnx")), None)
        if not onnx_path:
            continue
        registry[key] = {
            "path": onnx_path,
            "size": info["files"][onnx_path]["size_bytes"],
            "lang": info["language"]["name_english"],
        }
    return registry


def ensure_model(model_name):
    """Download a Piper model if not already present locally."""
    onnx_path = MODELS_DIR / f"{model_name}.onnx"
    json_path = MODELS_DIR / f"{model_name}.onnx.json"
    if onnx_path.exists() and json_path.exists():
        return

    registry = load_registry()
    info = registry.get(model_name)
    if not info:
        print(f"  [X] Model '{model_name}' not found in registry")
        sys.exit(1)

    if not onnx_path.exists():
        size_mb = info["size"] / 1024 / 1024
        url = f"{PIPER_VOICES_BASE}/{info['path']}"
        print(f"  Downloading {model_name} ({size_mb:.1f} MB)...")
        r = requests.get(url, stream=True, timeout=300)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        last_pct = -1
        tmp = onnx_path.with_suffix(".onnx.tmp")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = int(downloaded / total * 100)
                    if pct >= last_pct + 10:
                        print(f"    {pct}%", flush=True)
                        last_pct = pct
        tmp.rename(onnx_path)
        print(f"    done ({size_mb:.1f} MB)")

    if not json_path.exists():
        config_url = f"{PIPER_VOICES_BASE}/{info['path'].replace('.onnx', '.onnx.json')}"
        r = requests.get(config_url, timeout=60)
        r.raise_for_status()
        json_path.write_bytes(r.content)


def split_mixed_text(text):
    """Split text into (type, segment) tuples: ('cjk', ...) or ('latin', ...)."""
    if not text:
        return []
    segments = []
    for token in _SPLIT_RE.findall(text):
        token = token.strip()
        if not token:
            continue
        if _CJK_TOKEN.search(token):
            segments.append(("cjk", token))
        else:
            segments.append(("latin", token))
    return segments


def synthesize(text, cjk_model, en_model, speed=1.0):
    """Synthesize mixed Chinese-English text. Returns (int16_audio, sample_rate)."""
    segments = split_mixed_text(text)

    config = SynthesisConfig(
        length_scale=1.0 / speed if speed > 0 else 1.0,
        noise_scale=0.667,
        noise_w_scale=0.8,
        volume=1.0,
    )

    results = []
    sample_rate = 22050
    has_cjk = any(st == "cjk" for st, _ in segments)
    has_latin = any(st == "latin" for st, _ in segments)

    for i, (st, seg) in enumerate(segments):
        seg = seg.strip()
        if not seg:
            continue

        if st == "cjk":
            model_name = cjk_model
            tag = "CJK"
        else:
            model_name = en_model
            tag = "LATIN"

        # If only one language present, still use the appropriate model
        if not has_cjk and st == "latin" and en_model is None:
            # No latin model specified, try CJK model
            model_name = cjk_model
        elif not has_latin and st == "cjk" and cjk_model is None:
            model_name = en_model

        onnx_path = MODELS_DIR / f"{model_name}.onnx"
        if not onnx_path.exists():
            print(f"  [!] Model {model_name} not found, skipping: {seg[:40]}...")
            continue

        voice = PiperVoice.load(str(onnx_path))
        chunks = list(voice.synthesize(seg, config))

        for ch in chunks:
            sr = ch.sample_rate
            if ch._audio_int16_array is not None:
                results.append(ch._audio_int16_array)
            elif ch.audio_float_array is not None:
                results.append((ch.audio_float_array * 32767).astype(np.int16))
            sample_rate = sr

        print(f"  [{tag}] {model_name}: {seg[:60]}{'...' if len(seg) > 60 else ''}")

    if not results:
        return None, sample_rate

    # 30ms silence between segments to prevent clicks
    silence = np.zeros(int(sample_rate * 0.03), dtype=np.int16)
    combined = results[0]
    for arr in results[1:]:
        combined = np.concatenate([combined, silence, arr])

    return combined, sample_rate


def write_wav(path, audio, sample_rate):
    """Write int16 numpy array as a WAV file."""
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())


def escape_drawtext(s):
    r"""Escape a string for ffmpeg drawtext filter: \ ' : %"""
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = s.replace(":", "\\:")
    s = s.replace("%", "\\%")
    return s


def generate_video(audio_path, title, output_path):
    """Generate a podcast video: dark bg + title + waveform + audio track."""
    safe_title = escape_drawtext(title)

    filter_complex = (
        # Dark background — 360p (640x360)
        f"color=c=0x0a0a1a:s=640x360,format=rgba[bg];"

        # Title text at top
        f"[bg]drawtext=fontfile='{FONT_PATH}':"
        f"text='{safe_title}':"
        f"fontcolor=0xffffff:fontsize=24:"
        f"x=(w-text_w)/2:y=25[bg_title];"

        # Waveform visualization from audio
        f"[0:a]showwaves=s=640x120:mode=line:"
        f"colors=0x00ffaa|0x00dd88:rate=30[v_wave];"

        # Overlay waveform on background
        f"[bg_title][v_wave]overlay=0:140[out]"
    )

    cmd = [
        "ffmpeg",
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-y",
        str(output_path),
    ]

    print("  Running ffmpeg...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        stderr_tail = result.stderr.strip()[-2000:] if result.stderr else "(no output)"
        print(f"  ffmpeg error:\n{stderr_tail}")
        raise RuntimeError(f"ffmpeg exited with code {result.returncode}")

    print(f"  [OK] Video saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Podcast Video Generator — 播客視頻生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python podcast.py --title "今日科技新聞" --content "今天我們來聊聊AI的發展..."
  python podcast.py --title "Daily News" --content "Today we discuss..." -o news.mp4
  python podcast.py --title "讀書心得" --content-file script.txt --speed 1.2
        """,
    )
    parser.add_argument("--title", required=True, help="播客標題")
    parser.add_argument("--content", default="", help="播客內容文字")
    parser.add_argument("--content-file", default="", help="從文字檔案讀取內容")
    parser.add_argument("--output", "-o", default="podcast_output.mp4", help="輸出視頻路徑 (預設: podcast_output.mp4)")
    parser.add_argument("--cjk-model", default=DEFAULT_CJK_MODEL, help=f"中文模型 (預設: {DEFAULT_CJK_MODEL})")
    parser.add_argument("--en-model", default=DEFAULT_EN_MODEL, help=f"英文模型 (預設: {DEFAULT_EN_MODEL})")
    parser.add_argument("--speed", type=float, default=1.0, help="語速 0.5-3.0 (預設: 1.0)")

    args = parser.parse_args()

    # Resolve content
    content = args.content
    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")

    if not content.strip():
        print("Error: 沒有提供內容。使用 --content 或 --content-file 指定。")
        sys.exit(1)

    title = args.title.strip()
    output_path = Path(args.output).resolve()

    print("=" * 50)
    print("  Podcast Video Generator")
    print("=" * 50)
    print(f"  Title:   {title}")
    print(f"  Content: {len(content)} chars")
    print(f"  Output:  {output_path}")
    print()

    # Step 1 — download models
    print("[1/3] Ensuring models are available...")
    ensure_model(args.cjk_model)
    ensure_model(args.en_model)
    print()

    # Step 2 — TTS synthesis
    print("[2/3] Synthesizing speech...")
    audio, sample_rate = synthesize(content, args.cjk_model, args.en_model, args.speed)
    if audio is None:
        print("Error: 語音合成失敗，沒有生成任何音頻。")
        sys.exit(1)

    duration = len(audio) / sample_rate
    print(f"  Total: {duration:.1f}s @ {sample_rate}Hz, {len(audio)} samples")
    print()

    # Step 3 — video generation
    print("[3/3] Generating podcast video...")
    tmp_wav = output_path.with_suffix(".wav.tmp")
    try:
        write_wav(tmp_wav, audio, sample_rate)
        generate_video(str(tmp_wav), title, str(output_path))
    finally:
        tmp_wav.unlink(missing_ok=True)

    print()
    print("=" * 50)
    print(f"  Done! -> {output_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
