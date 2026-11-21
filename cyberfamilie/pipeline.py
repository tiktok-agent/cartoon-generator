#!/usr/bin/env python3
"""Cyberfamilie: free-first multi-provider image-to-video producer.

Public, quota-limited Hugging Face ZeroGPU demos are the ONLY automated
providers. Other services can supply their videos through explicit import.
No subscriptions, payment, credential scraping, TikTok uploads or auto-publish.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
NEGATIVE = "still image, panning across photo, slow motion, stiff pose, morphing, distorted hands, extra limbs, skating feet, repeated mouth open-close, flicker"
SOURCES = {
    "wan": {
        "name": "Wan 2.2 · China / Hugging Face ZeroGPU",
        "space": "zerogpu-aoti/wan2-2-fp8da-aoti-faster", "api": "/generate_video",
        "url": "https://huggingface.co/spaces/zerogpu-aoti/wan2-2-fp8da-aoti-faster",
        "status": "automatisch, alleen publieke gratis quota",
    },
    "hunyuan": {
        "name": "HunyuanVideo 1.5 · China / Hugging Face ZeroGPU",
        "space": "multimodalart/Hunyuan-Video-1-5", "api": "/generate",
        "url": "https://huggingface.co/spaces/multimodalart/Hunyuan-Video-1-5",
        "status": "automatisch, alleen publieke gratis quota",
    },
    "ltx": {
        "name": "LTX-2.3 · Israël / Hugging Face ZeroGPU",
        "space": "Lightricks/LTX-2-3", "api": "/generate_video",
        "url": "https://huggingface.co/spaces/Lightricks/LTX-2-3",
        "status": "automatisch, alleen publieke gratis quota",
    },
    "viggle": {"name": "Viggle · Canada", "url": "https://viggle.ai/", "status": "handmatige website-export; ontwikkelaarssleutel/credits vereist voor API"},
    "vidu": {"name": "Vidu · China", "url": "https://www.vidu.com/", "status": "handmatige website-export; API is apart geprijsd"},
    "pixverse": {"name": "PixVerse · China", "url": "https://app.pixverse.ai/", "status": "handmatige website-export; webcredits zijn niet hetzelfde als API-credits"},
    "dreamina": {"name": "Dreamina / Seedance · China", "url": "https://dreamina.capcut.com/", "status": "handmatige website-export"},
    "kandinsky": {"name": "Kandinsky 6.0 / GigaChat · Rusland", "url": "https://giga.chat/", "status": "handmatige website-export; taal/licentie controleren"},
    "alice": {"name": "Alice AI / Yandex · Rusland", "url": "https://alice.yandex.ru/videogen", "status": "handmatige website-export"},
    "shotloom": {"name": "Shotloom · India", "url": "https://shotloom.ai/", "status": "handmatige website-export; eenmalige proefcredits"},
    "varya": {"name": "Varya AI · India", "url": "https://varya.avataar.ai/", "status": "handmatig; toegang niet gegarandeerd"},
    "animaker": {"name": "Animaker · India", "url": "https://www.animaker.com/", "status": "handmatige website-export; 2D en gratis watermerk"},
    "qwen": {"name": "Qwen · China", "url": "https://qwen.ai/", "status": "handmatig; actuele gratis exportquotum niet bevestigd"},
}
AUTO = ["wan", "hunyuan", "ltx"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def plan_load() -> dict:
    p = json.loads((ROOT / "filmplan.json").read_text(encoding="utf-8"))
    if not p.get("shots") or not isinstance(p.get("shots"), list):
        raise ValueError("filmplan.json mist shots")
    ids = [s["id"] for s in p["shots"]]
    if len(ids) != len(set(ids)) or any(not x.replace("_", "").isalnum() for x in ids):
        raise ValueError("Ongeldige / dubbele shot-ID")
    reference = (ROOT / p["bronbeeld"]).resolve()
    if not reference.is_file() or ROOT.resolve() not in reference.parents:
        raise FileNotFoundError("De referentieafbeelding ontbreekt of staat buiten de projectmap")
    return p


def ref_path(plan: dict) -> Path:
    return ROOT / plan["bronbeeld"]


def out_dir() -> Path:
    p = ROOT / "output"
    p.mkdir(parents=True, exist_ok=True)
    return p


def log_event(event: dict) -> None:
    p = out_dir() / "productie-log.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"tijd": now(), **event}, ensure_ascii=False) + "\n")


def ffprobe(path: Path) -> dict:
    if not shutil.which("ffprobe"):
        raise RuntimeError("FFprobe is niet geïnstalleerd")
    data = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                    "format=duration:stream=codec_type,width,height,nb_frames",
                                    "-of", "json", str(path)], text=True, timeout=40)
    result = json.loads(data)
    video = next((s for s in result.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise RuntimeError("Geen videostream gevonden")
    return {"duration": float(result["format"]["duration"]),
            "width": int(video["width"]), "height": int(video["height"]),
            "bytes": path.stat().st_size}


def validate_clip(path: Path, target_duration: float, check_motion: bool = True) -> dict:
    if not path.is_file() or path.stat().st_size < 4000:
        raise RuntimeError("Ontbrekend/leeg videobestand")
    result = ffprobe(path)
    if result["duration"] < max(1., min(2., target_duration * 0.5)):
        raise RuntimeError("Videoclip is te kort")
    if check_motion:
        # Quick visual movement check. Camera motion can fool it; manual QA remains necessary.
        try:
            import cv2
            cap = cv2.VideoCapture(str(path))
            count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            positions = [max(0, int((count - 1) * t)) for t in (.12, .32, .52, .72, .92)]
            frames = []
            for frame_no in positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                ok, frame = cap.read()
                if ok:
                    frames.append(cv2.cvtColor(cv2.resize(frame, (160, 90)), cv2.COLOR_BGR2GRAY))
            cap.release()
            if len(frames) > 1:
                import numpy as np
                changes = [float(np.mean(cv2.absdiff(frames[i], frames[i+1])))
                           for i in range(len(frames) - 1)]
                result["frame_change_mean"] = round(sum(changes) / len(changes), 2)
                if max(changes) < 1.2:
                    raise RuntimeError("Bijna stilstaand beeld, geen overtuigende animatie")
        except ImportError:
            result["motion_check"] = "niet beschikbaar: cv2 ontbreekt"
    return result


def extract_result_path(response: Any) -> str | None:
    if isinstance(response, str):
        if response.lower().split("?")[0].endswith((".mp4", ".mkv", ".mov", ".webm")):
            return response
    if isinstance(response, dict):
        for key in ("video", "path", "url", "name"):
            if key in response:
                x = extract_result_path(response[key])
                if x:
                    return x
    if isinstance(response, (tuple, list)):
        for x in response:
            video = extract_result_path(x)
            if video:
                return video
    return None


def call_public_provider(provider: str, shot: dict, reference: Path) -> Any:
    if provider not in AUTO:
        raise ValueError("Automatische kostenloze API alleen voor: " + ", ".join(AUTO))
    from gradio_client import Client, handle_file
    c = Client(SOURCES[provider]["space"], verbose=False)
    # gradio_client can return version-specific metadata in response; video must be verified.
    if provider == "wan":
        return c.predict(
            input_image=handle_file(str(reference)), prompt=shot["prompt"], steps=6,
            negative_prompt=NEGATIVE, duration_seconds=float(shot["duur_seconden"]),
            guidance_scale=1, guidance_scale_2=1,
            seed=23501, randomize_seed=False, api_name="/generate_video")
    if provider == "hunyuan":
        # UI takes frame count (61 frames ~ 2.5 sec @24fps), not duration seconds.
        frames = max(17, min(129, int(float(shot["duur_seconden"]) * 24 // 4) * 4 + 1))
        return c.predict(handle_file(str(reference)), shot["prompt"], frames,
                         6, 5.0, 23501, 1.0, False, api_name="/generate")
    # The official LTX-2.3 Space UI calls generate_video(image, prompt, seconds,
    # enhance_prompt, seed, randomize_seed, height, width).
    return c.predict(handle_file(str(reference)), shot["prompt"], float(shot["duur_seconden"]),
                     False, 23501, False, 768, 512, api_name="/generate_video")


def store_result(answer: Any, destination: Path) -> None:
    source = extract_result_path(answer)
    if not source:
        raise RuntimeError("De videoserver gaf geen bruikbaar videobestand terug")
    import urllib.parse
    if source.startswith("https://"):
        from urllib.request import urlopen
        parsed = urllib.parse.urlparse(source)
        if parsed.hostname not in ("huggingface.co", "cdn-lfs.hf.co") and not parsed.hostname.endswith(".hf.space"):
            raise RuntimeError("Onverwachte bestandsserver; veiligheidshalve geen download")
        with urlopen(source, timeout=150) as r, destination.open("wb") as f:
            shutil.copyfileobj(r, f, length=1024 * 1024)
    elif source.startswith("http://"):
        raise RuntimeError("Onveilige HTTP-download geblokkeerd")
    else:
        local = Path(source)
        if not local.is_file():
            raise RuntimeError("Het teruggegeven videobestand is niet lokaal beschikbaar")
        shutil.copyfile(local, destination)


def clip_path(shot_id: str) -> Path:
    return out_dir() / f"{shot_id}.mp4"


def do_render(plan: dict, provider: str, only_shot: str | None = None) -> int:
    if provider not in AUTO and provider != "auto":
        raise ValueError("Gebruik wan, hunyuan, ltx of auto; andere sites hebben geen gratis publieke API")
    candidates = AUTO if provider == "auto" else [provider]
    failures = []
    for shot in plan["shots"]:
        if only_shot and only_shot != shot["id"]:
            continue
        target = clip_path(shot["id"])
        if target.exists():
            try:
                info = validate_clip(target, shot["duur_seconden"])
                print(f"Bewaard: {target.name} ({info['duration']:.1f}s)")
                continue
            except Exception as e:
                print(f"Bestaande clip afgekeurd, blijft behouden voor controle: {e}")
                return 2
        succeeded = False
        for name in candidates:
            print(f"Render {shot['id']} via {name} (gratis publieke GPU-quota)...", flush=True)
            tmp = target.with_suffix(".incoming.mp4")
            try:
                answer = call_public_provider(name, shot, ref_path(plan))
                store_result(answer, tmp)
                info = validate_clip(tmp, shot["duur_seconden"])
                tmp.replace(target)
                log_event({"action": "render", "shot": shot["id"], "provider": name,
                           "status": "rendered", "file": target.name, **info})
                print(f"ECHTE VIDEO: {target}")
                succeeded = True
                break
            except Exception as e:
                tmp.unlink(missing_ok=True)
                error = f"{name}/{shot['id']}: {type(e).__name__}: {e}"
                failures.append(error)
                log_event({"action": "render", "shot": shot["id"], "provider": name,
                           "status": "failed", "reason": str(e)[:500]})
                print("MISLUKT: " + error, file=sys.stderr)
        if not succeeded:
            print("Geen betaalde fallback. Bekijk gratis webdiensten in handoff/.", file=sys.stderr)
            return 2
    print("Alle gekozen shots klaar. Gebruik: python pipeline.py assemble")
    return 0


def prepare(plan: dict) -> None:
    target = ROOT / "handoff"
    target.mkdir(exist_ok=True)
    lines = ["# CYBERFAMILIE — gratis handmatige video-export", "",
             "Gebruik de bestaande afbeelding: assets/neonfamilie.png", "",
             "Sla de twee ECHT gegenereerde video's op als output/shot_01.mp4 en output/shot_02.mp4.",
             "Geen nep-animatie, geen betaling en geen automatische TikTok-publicatie.", "",
             "## Platforms (handmatige aansluiting)"]
    for name, info in SOURCES.items():
        lines.append(f"- {info['name']}: {info['url']} — {info['status']}")
    for shot in plan["shots"]:
        lines += ["", f"## {shot['id']} — {shot['duur_seconden']} seconden", "", shot["prompt"], ""]
        (target / f"{shot['id']}_prompt.txt").write_text(shot["prompt"]+"\n", encoding="utf-8")
    (target / "PLATFORMS_EN_PROMPTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Koppelmap aangemaakt: {target}. Opgeslagen prompts voor {len(plan['shots'])} shots.")


def import_clip(shot_id: str, source: Path, plan: dict) -> None:
    match = next((s for s in plan["shots"] if s["id"] == shot_id), None)
    if match is None:
        raise ValueError("Onbekend shot-ID")
    if not source.is_file():
        raise FileNotFoundError(source)
    target = clip_path(shot_id)
    if source.resolve() == target.resolve():
        info = validate_clip(target, match["duur_seconden"])
        print("Clip al aanwezig, goedgekeurd:", info)
        return
    if target.exists():
        raise FileExistsError(f"{target} bestaat al; er wordt niets overschreven")
    temp = target.with_suffix(".incoming.mp4")
    try:
        shutil.copyfile(source, temp)
        info = validate_clip(temp, match["duur_seconden"])
        temp.replace(target)
        log_event({"action": "import", "shot": shot_id, "provider": "manual", **info})
    finally:
        temp.unlink(missing_ok=True)
    print("Videoclip geïmporteerd:", target)


def assemble(plan: dict) -> Path:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg en FFprobe zijn nodig voor het samenvoegen")
    clips = []
    for s in plan["shots"]:
        video = clip_path(s["id"])
        info = validate_clip(video, s["duur_seconden"])
        print(s["id"], "controle:", info)
        clips.append(video)
    normalized = []
    for s, clip in zip(plan["shots"], clips):
        name = out_dir() / f"norm_{s['id']}.mp4"
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(clip),
               "-vf", "fps=24,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1",
               "-c:v", "libx264", "-crf", "21", "-preset", "veryfast", "-pix_fmt", "yuv420p",
               "-an", "-t", str(float(s["duur_seconden"])), str(name)]
        subprocess.run(cmd, check=True, timeout=600)
        normalized.append(name)
    concat_file = out_dir() / "concat.txt"
    concat_file.write_text("".join("file '" + p.name + "'\n" for p in normalized), encoding="utf-8")
    dst = out_dir() / "Cyberfamilie_De_mysterieuze_knop.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(concat_file), "-c", "copy", "-movflags", "+faststart", str(dst)],
                   check=True, timeout=300)
    info = validate_clip(dst, sum(float(s["duur_seconden"]) for s in plan["shots"]))
    log_event({"action": "assemble", "status": "complete", **info, "file": dst.name})
    print("FILM KLAAR:", dst, info)
    return dst


def status(plan: dict) -> dict:
    details = []
    for shot in plan["shots"]:
        p = clip_path(shot["id"])
        try:
            v = validate_clip(p, shot["duur_seconden"])
            state = "video gecontroleerd"
        except Exception as e:
            state = "video ontbreekt" if not p.exists() else f"ONGELDIG: {e}"
            v = None
        details.append({"id": shot["id"], "status": state, "metadata": v})
    final = out_dir() / "Cyberfamilie_De_mysterieuze_knop.mp4"
    return {"film": plan["titel"], "provider_count": len(SOURCES),
            "automatische_gratis_providers": AUTO, "shots": details,
            "film_gemaakt": final.exists(), "publicatie_tiktok": "uitgeschakeld",
            "betaalde_generaties": "uitgeschakeld"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Cyberfamilie gratis filmproductiesysteem")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status", help="Bekijk aansluitingen en bestaande shots")
    sub.add_parser("prepare", help="Schrijf prompts en links voor alle platforms")
    render = sub.add_parser("render", help="Probeer gratis GPU-demos (geen betaalde APIs)")
    render.add_argument("--provider", choices=["auto"]+AUTO, default="auto")
    render.add_argument("--shot", default=None)
    imp = sub.add_parser("import", help="Importeer een via een andere dienst gerenderde video")
    imp.add_argument("--shot", required=True)
    imp.add_argument("--file", required=True, type=Path)
    sub.add_parser("assemble", help="Maak film van echte video-shots")
    args = parser.parse_args(argv)
    plan = plan_load()
    if args.action == "status":
        print(json.dumps(status(plan), indent=2, ensure_ascii=False))
        return 0
    if args.action == "prepare":
        prepare(plan)
        return 0
    if args.action == "render":
        if args.shot and args.shot not in [s["id"] for s in plan["shots"]]:
            parser.error("Onbekend shot")
        return do_render(plan, args.provider, args.shot)
    if args.action == "import":
        import_clip(args.shot, args.file, plan)
        return 0
    if args.action == "assemble":
        assemble(plan)
        return 0
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("STOP: " + str(exc), file=sys.stderr)
        sys.exit(2)