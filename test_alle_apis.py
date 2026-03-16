"""
ULTRA API TESTER v2 — Gefixte versie
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
    "soft magical lighting, dreamy illustration, vertical 9:16"
)

results = {}
Path("test_outputs").mkdir(exist_ok=True)

def ok(name, msg, **extra):
    results[name] = {"status": "WERKT", "msg": msg, **extra}
    print(f"  OK  {name}: {msg}")

def fail(name, msg):
    results[name] = {"status": "MISLUKT", "msg": msg}
    print(f"  FAIL  {name}: {msg}")

def skip(name, msg):
    results[name] = {"status": "OVERGESLAGEN", "msg": msg}
    print(f"  SKIP  {name}: {msg}")

def maak_test_afbeelding():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (480, 832), "#0a0a2e")
    d = ImageDraw.Draw(img)
    d.ellipse([100,80,380,360], fill="#d4d4d4")
    d.ellipse([150,560,230,640], fill="#ffcc99")
    d.ellipse([220,550,300,630], fill="#ffcc99")
    d.ellipse([290,560,370,640], fill="#ffcc99")
    p = "test_outputs/test_afbeelding.jpg"
    img.save(p)
    print(f"  Test afbeelding gemaakt: {p}")
    return p

def test_gemini():
    print("\n[1] Google Gemini Image - 500/dag gratis")
    if not GEMINI_KEY:
        skip("gemini", "Geen GEMINI_API_KEY - haal op: aistudio.google.com")
        return
    try:
        import base64
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key={GEMINI_KEY}"
        body = {
            "contents": [{"parts": [{"text": PROMPT}]}],
            "generationConfig": {"responseModalities": ["IMAGE"]}
        }
        r = requests.post(url, json=body, timeout=60)
        data = r.json()
        for part in data.get("candidates",[{}])[0].get("content",{}).get("parts",[]):
            if "inlineData" in part:
                img = base64.b64decode(part["inlineData"]["data"])
                p = "test_outputs/gemini.jpg"
                open(p,"wb").write(img)
                ok("gemini", f"{len(img):,} bytes")
                return
        fail("gemini", f"Geen afbeelding: {str(data)[:150]}")
    except Exception as e:
        fail("gemini", str(e)[:120])

def test_hf_flux_direct():
    print("\n[2] HuggingFace FLUX - directe inference API")
    if not HF_TOKEN:
        skip("hf_flux", "Geen HF_TOKEN")
        return
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        models = [
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/stable-diffusion-xl-base-1.0",
            "runwayml/stable-diffusion-v1-5",
        ]
        for model in models:
            try:
                print(f"  Probeer: {model}")
                url = f"https://api-inference.huggingface.co/models/{model}"
                r = requests.post(url,
                    headers=headers,
                    json={"inputs": PROMPT},
                    timeout=120
                )
                if r.status_code == 200 and len(r.content) > 5000:
                    p = "test_outputs/hf_flux.jpg"
                    open(p,"wb").write(r.content)
                    ok("hf_flux", f"{model} - {len(r.content):,} bytes")
                    return
                else:
                    print(f"  HTTP {r.status_code}: {r.text[:80]}")
            except Exception as e:
                print(f"  {model}: {str(e)[:80]}")
        fail("hf_flux", "Alle modellen gefaald")
    except Exception as e:
        fail("hf_flux", str(e)[:120])

def test_hf_video_gradio():
    print("\n[3] HF Video Space - Gradio (gefixte versie)")
    if not HF_TOKEN:
        skip("hf_video", "Geen HF_TOKEN")
        return
    try:
        from gradio_client import Client, handle_file

        img_path = "test_outputs/hf_flux.jpg"
        if not os.path.exists(img_path):
            img_path = maak_test_afbeelding()

        spaces = [
            "DeepRat/LTX-Video-ZeroGPU-Optimized",
            "THUDM/CogVideoX-5B-Space",
        ]
        hdr = {"Authorization": f"Bearer {HF_TOKEN}"}

        for space in spaces:
            try:
                print(f"  Probeer: {space}")
                client = Client(space, headers=hdr)

                # Gefixte manier om endpoints op te halen
                try:
                    info = client.view_api(return_format="dict")
                    named = list(info.get("named_endpoints", {}).keys())
                    unnamed = list(info.get("unnamed_endpoints", {}).keys())
                    endpoints = named + unnamed
                    print(f"  Endpoints: {endpoints[:4]}")
                except Exception as ep_err:
                    print(f"  Kon endpoints niet ophalen: {ep_err}")
                    endpoints = ["/predict"]

                api = "/image_to_video" if "/image_to_video" in endpoints else (endpoints[0] if endpoints else "/predict")

                result = client.predict(
                    handle_file(img_path),
                    PROMPT,
                    api_name=api
                )
                video = result[0] if isinstance(result,(list,tuple)) else result
                if isinstance(video,dict):
                    video = video.get("video") or video.get("path") or video.get("url")
                if video and os.path.exists(str(video)):
                    p = "test_outputs/hf_video.mp4"
                    shutil.copy(str(video), p)
                    ok("hf_video", f"{space} - {p}")
                    return
            except Exception as e:
                print(f"  {space}: {str(e)[:100]}")

        fail("hf_video", "Alle spaces gefaald")
    except Exception as e:
        fail("hf_video", str(e)[:120])

def test_zhipu():
    print("\n[4] ZhipuAI - CogVideoX-Flash (China, GRATIS onbeperkt)")
    if not ZHIPU_KEY:
        skip("zhipu", "Geen ZHIPU_API_KEY - gratis op: open.bigmodel.cn")
        return
    try:
        headers = {
            "Authorization": f"Bearer {ZHIPU_KEY}",
            "Content-Type": "application/json"
        }
        r = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/videos/generations",
            headers=headers,
            json={"model": "cogvideox-flash", "prompt": PROMPT, "size": "1080x1920", "duration": 5},
            timeout=30
        )
        data = r.json()
        task_id = data.get("id")
        if not task_id:
            fail("zhipu", f"Geen task_id: {data}")
            return

        print(f"  Task: {task_id} - wachten...")
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
                if url:
                    r3 = requests.get(url, timeout=60)
                    p = "test_outputs/zhipu_video.mp4"
                    open(p,"wb").write(r3.content)
                    ok("zhipu", f"CogVideoX-Flash - {p}")
                else:
                    fail("zhipu", "Geen URL")
                return
            elif status in ["FAIL","REVOKED"]:
                fail("zhipu", f"Gefaald: {d2}")
                return
        fail("zhipu", "Timeout")
    except Exception as e:
        fail("zhipu", str(e)[:120])

def rapport():
    print("\n" + "="*50)
    print("EINDRAPPORT")
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
    print(f"ULTRA API TESTER v2")
    print(f"HF_TOKEN:   {'JA' if HF_TOKEN else 'NEE'}")
    print(f"GEMINI_KEY: {'JA' if GEMINI_KEY else 'NEE'}")
    print(f"ZHIPU_KEY:  {'JA' if ZHIPU_KEY else 'NEE'}")
    print("="*50)
    os.system(f"{sys.executable} -m pip install requests pillow gradio_client -q")
    test_gemini()
    test_hf_flux_direct()
    test_hf_video_gradio()
    test_zhipu()
    rapport()
