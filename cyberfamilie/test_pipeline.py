import json
from pathlib import Path
from unittest.mock import patch
import pipeline

def test_plan_and_platforms():
    p = pipeline.plan_load()
    assert len(p['shots']) == 2
    assert len(pipeline.SOURCES) >= 12
    assert 'wan' in pipeline.AUTO and 'pixverse' not in pipeline.AUTO

def test_extract_path():
    assert pipeline.extract_result_path(({'video':{'path':'/x/foo.mp4'}},9)) == '/x/foo.mp4'
    assert pipeline.extract_result_path((None, {'video': None})) is None
    assert pipeline.extract_result_path('file.jpg') is None

def test_prepare():
    pipeline.prepare(pipeline.plan_load())
    assert (pipeline.ROOT/'handoff'/'shot_01_prompt.txt').exists()

def test_manual_provider_is_blocked():
    p = pipeline.plan_load()
    try:
        pipeline.call_public_provider('pixverse',p['shots'][0],pipeline.ref_path(p))
        assert False
    except ValueError:
        pass

def test_video_assemble_missing():
    p = pipeline.plan_load()
    try:
        pipeline.assemble(p)
        assert False
    except (RuntimeError, FileNotFoundError):
        pass

def test_status_not_fabricated():
    result = pipeline.status(pipeline.plan_load())
    assert result['publicatie_tiktok'] == 'uitgeschakeld'
    assert result['betaalde_generaties'] == 'uitgeschakeld'