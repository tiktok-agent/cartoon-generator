"""
ULTRA API TESTER v3 - Alle fixes toegepast
"""
import os, sys, time, json, shutil, requests
from datetime import datetime
from pathlib import Path

HF_TOKEN   = os.environ.get("HF_TOKEN", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
ZHIPU_KEY  = os.environ.get("ZHIPU_API_KEY", "")

PROMPT = (
    "three children holding hands in a moonlit flower meadow, "
    "giant full moon glowing, Studio Ghibli painterly style, "
    "soft magical lighting, dreamy illustration"
)

results = {}
Path("test_outputs").mkdir(exist_ok=True)

def ok(name, msg):
    results[name] = {"status": "WERKT", "msg": msg}
    print(f"  OK    {name}: {msg}")

def fail(name, msg):
    results[name] = {"status": "MISLUKT", "msg": msg}
    print(f"  FAIL  {name}: {msg}")

def skip(name, msg):
    results[name] = {"status": "OVERGESLAGEN", "msg": msg}
    print(f"  SKIP  {name}: {msg}")

def maak_test_afbeelding():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (512, 512), "#0a0a2e")
    d = ImageDraw.Draw(img)
    d.ellipse([100,50,400,350], fill="#d4d4d4")
    d.ellipse([100,380,200,460], fill="#ffcc99")
    d.ellipse([210,370,310,450], fill="#ffcc99")
    d.ellipse([320,380,420,460], fill="#ffcc99")
    p = "test_outputs/test_afbeelding.jpg"
    img.save(p)
    return p

# ── TEST 1: HF Inference API - NIEUW adres ─────────────────
def test_hf_flux():
    print("\n[1] HuggingFace FLUX - nieuw router adres")
    if not HF_TOKEN:
        skip("hf_flux", "Geen HF_TOKEN")
        return
    try:
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        # NIEUW adres na 410 fout
        models = [
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/stable-diffusion-xl-base-1.0",
            "CompVis/stable-diffusion-v1-4",
        ]
        for model in models:
            try:
                print(f"  Probeer: {model}")
                # Probeer nieuw router endpoint
                url = f"https://router.huggingface.co/hf-inference/models/{model}"
                r = requests.post(url,
                    headers=headers,
                    json={"inputs": PROMPT},
                    timeout=120
                )
                print(f"  HTTP {r.status_code}: {r.text[:100]}")
                if r.status_code == 200 and len(r.content) > 5000:
                    p = "test_outputs/hf_flux.jpg"
                    open(p,"wb").write(r.content)
                    ok("hf_flux", f"{model} - {len(r.content):,} bytes")
                    return
            except Exception as e:
                print(f"  Fout: {str(e)[:80]}")
        fail("hf_flux", "Alle modellen gefaald")
    except Exception as e:
        fail("hf_flux", str(e)[:120])

# ── TEST 2: LTX Video - gefixte image parameter ────────────
def test_ltx_video():
    print("\n[2] LTX Video - image-to-video (gefixte params)")
    if not HF_TOKEN:
        skip("ltx_video", "Geen HF_TOKEN")
        return
    try:
        from gradio_client import Client, handle_file

        img_path = "test_outputs/hf_flux.jpg"
        if not os.path.exists(img_path):
            img_path = maak_test_afbeelding()

        print(f"  Afbeelding: {img_path} ({os.path.getsize(img_path)} bytes)")

        client = Client(
            "DeepRat/LTX-Video-ZeroGPU-Optimized",
            headers={"Authorization": f"Bearer {HF_TOKEN}"}
        )

        # Exacte parameters van de API info die we zagen:
        result = client.predict(
            prompt=PROMPT,
            negative_prompt="worst quality, blurry, distorted",
            input_image_filepath=handle_file(img_path),  # dict met path
            input_video_filepath=None,
            height_ui=480,
            width_ui=272,
            mode="image-to-video",
            duration_ui=2,
            ui_frames_to_use=9,
            seed_ui=42,
            randomize_seed=False,
            ui_guidance_scale=1,
            improve_texture_flag=True,
            slow_motion_flag=False,
            api_name="/image_to_video"
        )

        print(f"  Resultaat type: {type(result)}")
        video = result[0] if isinstance(result,(list,tuple)) else result
        if isinstance(video, dict):
            video = video.get("video") or video.get("path")

        print(f"  Video pad: {video}")
        if video and os.path.exists(str(video)):
            p = "test_outputs/ltx_video.mp4"
            shutil.copy(str(video), p)
            ok("ltx_video", f"{os.path.getsize(p):,} bytes")
        else:
            fail("ltx_video", f"Geen geldig video bestand: {video}")

    except Exception as e:
        fail("ltx_video", str(e)[:200])

