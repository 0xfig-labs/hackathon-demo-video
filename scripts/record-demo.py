#!/usr/bin/env python3
# /// script
# dependencies = ["playwright>=1.40", "Pillow>=10", "edge-tts>=6"]
# ///
"""
Hackathon demo video pipeline — record, narrate, subtitle, compose.

Usage:
  uv run record-demo.py <url> "<narration_text>" [--steps <steps_json>] [--voice <voice>]

Inputs:
  url            — Deployed project URL to demo
  narration_text — TTS + subtitle script (Chinese or English)
  --steps        — Optional JSON array of Playwright interaction steps
  --voice        — edge-tts voice ID (default: zh-CN-YunyangNeural)
  --outdir       — Output directory (default: ./demo/)

Output:
  {outdir}/{project-name}-demo-subtitled.mp4
"""

import argparse, json, os, subprocess, sys, math, re, shutil, uuid, atexit
from pathlib import Path


def req(cmd, **kw):
    """Run command, return (returncode, stdout, stderr)."""
    r = subprocess.run(
        cmd, capture_output=True, text=True, timeout=kw.pop("timeout", 300), **kw
    )
    return r.returncode, r.stdout, r.stderr


def ffprobe_dur(path):
    """Get video duration via ffprobe."""
    rc, out, _ = req(["ffprobe", "-v", "quiet", "-show_format", str(path)])
    if rc:
        return 0
    for l in out.split("\n"):
        if l.startswith("duration="):
            return float(l.split("=")[1])
    return 0


def fmt_srt(t):
    """Float seconds → SRT timestamp."""
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_size(value):
    m = re.fullmatch(r"(\d+)x(\d+)", value or "")
    if not m:
        raise argparse.ArgumentTypeError("expected WIDTHxHEIGHT, e.g. 1080x1920")
    return int(m.group(1)), int(m.group(2))


