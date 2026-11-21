#!/usr/bin/env python3
"""Free-first global GPU scene dispatcher for Cyberfamilie.

A free GPU demo gives access to its application, not to its root GPU device.
Jobs here are independent scenes, never a fictional pooled VRAM device.

Safety: only 3 previously documented public Hugging Face ZeroGPU Gradio
endpoints are executable. Research/trial/paid providers are *catalog-only*.
No billing, signup, token scraping, card, SSH tunneling or unauthorized access.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pipeline

# Public source links are documented in GPU_WERELDWIJD.md.
CATALOG = [
    {"id":"huggingface_zerogpu","region":"International","free":"existing public Spaces with personal daily quotas","type":"public-demo","programmatic":"existing-public-gradio-only","url":"https://huggingface.co/docs/hub/spaces-zerogpu"},
    {"id":"kaggle","region":"US / international","free":"free GPU notebook quota, hardware and hours variable","type":"notebook","programmatic":"notebook under owner account and platform terms","url":"https://www.kaggle.com/docs/notebooks"},
    {"id":"modal","region":"US / international","free":"$30 monthly compute allowance, billable overage possible","type":"developer-credit","programmatic":"requires owner account and billing safeguard","url":"https://modal.com/pricing"},
    {"id":"alibaba_pai_dsw","region":"China","free":"new eligible users: 250 CU-hours/month for 3 months (~35.8 A10 GPU hours/month)","type":"one-time-trial","programmatic":"account/verified identity; can incur charges if not released","url":"https://help.aliyun.com/en/pai/product-overview/free-trial-guide"},
    {"id":"modelscope_xgpu","region":"China","free":"eligible developer programs and GPU hosting quotas","type":"qualified-program","programmatic":"account, eligibility and xGPU approval required","url":"https://www.modelscope.cn/posts/433641"},
    {"id":"amd_developer_cloud","region":"International","free":"$100 cloud credit subject to application approval","type":"developer-credit","programmatic":"account and AMD ROCm compatibility required","url":"https://www.amd.com/en/developer/resources/cloud-access/amd-developer-cloud.html"},
    {"id":"yotta_shakti_studio","region":"India","free":"INR 10000 trial credits advertised; eligibility to be confirmed","type":"one-time-trial","programmatic":"account required; project access not confirmed","url":"https://yotta.com/newsletter/yotta-spark-edition-aug-sep-2026/"},
    {"id":"indiaai_compute","region":"India","free":"subsidized/eligible institutional access; not general free GPU","type":"restricted-program","programmatic":"eligibility/approval required","url":"https://compute.indiaai.gov.in/eligibilitycriteria"},
    {"id":"selectel_ml","region":"Russia","free":"2-week ML platform trial advertised, access conditions unverified","type":"conditional-trial","programmatic":"account/approval; GPU included not guaranteed","url":"https://selectel.ru/services/gpu/"},
    {"id":"lightning_ai","region":"International","free":"5 complimentary starter credits and free CPU Studio","type":"developer-credit","programmatic":"account needed, credit/charges safeguard","url":"https://platform.lightning.ai/studio"},
    {"id":"paperspace_gradient","region":"International","free":"M4000 free notebook type, subject to availability","type":"notebook","programmatic":"account needed; retired legacy API endpoints","url":"https://docs.digitalocean.com/products/paperspace/pricing/"},
    {"id":"google_colab","region":"International","free":"limited, availability-based notebook GPU","type":"notebook","programmatic":"interactive notebook; no unattended remote execution bypass","url":"https://research.google.com/colaboratory/faq.html"},
    {"id":"ai_horde","region":"Europe / volunteers worldwide","free":"volunteer image and text generation (not general GPU access)","type":"volunteer-service","programmatic":"API for images and text; no verified video worker capability","url":"https://github.com/Haidra-org/AI-Horde"},
    {"id":"yandex_cloud","region":"Russia","free":"new client free trial unavailable and trial GPU quota zero","type":"not-free","programmatic":"disabled","url":"https://yandex.cloud/en/docs/getting-started/free-trial/concepts/limits"},
    {"id":"aws_sagemaker_studio_lab","region":"US / international","free":"free GPU only for existing accounts, registration closed 2026-07-30","type":"closed-to-new-users","programmatic":"disabled for new accounts","url":"https://docs.aws.amazon.com/sagemaker/latest/dg/studio-lab-overview.html"},
]
AUTO_VIDEO = tuple(pipeline.AUTO)  # wan, hunyuan, ltx — public Gradio demos only


def planned_jobs(plan: dict, providers: tuple[str, ...] = AUTO_VIDEO) -> list[dict]:
    if not providers or any(p not in AUTO_VIDEO for p in providers):
        raise ValueError("Alleen gratis publieke videodemos zijn uitvoerbaar: " + ", ".join(AUTO_VIDEO))
    result = []
    for index, shot in enumerate(plan["shots"]):
        destination = pipeline.clip_path(shot["id"])
        try:
            metadata = pipeline.validate_clip(destination, shot["duur_seconden"])
            status = "already_valid"
        except Exception:
            metadata = None
            status = "not_rendered"
        result.append({"shot_id": shot["id"], "duration": shot["duur_seconden"],
                       "provider": providers[index % len(providers)],
                       "status": status, "path": str(destination), "metadata": metadata})
    return result


def attempt_free_render(shot: dict, provider: str, plan: dict) -> dict:
    """One remote free-demo request, no retries, no paid fallback."""
    if provider not in AUTO_VIDEO:
        raise ValueError("Deze provider mag niet automatisch worden gebruikt")
    target = pipeline.clip_path(shot["id"])
    if target.exists():
        # Never overwrite an existing result, even if invalid.
        try:
            info = pipeline.validate_clip(target, shot["duur_seconden"])
            return {"shot": shot["id"], "provider": provider, "status": "already_valid", **info}
        except Exception as e:
            return {"shot": shot["id"], "provider": provider, "status": "blocked_existing_clip", "reason": str(e)}
    temp = target.with_suffix(".incoming.mp4")
    if temp.exists():
        return {"shot":shot["id"],"provider":provider,"status":"blocked_existing_temp"}
    try:
        reply = pipeline.call_public_provider(provider, shot, pipeline.ref_path(plan))
        pipeline.store_result(reply, temp)
        info = pipeline.validate_clip(temp, float(shot["duur_seconden"]))
        if target.exists():
            return {"shot": shot["id"], "provider": provider, "status": "blocked_existing_clip"}
        temp.replace(target)
        pipeline.log_event({"action":"gpu_pool_render","shot":shot["id"],"provider":provider,"status":"rendered","metadata":info})
        return {"shot":shot["id"],"provider":provider,"status":"rendered",**info}
    except Exception as e:
        pipeline.log_event({"action":"gpu_pool_render","shot":shot["id"],"provider":provider,"status":"failed","error":str(e)[:500]})
        return {"shot":shot["id"],"provider":provider,"status":"failed","error":f"{type(e).__name__}: {e}"}
    finally:
        temp.unlink(missing_ok=True)


def render_parallel(plan: dict, providers: tuple[str, ...], workers: int) -> dict:
    if workers < 1 or workers > 3:
        raise ValueError("Maximaal 3 gelijktijdige publieke demos om quota te respecteren")
    jobs = planned_jobs(plan, providers)
    shots = {s["id"]:s for s in plan["shots"]}
    results = []
    pending = [j for j in jobs if j["status"] != "already_valid"]
    # One request per distinct provider at a time: do not flood the shared demo.
    locks = {provider: Lock() for provider in providers}
    def serialize_per_provider(shot: dict, provider: str) -> dict:
        with locks[provider]:
            return attempt_free_render(shot, provider, plan)
    with ThreadPoolExecutor(max_workers=min(workers, len(providers))) as pool:
        futures = []
        for j in pending:
            futures.append(pool.submit(serialize_per_provider, shots[j["shot_id"]], j["provider"]))
        for future in as_completed(futures):
            results.append(future.result())
    already = [{"shot":j["shot_id"],"provider":j["provider"],"status":"already_valid"} for j in jobs if j["status"]=="already_valid"]
    return {"generated_at":datetime.now(timezone.utc).isoformat(),"mode":"parallel-independent-shots", "free_only":True,
            "ran":results + already,"paid_fallback":False,"total_shots":len(jobs)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Cyberfamilie — gratis GPU's in parallel per scène")
    parser.add_argument("action",choices=["catalog","plan","render-free-parallel"])
    parser.add_argument("--providers",default="wan,hunyuan",help="Komma-lijst van publieke gratis demos: wan,hunyuan,ltx")
    parser.add_argument("--workers",type=int,default=2)
    args = parser.parse_args(argv)
    if args.action == "catalog":
        print(json.dumps(CATALOG,ensure_ascii=False,indent=2));return 0
    providers = tuple(s.strip() for s in args.providers.split(",") if s.strip())
    plan = pipeline.plan_load()
    if args.action == "plan":
        print(json.dumps(planned_jobs(plan,providers),ensure_ascii=False,indent=2));return 0
    result = render_parallel(plan,providers,args.workers)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if all(j["status"] in ("rendered","already_valid") for j in result["ran"]) else 2


if __name__ == "__main__":
    sys.exit(main())