# ── TEST 3: CogVideoX - text-to-video (geen video nodig) ───
def test_cogvideox():
    print("\n[3] CogVideoX - text-to-video")
    if not HF_TOKEN:
        skip("cogvideox", "Geen HF_TOKEN")
        return
    try:
        from gradio_client import Client, handle_file

        img_path = "test_outputs/hf_flux.jpg"
        if not os.path.exists(img_path):
            img_path = maak_test_afbeelding()

        client = Client(
            "THUDM/CogVideoX-5B-Space",
            headers={"Authorization": f"Bearer {HF_TOKEN}"}
        )

        # API signature: prompt, image_input, video_input, video_strength, seed_value, scale_status, rife_status
        # video_input is required maar we geven een lege string
        result = client.predict(
            prompt=PROMPT,
            image_input=handle_file(img_path),
            video_input={"video": img_path, "subtitles": None},  # dummy
            video_strength=0.8,
            seed_value=42,
            scale_status=False,
            rife_status=False,
            api_name="/generate"
        )

        print(f"  Resultaat: {type(result)}, len={len(result) if isinstance(result,(list,tuple)) else 'n/a'}")
        video = result[0] if isinstance(result,(list,tuple)) else result
        if isinstance(video, dict):
            video = video.get("video") or video.get("path")

        if video and os.path.exists(str(video)):
            p = "test_outputs/cogvideox.mp4"
            shutil.copy(str(video), p)
            ok("cogvideox", f"{os.path.getsize(p):,} bytes")
        else:
            fail("cogvideox", f"Geen video: {video}")

    except Exception as e:
        fail("cogvideox", str(e)[:200])

# ── TEST 4: Gemini ─────────────────────────────────────────
def test_gemini():
    print("\n[4] Google Gemini - 500/dag gratis")
    if not GEMINI_KEY:
        skip("gemini", "Geen key - haal op: aistudio.google.com (GRATIS, geen creditcard)")
        return
    try:
        import base64
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key={GEMINI_KEY}"
        r = requests.post(url, json={
            "contents": [{"parts": [{"text": PROMPT}]}],
            "generationConfig": {"responseModalities": ["IMAGE"]}
        }, timeout=60)
        data = r.json()
        for part in data.get("candidates",[{}])[0].get("content",{}).get("parts",[]):
            if "inlineData" in part:
                img = base64.b64decode(part["inlineData"]["data"])
                p = "test_outputs/gemini.jpg"
                open(p,"wb").write(img)
                ok("gemini", f"{len(img):,} bytes")
                return
        fail("gemini", str(data)[:150])
    except Exception as e:
        fail("gemini", str(e)[:120])

# ── TEST 5: ZhipuAI ────────────────────────────────────────
def test_zhipu():
    print("\n[5] ZhipuAI CogVideoX - onbeperkt gratis")
    if not ZHIPU_KEY:
        skip("zhipu", "Geen key - haal op: bigmodel.cn (GRATIS, geen creditcard)")
        return
    try:
        headers = {"Authorization": f"Bearer {ZHIPU_KEY}", "Content-Type": "application/json"}
        r = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/videos/generations",
            headers=headers,
            json={"model": "cogvideox-flash", "prompt": PROMPT, "size": "1280x720", "duration": 5},
            timeout=30
        )
        data = r.json()
        print(f"  Response: {data}")
        task_id = data.get("id")
        if not task_id:
            fail("zhipu", f"Geen task_id: {data}")
            return
        for i in range(24):
            time.sleep(10)
            r2 = requests.get(
                f"https://open.bigmodel.cn/api/paas/v4/async-result/{task_id}",
                headers=headers
            )
            d2 = r2.json()
            status = d2.get("task_status")
            print(f"  [{i+1}] {status}")
            if status == "SUCCESS":
                url = d2.get("video_result",[{}])[0].get("url","")
                r3 = requests.get(url, timeout=60)
                p = "test_outputs/zhipu_video.mp4"
                open(p,"wb").write(r3.content)
                ok("zhipu", f"{os.path.getsize(p):,} bytes")
                return
            elif status in ["FAIL","REVOKED"]:
                fail("zhipu", str(d2))
                return
        fail("zhipu", "Timeout")
    except Exception as e:
        fail("zhipu", str(e)[:120])

# ── RAPPORT ────────────────────────────────────────────────
def rapport():
    print("\n" + "="*50)
    print("EINDRAPPORT v3")
    print("="*50)
    w = {k:v for k,v in results.items() if v["status"]=="WERKT"}
    m = {k:v for k,v in results.items() if v["status"]=="MISLUKT"}
    s = {k:v for k,v in results.items() if v["status"]=="OVERGESLAGEN"}
    print(f"\nWERKT ({len(w)}):")
    for k,v in w.items(): print(f"  OK  {k}: {v['msg']}")
    print(f"\nMISLUKT ({len(m)}):")
    for k,v in m.items(): print(f"  FAIL  {k}: {v['msg']}")
    print(f"\nOVERGESLAGEN ({len(s)}):")
    for k,v in s.items(): print(f"  SKIP  {k}: {v['msg']}")
    print(f"\nBESTANDEN:")
    for p in sorted(Path("test_outputs").iterdir()):
        if p.is_file():
            print(f"  {p.name} - {p.stat().st_size:,} bytes")
    json.dump({"tijd": datetime.now().isoformat(), "resultaten": results},
              open("test_outputs/rapport.json","w"), indent=2, ensure_ascii=False)
    print("="*50)

if __name__ == "__main__":
    print("="*50)
    print("ULTRA API TESTER v3")
    print(f"HF_TOKEN:   {'JA' if HF_TOKEN else 'NEE'}")
    print(f"GEMINI_KEY: {'JA' if GEMINI_KEY else 'NEE'}")
    print(f"ZHIPU_KEY:  {'JA' if ZHIPU_KEY else 'NEE'}")
    print("="*50)
    os.system(f"{sys.executable} -m pip install requests pillow gradio_client -q")
    test_hf_flux()
    test_ltx_video()
    test_cogvideox()
    test_gemini()
    test_zhipu()
    rapport()