FORMATS = {"landscape": (1920, 1080), "portrait": (1080, 1920), "square": (1080, 1080)}
CAPTURES = {"desktop": (1920, 1080), "mobile": (390, 844), "tablet": (820, 1180)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Deployed project URL")
    parser.add_argument("narration", help="TTS narration text (Chinese/English)")
    parser.add_argument("--voice", default="zh-CN-YunyangNeural", help="edge-tts voice")
    parser.add_argument("--rate", default="+0%", help="TTS speed rate")
    parser.add_argument("--steps", default=None, help="JSON steps overrides")
    parser.add_argument("--outdir", default=None, help="Output directory")
    parser.add_argument("--output", default=None, help="Final MP4 path; avoids collisions in parallel runs")
    parser.add_argument("--format", choices=FORMATS, default="landscape", help="Output canvas")
    parser.add_argument("--capture", choices=CAPTURES, default=None, help="Browser viewport preset")
    parser.add_argument("--layout", choices=["native", "fit", "crop", "framed"], default="native", help="How recording fits output")
    parser.add_argument("--viewport", type=parse_size, default=None, help="Capture viewport WIDTHxHEIGHT")
    parser.add_argument("--output-size", type=parse_size, default=None, help="Output canvas WIDTHxHEIGHT")
    parser.add_argument("--preset", default="medium", help="ffmpeg x264 preset: faster = quicker, slower = smaller/better")
    parser.add_argument("--crf", default="20", help="ffmpeg x264 CRF: lower = better/larger")
    parser.add_argument("--wait-until", choices=["domcontentloaded", "load", "networkidle"], default="domcontentloaded", help="Playwright navigation wait strategy")
    parser.add_argument("--strict-steps", action=argparse.BooleanOptionalAction, default=True, help="Fail when a step cannot be performed")
    args = parser.parse_args()

    output_w, output_h = args.output_size or FORMATS[args.format]
    capture_mode = args.capture or ("mobile" if args.format == "portrait" else "desktop")
    capture_w, capture_h = args.viewport or CAPTURES[capture_mode]
    record_w, record_h = (output_w, output_h) if args.layout == "native" else (capture_w, capture_h)
    is_mobile = capture_mode == "mobile"

    # Determine output directory
    if args.outdir:
        out_dir = Path(args.outdir)
    else:
        out_dir = Path.cwd() / "demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    project_name = (
        re.sub(
            r"[^a-z0-9-]",
            "",
            args.url.split("//")[-1].split("/")[0].split(".")[0].lower(),
        )
        or "demo"
    )
    output_mp4 = Path(args.output) if args.output else out_dir / f"{project_name}-demo-subtitled.mp4"
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    # ponytail: per-run work dir prevents parallel runs from deleting/renaming each other's temp files.
    work_dir = out_dir / f".work-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    final_tmp = work_dir / "final.mp4"
    webm = work_dir / "recording.webm"
    audio = work_dir / "narration.mp3"
    vtt_file = work_dir / "subtitles.vtt"
    srt_file = work_dir / "subtitles.srt"
    subs_dir = work_dir / "subs"
    subs_dir.mkdir(parents=True, exist_ok=True)
    atexit.register(lambda: shutil.rmtree(work_dir, ignore_errors=True))

    print(f"\n{'=' * 40}")
    print(f"🎥 Hackathon Demo Video Pipeline")
    print(f"   URL: {args.url}")
    print(f"   Output: {output_mp4}")
    print(f"   Capture: {capture_mode} {capture_w}x{capture_h} → {args.format} {output_w}x{output_h} ({args.layout})")
    print(f"{'=' * 40}\n")

    # ── 1. Record with Python Playwright ──
    print("Step 1/5: Recording browser demo...")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("   ❌ Python Playwright missing. Install: python3 -m pip install playwright")
        print("      Optional browser install: python3 -m playwright install chromium")
        sys.exit(1)

    def launch_browser(pw):
        try:
            return pw.chromium.launch(headless=True)
        except Exception as first_error:
            for executable_path in [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]:
                if Path(executable_path).exists():
                    return pw.chromium.launch(executable_path=executable_path, headless=True)
            raise first_error

    def run_step(page, label, fn):
        try:
            fn()
        except Exception as e:
            if args.strict_steps:
                raise
            print(f"   ⚠️  SKIP_STEP:{label}:{str(e).splitlines()[0]}")

    context_options = {
        "viewport": {"width": capture_w, "height": capture_h},
        "is_mobile": is_mobile,
        "has_touch": is_mobile,
        "device_scale_factor": 1,
    }

    try:
        with sync_playwright() as pw:
            browser = launch_browser(pw)
            try:
                warmup_ctx = browser.new_context(**context_options)
                warmup_page = warmup_ctx.new_page()
                warmup_page.goto(args.url, wait_until=args.wait_until, timeout=45000)
                warmup_page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
                warmup_page.wait_for_timeout(2000)
                warmup_ctx.close()

                context = browser.new_context(
                    **context_options,
                    record_video_dir=str(work_dir),
                    record_video_size={"width": record_w, "height": record_h},
                )
                page = context.new_page()
                page.goto(args.url, wait_until=args.wait_until, timeout=45000)
                page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")

                steps = json.loads(args.steps) if args.steps else [
                    {"type": "click", "selector": "Fill example transaction", "wait": 1500},
                    {"type": "click", "selector": "Explain outcome", "wait": 0},
                    {"type": "wait_text", "selector": "OUTCOME EXPLANATION", "wait": 50000},
                    *[{"type": "scroll", "selector": str(y), "wait": 2000} for y in [400, 800, 1200, 1600]],
                ]

                for item in steps:
                    t = item.get("type", "click")
                    sel = item.get("selector", "")
                    wait = item.get("wait", 1000)
                    if t == "click":
                        run_step(page, f"click:{sel}", lambda sel=sel: page.get_by_role("button", name=sel).click())
                        page.wait_for_timeout(wait)
                    elif t == "fill":
                        value = item.get("value", "")
                        run_step(page, f"fill:{sel}", lambda sel=sel, value=value: page.locator(sel).fill(value))
                        page.wait_for_timeout(wait)
                    elif t == "link":
                        run_step(page, f"link:{sel}", lambda sel=sel: page.get_by_role("link", name=sel).click())
                        page.wait_for_timeout(wait)
                    elif t == "wait_text":
                        run_step(
                            page,
                            f"wait_text:{sel}",
                            lambda sel=sel, wait=wait: page.wait_for_function(
                                "text => document.body.innerText.includes(text)",
                                arg=sel,
                                timeout=max(wait, 10000),
                            ),
                        )
                        page.wait_for_timeout(2000)
                    elif t == "wait":
                        page.wait_for_timeout(max(wait, 1000))
                    elif t == "scroll":
                        page.evaluate("y => window.scrollTo(0, y)", int(sel))
                        page.wait_for_timeout(wait)

                video = page.video
                context.close()
                if video is None:
                    raise RuntimeError("Playwright did not create a video")
                shutil.move(video.path(), webm)
            finally:
                browser.close()
    except Exception as e:
        print(f"   ❌ Playwright error: {str(e)[:500]}")
        sys.exit(1)

    dur = ffprobe_dur(webm)
    print(f"   ✅ Recorded {dur:.0f}s ({webm.stat().st_size / 1024 / 1024:.1f}MB)")

    # ── 2. TTS Narration ──
    print("Step 2/5: Generating TTS narration...")
    rc, _, _ = req(
        [
            "edge-tts",
            "--voice",
            args.voice,
            "--rate",
            args.rate,
            "--text",
            args.narration,
            "--write-media",
            str(audio),
            "--write-subtitles",
            str(vtt_file),
        ],
        timeout=30,
    )
    if rc:
        print("   ❌ TTS failed")
        sys.exit(1)

    tts_dur = ffprobe_dur(audio)
    video_dur = dur
    print(f"   ✅ TTS: {tts_dur:.1f}s (voice: {args.voice.split('-')[-2]})")

    # ── 3. VTT → SRT ──
    print("Step 3/5: Generating subtitles...")
    with open(vtt_file) as f:
        blocks = f.read().strip().split("\n\n")

    def parse_vtt_time(t):
        parts = [float(x) for x in t.replace(",", ".").strip().split()[0].split(":")]
        return sum(v * m for v, m in zip(reversed(parts), [1, 60, 3600]))

    srt = ""
    idx = 1
    for block in blocks:
        lines = [line.strip() for line in block.strip().split("\n") if line.strip() and line.strip() != "WEBVTT"]
        time_i = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time_i is None or time_i + 1 >= len(lines):
            continue
        text = "\n".join(lines[time_i + 1 :]).strip()
        if not text:
            continue
        t = lines[time_i].split("-->")
        ss, ee = parse_vtt_time(t[0]), min(parse_vtt_time(t[1]), video_dur)
        if ee - ss < 0.3:
            continue
        srt += f"{idx}\n{fmt_srt(ss)} --> {fmt_srt(ee)}\n{text}\n\n"
        idx += 1

    with open(srt_file, "w") as f:
        f.write(srt)
    print(f"   ✅ {idx - 1} subtitle cues")

    # ── 4. Render subtitle overlay PNGs ──
    print("Step 4/5: Rendering subtitle overlays...")
    from PIL import Image, ImageDraw, ImageFont

    # Prefer CJK-capable font for Chinese, fallback otherwise
    font = None
    for fp, sz in [
        ("/System/Library/Fonts/STHeiti Medium.ttc", 34),
        ("/System/Library/Fonts/Helvetica.ttc", 34),
    ]:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, sz)
                break
            except:
                pass
    if font is None:
        font = ImageFont.load_default()

    with open(srt_file) as f:
        for block in f.read().strip().split("\n\n"):
            lines = block.split("\n")
            if len(lines) < 3:
                continue
            text = "\n".join(lines[2:]).strip()
            if not text:
                continue
            times = lines[1].split(" --> ")
            ss = sum(
                float(x) * m
                for x, m in zip(times[0].replace(",", ".").split(":"), [3600, 60, 1])
            )
            ee = sum(
                float(x) * m
                for x, m in zip(times[1].replace(",", ".").split(":"), [3600, 60, 1])
            )
            if ee - ss < 0.3:
                continue

            d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            max_text_w = max(320, output_w - 240)

            def text_w(line):
                box = d.textbbox((0, 0), line, font=font)
                return box[2] - box[0]

            def wrap_line(line):
                if text_w(line) <= max_text_w:
                    return [line]
                words = line.split(" ")
                if len(words) == 1:
                    rows, cur = [], ""
                    for ch in line:
                        if cur and text_w(cur + ch) > max_text_w:
                            rows.append(cur)
                            cur = ch
                        else:
                            cur += ch
                    return rows + ([cur] if cur else [])
                rows, cur = [], ""
                for word in words:
                    candidate = word if not cur else cur + " " + word
                    if cur and text_w(candidate) > max_text_w:
                        rows.append(cur)
                        cur = word
                    else:
                        cur = candidate
                return rows + ([cur] if cur else [])

            lt = [row for line in text.split("\n") for row in wrap_line(line)]
            line_heights = [d.textbbox((0, 0), l, font=font)[3] - d.textbbox((0, 0), l, font=font)[1] for l in lt]
            mw = min(output_w - 120, max(text_w(l) for l in lt) + 56)
            mh = sum(h + 8 for h in line_heights) + 32

            img = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
            dr = ImageDraw.Draw(img)
            dr.rounded_rectangle(
                [(0, 0), (mw - 1, mh - 1)], radius=16, fill=(0, 0, 0, 210)
            )
            y = 16
            for l, h in zip(lt, line_heights):
                dr.text((28, y), l, fill=(255, 255, 255, 255), font=font)
                y += h + 8

            img.save(os.path.join(subs_dir, f"s{lines[0].zfill(3)}.png"))

    # Intro dark overlay
    Image.new("RGB", (output_w, output_h), (25, 28, 35)).save(
        os.path.join(subs_dir, "_intro.png")
    )
    print(f"   ✅ Subtitle overlays rendered")

    # ── 5. ffmpeg Composite ──
    print("Step 5/5: Compositing final video...")
    subs_list = []
    with open(srt_file) as f:
        for block in f.read().strip().split("\n\n"):
            lines = block.split("\n")
            if len(lines) >= 3:
                t = lines[1].split(" --> ")
                ss = sum(
                    float(x) * m
                    for x, m in zip(t[0].replace(",", ".").split(":"), [3600, 60, 1])
                )
                ee = sum(
                    float(x) * m
                    for x, m in zip(t[1].replace(",", ".").split(":"), [3600, 60, 1])
                )
                p = os.path.join(subs_dir, f"s{lines[0].zfill(3)}.png")
                if os.path.exists(p) and ee - ss > 0.3:
                    subs_list.append((lines[0], ss, ee, p))

    inputs = [str(webm), os.path.join(subs_dir, "_intro.png"), str(audio)]
    for _, _, _, p in subs_list:
        inputs.append(p)

    target_dur = max(video_dur, tts_dur)
    if args.layout == "crop":
        base_filter = f"[0:v]scale={output_w}:{output_h}:force_original_aspect_ratio=increase,crop={output_w}:{output_h},setsar=1,tpad=stop_mode=clone:stop_duration={max(0, target_dur - video_dur):.3f}[v0]"
    elif args.layout in {"fit", "framed"}:
        base_filter = f"[0:v]scale={output_w}:{output_h}:force_original_aspect_ratio=decrease,pad={output_w}:{output_h}:(ow-iw)/2:(oh-ih)/2:color=0x191c23,setsar=1,tpad=stop_mode=clone:stop_duration={max(0, target_dur - video_dur):.3f}[v0]"
    else:
        base_filter = f"[0:v]scale={output_w}:{output_h},setsar=1,tpad=stop_mode=clone:stop_duration={max(0, target_dur - video_dur):.3f}[v0]"

    filters = [base_filter, "[v0][1:v]overlay=0:0:enable='between(t,0,1.5)'[base]"]
    last = "base"
    for i, (_, ss, ee, _) in enumerate(subs_list):
        filters.append(
            f"[{last}][{i + 3}:v]overlay=(W-w)/2:H-h-40:enable='between(t,{ss},{ee})'[o{i}]"
        )
        last = f"o{i}"

    cmd = ["ffmpeg", "-y"]
    for inp in inputs:
        cmd.extend(["-i", inp])
    cmd.extend(
        ["-filter_complex", ";".join(filters), "-map", f"[{last}]", "-map", "2:a"]
    )
    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            args.preset,
            "-crf",
            args.crf,
            "-profile:v",
            "high",
            "-pix_fmt",
            "yuv420p",
        ]
    )
    cmd.extend(["-c:a", "aac", "-b:a", "128k", "-shortest", str(final_tmp)])

    rc, _, err = req(cmd, timeout=180)
    if rc:
        print(f"   ❌ ffmpeg error: {err[-200:]}")
        sys.exit(1)

    shutil.move(final_tmp, output_mp4)
    sz = output_mp4.stat().st_size / 1024 / 1024
    print(
        f"   ✅ {output_mp4.name} ({sz:.0f}MB, {target_dur:.0f}s, {len(subs_list)} subtitles)"
    )

    # Cleanup
    shutil.rmtree(subs_dir, ignore_errors=True)
    for f in [webm, audio, vtt_file, srt_file]:
        if f.exists():
            f.unlink()

    print(f"\n✅ Done! Output: {output_mp4}")
    print(f'   Open with: open "{output_mp4}"')


if __name__ == "__main__":
    main()
