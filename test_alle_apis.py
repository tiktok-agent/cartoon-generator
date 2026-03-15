"""
╔══════════════════════════════════════════════════════════════════╗
║   ULTRA AGRESSIEF API TESTER — ALLE LANDEN, ALLE SERVICES       ║
║   Test: Afbeelding + Video generatie APIs                        ║
║   Resultaat: rapport.json + rapport.txt                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, sys, time, json, shutil, traceback, requests
from datetime import datetime
from pathlib import Path

HF_TOKEN      = os.environ.get("HF_TOKEN", "")
GEMINI_KEY    = os.environ.get("GEMINI_API_KEY", "")
ZHIPU_KEY     = os.environ.get("ZHIPU_API_KEY", "")     # 智谱 CogVideoX
DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY", "") # Alibaba Wan2.1

GHIBLI_PROMPT = (
    "three children holding hands in a moonlit flower meadow, "
    "giant full moon glowing, Studio Ghibli painterly style, "
    "soft magical lighting, hayao miyazaki inspired, "
    "vertical portrait 9:16, dreamy illustration"
)

results = {}
Path("test_outputs").mkdir(exist_ok=True)

def log(msg): print(f"  {msg}", flush=True)
def ok(name, msg, **extra):
    results[name] = {"status": "✅ WERKT", "msg": msg, **extra}
    print(f"  ✅ {name}: {msg}")
def fail(name, msg):
    results[name] = {"status": "❌ MISLUKT", "msg": msg}
    print(f"  ❌ {name}: {msg}")
def skip(name, msg):
    results[name] = {"status": "⏭️  OVERGESLAGEN", "msg": msg}
    print(f"  ⏭️  {name}: {msg}")

# ════════════════════════════════════════════════════════════
# BLOK 1 — AFBEELDING APIS (gratis, geen key)
# ════════════════════════════════════════════════════════════

def test_pollinations_flux():
    print("\n🌸 [1/10] Pollinations.AI — FLUX (Berlijn, DE)")
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(GHIBLI_PROMPT)}?model=flux&width=480&height=832&seed=42&nologo=true"
        r = requests.get(url, timeout=90)
        if r.status_code == 200 and len(r.content) > 5000:
            path = "test_outputs/pollinations_flux.jpg"
            with open(path, "wb") as f: f.write(r.content)
            ok("pollinations_flux", f"{len(r.content):,} bytes → {path}", url=url)
        else:
            fail("pollinations_flux", f"HTTP {r.status_code}, {len(r.content)} bytes")
    except Exception as e:
        fail("pollinations_flux", str(e)[:120])

def test_pollinations_turbo():
    print("\n⚡ [2/10] Pollinations.AI — Turbo model")
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(GHIBLI_PROMPT)}?model=turbo&width=480&height=832&seed=42&nologo=true"
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 5000:
            path = "test_outputs/pollinations_turbo.jpg"
            with open(path, "wb") as f: f.write(r.content)
            ok("pollinations_turbo", f"{len(r.content):,} bytes → {path}", url=url)
        else:
            fail("pollinations_turbo", f"HTTP {r.status_code}")
    except Exception as e:
        fail("pollinations_turbo", str(e)[:120])

def test_gemini_image():
    print("\n🔷 [3/10] Google Gemini 2.5 Flash Image — 500/dag gratis (USA)")
    if not GEMINI_KEY:
        skip("gemini_image", "Geen GEMINI_API_KEY — haal gratis op via aistudio.google.com")
        return
    try:
        import base64
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-04-17:generateContent?key={GEMINI_KEY}"
        body = {
            "contents": [{"parts": [{"text": GHIBLI_PROMPT}]}],
            "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
        }
        r = requests.post(url, json=body, timeout=60)
        data = r.json()
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                img = base64.b64decode(part["inlineData"]["data"])
                path = "test_outputs/gemini_image.jpg"
                with open(path, "wb") as f: f.write(img)
                ok("gemini_image", f"{len(img):,} bytes → {path}", quota="500/dag gratis")
                return
        fail("gemini_image", f"Geen afbeelding in response: {str(data)[:200]}")
    except Exception as e:
        fail("gemini_image", str(e)[:120])

def test_hf_flux_space():
    print("\n🤗 [4/10] HuggingFace Space — FLUX.1-schnell (USA/Global)")
    if not HF_TOKEN:
        skip("hf_flux_space", "Geen HF_TOKEN — gratis account op huggingface.co")
        return
    try:
        from gradio_client import Client
        spaces = [
            "black-forest-labs/FLUX.1-schnell",
            "multimodalart/FLUX.1-merged",
            "ByteDance/SDXL-Lightning",
        ]
        hdr = {"Authorization": f"Bearer {HF_TOKEN}"}
        for space in spaces:
            try:
                log(f"Probeer: {space}")
                client = Client(space, headers=hdr)
                ep = [e.api_name for e in client.endpoints]
                log(f"Endpoints: {ep[:3]}")
                result = client.predict(
                    prompt=GHIBLI_PROMPT,
                    api_name=ep[0] if ep else "/predict"
                )
                img = result[0] if isinstance(result, (list,tuple)) else result
                if isinstance(img, dict): img = img.get("path") or img.get("url")
                if img and os.path.exists(str(img)):
                    path = "test_outputs/hf_flux.jpg"
                    shutil.copy(str(img), path)
                    ok("hf_flux_space", f"Space: {space} → {path}")
                    return
            except Exception as e:
                log(f"  ❌ {space}: {str(e)[:80]}")
        fail("hf_flux_space", "Alle spaces gefaald")
    except ImportError:
        fail("hf_flux_space", "gradio_client niet geïnstalleerd")
    except Exception as e:
        fail("hf_flux_space", str(e)[:120])

# ════════════════════════════════════════════════════════════
# BLOK 2 — VIDEO APIS
# ════════════════════════════════════════════════════════════

def test_cogvideox_hf():
    print("\n🇨🇳 [5/10] CogVideoX I2V — ZhipuAI open source (China/HuggingFace)")
    if not HF_TOKEN:
        skip("cogvideox_hf", "Geen HF_TOKEN nodig maar helpt — probeer toch")
    try:
        from gradio_client import Client, handle_file

        # Zorg dat er een testafbeelding is
        img_path = "test_outputs/pollinations_flux.jpg"
        if not os.path.exists(img_path):
            img_path = _maak_test_afbeelding()

        spaces = [
            "THUDM/CogVideoX-5B-Space",
            "THUDM/CogVideoX2.0-Space",
            "Nymbo/CogVideoX-5B",
        ]
        hdr = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        for space in spaces:
            try:
                log(f"Probeer: {space}")
                client = Client(space, headers=hdr)
                ep = [e.api_name for e in client.endpoints]
                log(f"Endpoints: {ep[:3]}")
                result = client.predict(
                    prompt=GHIBLI_PROMPT,
                    image=handle_file(img_path),
                    api_name="/generate_video" if "/generate_video" in ep else ep[0]
                )
                video = result[0] if isinstance(result,(list,tuple)) else result
                if isinstance(video, dict): video = video.get("video") or video.get("path")
                if video and os.path.exists(str(video)):
                    path = "test_outputs/cogvideox.mp4"
                    shutil.copy(str(video), path)
                    ok("cogvideox_hf", f"Space: {space} → {path}", licentie="Apache 2.0")
                    return
            except Exception as e:
                log(f"  ❌ {space}: {str(e)[:100]}")
        fail("cogvideox_hf", "Alle CogVideoX spaces gefaald")
    except ImportError:
        fail("cogvideox_hf", "gradio_client niet geïnstalleerd")
    except Exception as e:
        fail("cogvideox_hf", str(e)[:120])

def test_ltx_video_hf():
    print("\n🇮🇱 [6/10] LTX Video — Lightricks (Israël/HuggingFace)")
    if not HF_TOKEN:
        skip("ltx_video", "Geen HF_TOKEN — gratis account op huggingface.co")
        return
    try:
        from gradio_client import Client, handle_file
        img_path = "test_outputs/pollinations_flux.jpg"
        if not os.path.exists(img_path): img_path = _maak_test_afbeelding()

        spaces = [
            "Lightricks/LTX-Video",
            "multimodalart/ltx-video",
            "DeepRat/LTX-Video-ZeroGPU-Optimized",
        ]
        hdr = {"Authorization": f"Bearer {HF_TOKEN}"}
        for space in spaces:
            try:
                log(f"Probeer: {space}")
                client = Client(space, headers=hdr)
                ep = [e.api_name for e in client.endpoints]
                result = client.predict(
                    prompt=GHIBLI_PROMPT,
                    negative_prompt="ugly, blurry, distorted",
                    input_image_filepath=handle_file(img_path),
                    input_video_filepath=None,
                    height_ui=480, width_ui=272,
                    mode="image-to-video",
                    duration_ui=3,
                    ui_frames_to_use=13,
                    seed_ui=42,
                    randomize_seed=False,
                    ui_guidance_scale=1.0,
                    improve_texture_flag=True,
                    slow_motion_flag=False,
                    api_name="/image_to_video"
                )
                video = result[0]
                if isinstance(video, dict): video = video.get("video") or video.get("path")
                if video and os.path.exists(str(video)):
                    path = "test_outputs/ltx_video.mp4"
                    shutil.copy(str(video), path)
                    ok("ltx_video", f"Space: {space} → {path}")
                    return
            except Exception as e:
                log(f"  ❌ {space}: {str(e)[:100]}")
        fail("ltx_video", "Alle LTX spaces gefaald")
    except Exception as e:
        fail("ltx_video", str(e)[:120])

def test_wan21_hf():
    print("\n🇨🇳 [7/10] Wan2.1 — Alibaba open source (China/HuggingFace)")
    if not HF_TOKEN:
        skip("wan21_hf", "Geen HF_TOKEN")
        return
    try:
        from gradio_client import Client, handle_file
        img_path = "test_outputs/pollinations_flux.jpg"
        if not os.path.exists(img_path): img_path = _maak_test_afbeelding()

        spaces = [
            "Wan-AI/Wan2.1-I2V-14B-720P-Gradio",
            "multimodalart/wan-2.1",
            "alibaba-pai/EasyAnimate-I2V",
        ]
        hdr = {"Authorization": f"Bearer {HF_TOKEN}"}
        for space in spaces:
            try:
                log(f"Probeer: {space}")
                client = Client(space, headers=hdr)
                ep = [e.api_name for e in client.endpoints]
                log(f"Endpoints: {ep[:3]}")
                result = client.predict(
                    prompt=GHIBLI_PROMPT,
                    image=handle_file(img_path),
                    api_name=ep[0]
                )
                video = result[0] if isinstance(result,(list,tuple)) else result
                if isinstance(video, dict): video = video.get("video") or video.get("path")
                if video and os.path.exists(str(video)):
                    path = "test_outputs/wan21.mp4"
                    shutil.copy(str(video), path)
                    ok("wan21_hf", f"Space: {space} → {path}", licentie="Apache 2.0")
                    return
            except Exception as e:
                log(f"  ❌ {space}: {str(e)[:100]}")
        fail("wan21_hf", "Alle Wan2.1 spaces gefaald")
    except Exception as e:
        fail("wan21_hf", str(e)[:120])

def test_hunyuan_hf():
    print("\n🇨🇳 [8/10] HunyuanVideo — Tencent open source (China/HuggingFace)")
    if not HF_TOKEN:
        skip("hunyuan_hf", "Geen HF_TOKEN")
        return
    try:
        from gradio_client import Client, handle_file
        img_path = "test_outputs/pollinations_flux.jpg"
        if not os.path.exists(img_path): img_path = _maak_test_afbeelding()

        spaces = [
            "tencent/HunyuanVideo",
            "Tencent-Hunyuan/HunyuanVideo",
        ]
        hdr = {"Authorization": f"Bearer {HF_TOKEN}"}
        for space in spaces:
            try:
                log(f"Probeer: {space}")
                client = Client(space, headers=hdr)
                ep = [e.api_name for e in client.endpoints]
                result = client.predict(
                    prompt=GHIBLI_PROMPT,
                    api_name=ep[0]
                )
                video = result[0] if isinstance(result,(list,tuple)) else result
                if isinstance(video, dict): video = video.get("video") or video.get("path")
                if video and os.path.exists(str(video)):
                    path = "test_outputs/hunyuan.mp4"
                    shutil.copy(str(video), path)
                    ok("hunyuan_hf", f"Space: {space} → {path}")
                    return
            except Exception as e:
                log(f"  ❌ {space}: {str(e)[:100]}")
        fail("hunyuan_hf", "Alle HunyuanVideo spaces gefaald")
    except Exception as e:
        fail("hunyuan_hf", str(e)[:120])

def test_zhipu_cogvideox_api():
    print("\n🇨🇳 [9/10] ZhipuAI CogVideoX API — directe API (China)")
    if not ZHIPU_KEY:
        skip("zhipu_api", "Geen ZHIPU_API_KEY — gratis op open.bigmodel.cn")
        return
    try:
        # ZhipuAI heeft een officiele Python SDK
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=ZHIPU_KEY)
        response = client.videos.generations(
            model="cogvideox-flash",
            prompt=GHIBLI_PROMPT,
            quality="quality",
            with_audio=False,
            size="1080x1920",
            duration=5,
        )
        task_id = response.id
        log(f"Task ID: {task_id} — wachten op resultaat...")

        for i in range(30):
            time.sleep(10)
            result = client.videos.retrieve_videos_result(id=task_id)
            log(f"  Status: {result.task_status}")
            if result.task_status == "SUCCESS":
                video_url = result.video_result[0].url
                r = requests.get(video_url, timeout=60)
                path = "test_outputs/zhipu_cogvideox.mp4"
                with open(path, "wb") as f: f.write(r.content)
                ok("zhipu_api", f"CogVideoX-Flash → {path}", url=video_url)
                return
            elif result.task_status == "FAIL":
                fail("zhipu_api", f"Taak gefaald: {result}")
                return

        fail("zhipu_api", "Timeout na 5 minuten")
    except ImportError:
        fail("zhipu_api", "pip install zhipuai nodig")
    except Exception as e:
        fail("zhipu_api", str(e)[:120])

def test_minimax_api():
    print("\n🇨🇳 [10/10] MiniMax Hailuo API — starter gratis (China)")
    minimax_key = os.environ.get("MINIMAX_API_KEY", "")
    if not minimax_key:
        skip("minimax_api", "Geen MINIMAX_API_KEY — gratis starter op intl.minimaxi.com (3 video's)")
        return
    try:
        img_path = "test_outputs/pollinations_flux.jpg"
        if not os.path.exists(img_path): img_path = _maak_test_afbeelding()

        import base64
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # Submit job
        headers = {"Authorization": f"Bearer {minimax_key}", "Content-Type": "application/json"}
        body = {
            "model": "I2V-01",
            "first_frame_image": f"data:image/jpeg;base64,{img_b64}",
            "prompt": GHIBLI_PROMPT,
        }
        r = requests.post("https://api.minimaxi.com/v1/video_generation", json=body, headers=headers, timeout=30)
        data = r.json()
        task_id = data.get("task_id")
        if not task_id:
            fail("minimax_api", f"Geen task_id: {data}")
            return

        log(f"Task ID: {task_id} — wachten...")
        for _ in range(30):
            time.sleep(10)
            r2 = requests.get(f"https://api.minimaxi.com/v1/query/video_generation?task_id={task_id}", headers=headers)
            d2 = r2.json()
            status = d2.get("status")
            log(f"  Status: {status}")
            if status == "Success":
                video_url = d2["file_id"]
                r3 = requests.get(f"https://api.minimaxi.com/v1/files/retrieve?file_id={video_url}", headers=headers)
                dl_url = r3.json().get("file", {}).get("download_url")
                r4 = requests.get(dl_url, timeout=60)
                path = "test_outputs/minimax_hailuo.mp4"
                with open(path, "wb") as f: f.write(r4.content)
                ok("minimax_api", f"Hailuo I2V → {path}")
                return
            elif status in ["Fail", "Unknown"]:
                fail("minimax_api", f"Status: {status}")
                return

        fail("minimax_api", "Timeout")
    except Exception as e:
        fail("minimax_api", str(e)[:120])

# ════════════════════════════════════════════════════════════
# HELPER
# ════════════════════════════════════════════════════════════

def _maak_test_afbeelding():
    """Maak een minimale test-afbeelding met PIL als er geen API-afbeelding is."""
    from PIL import Image, ImageDraw
    W, H = 480, 832
    img = Image.new("RGB", (W, H), "#0a0a2e")
    draw = ImageDraw.Draw(img)
    draw.ellipse([100, 80, 380, 360], fill="#d4d4d4")   # maan
    draw.ellipse([160, 560, 240, 640], fill="#ffcc99")   # kind 1
    draw.ellipse([220, 550, 300, 630], fill="#ffcc99")   # kind 2
    draw.ellipse([280, 560, 360, 640], fill="#ffcc99")   # kind 3
    path = "test_outputs/test_fallback.jpg"
    img.save(path)
    log(f"Fallback afbeelding gemaakt: {path}")
    return path

# ════════════════════════════════════════════════════════════
# RAPPORT
# ════════════════════════════════════════════════════════════

def genereer_rapport():
    print("\n" + "═"*60)
    print("📊 EINDRAPPORT")
    print("═"*60)

    werkend   = {k:v for k,v in results.items() if "✅" in v["status"]}
    mislukt   = {k:v for k,v in results.items() if "❌" in v["status"]}
    geslaagd  = {k:v for k,v in results.items() if "⏭️" in v["status"]}

    print(f"\n✅ WERKEND ({len(werkend)}):")
    for k, v in werkend.items():
        print(f"   {k}: {v['msg']}")

    print(f"\n❌ MISLUKT ({len(mislukt)}):")
    for k, v in mislukt.items():
        print(f"   {k}: {v['msg']}")

    print(f"\n⏭️  OVERGESLAGEN ({len(geslaagd)}) — key ontbreekt:")
    for k, v in geslaagd.items():
        print(f"   {k}: {v['msg']}")

    # Sla op als JSON
    rapport = {
        "timestamp": datetime.now().isoformat(),
        "samenvatting": {
            "werkend": len(werkend),
            "mislukt": len(mislukt),
            "overgeslagen": len(geslaagd),
        },
        "resultaten": results
    }
    with open("test_outputs/rapport.json", "w") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)

    # Sla op als leesbare tekst
    with open("test_outputs/rapport.txt", "w") as f:
        f.write(f"RAPPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("="*60 + "\n\n")
        f.write(f"✅ WERKEND ({len(werkend)}):\n")
        for k,v in werkend.items(): f.write(f"  {k}: {v['msg']}\n")
        f.write(f"\n❌ MISLUKT ({len(mislukt)}):\n")
        for k,v in mislukt.items(): f.write(f"  {k}: {v['msg']}\n")
        f.write(f"\n⏭️  OVERGESLAGEN ({len(geslaagd)}):\n")
        for k,v in geslaagd.items(): f.write(f"  {k}: {v['msg']}\n")
        f.write(f"\nBESTANDEN IN test_outputs/:\n")
        for p in sorted(Path("test_outputs").iterdir()):
            if p.is_file():
                f.write(f"  {p.name} ({p.stat().st_size:,} bytes)\n")

    print(f"\n📁 Alle output in: test_outputs/")
    print(f"📄 rapport.json + rapport.txt opgeslagen")
    print("═"*60)


# ════════════════════════════════════════════════════════════
# MAIN — voer alles uit
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   ULTRA AGRESSIEF API TESTER — START                    ║")
    print(f"║   Tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                              ║")
    print(f"║   HF_TOKEN:      {'✅ aanwezig' if HF_TOKEN else '❌ ontbreekt'}                     ║")
    print(f"║   GEMINI_KEY:    {'✅ aanwezig' if GEMINI_KEY else '❌ ontbreekt'}                     ║")
    print(f"║   ZHIPU_KEY:     {'✅ aanwezig' if ZHIPU_KEY else '❌ ontbreekt'}                     ║")
    print(f"║   DASHSCOPE_KEY: {'✅ aanwezig' if DASHSCOPE_KEY else '❌ ontbreekt'}                     ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # Installeer dependencies
    print("\n📦 Dependencies installeren...")
    os.system(f"{sys.executable} -m pip install requests pillow gradio_client -q")

    # ── AFBEELDING TESTS ──
    print("\n" + "─"*60)
    print("🎨 BLOK 1 — AFBEELDING GENERATIE")
    print("─"*60)
    test_pollinations_flux()
    test_pollinations_turbo()
    test_gemini_image()
    test_hf_flux_space()

    # ── VIDEO TESTS ──
    print("\n" + "─"*60)
    print("🎬 BLOK 2 — VIDEO GENERATIE (image-to-video)")
    print("─"*60)
    test_cogvideox_hf()
    test_ltx_video_hf()
    test_wan21_hf()
    test_hunyuan_hf()
    test_zhipu_cogvideox_api()
    test_minimax_api()

    # ── RAPPORT ──
    genereer_rapport()
