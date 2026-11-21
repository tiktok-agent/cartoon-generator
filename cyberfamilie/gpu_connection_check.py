#!/usr/bin/env python3
"""Read-only verification of public Hugging Face ZeroGPU API connectivity.
No GPU jobs, uploads, charges, logins, or silent retries.
"""
import argparse, json, os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

SPACE_CONFIG = (
    {'name':'Wan 2.2','id':'zerogpu-aoti/wan2-2-fp8da-aoti-faster','endpoint':'/generate_video'},
    {'name':'HunyuanVideo 1.5','id':'multimodalart/Hunyuan-Video-1-5','endpoint':'/generate'},
    {'name':'LTX-2.3','id':'Lightricks/LTX-2-3','endpoint':'/generate_video'},
)

def read_json(url, timeout=14):
    req=Request(url,headers={'User-Agent':'Cyberfamilie-Connectivity-Check/1.0','Accept':'application/json'})
    try:
        with urlopen(req,timeout=timeout) as response:
            data=response.read(400_000)
            if len(data)>=400_000: raise ValueError('API response is too large')
            return json.loads(data.decode('utf-8')),None
    except (HTTPError,URLError,OSError,ValueError) as error:
        return None,f'{type(error).__name__}: {str(error)[:190]}'

def host_from_metadata(meta,space_id):
    host=meta.get('host','')
    if isinstance(host,str) and host.endswith('.hf.space') and '/' not in host:
        return host
    return space_id.lower().replace('/','-')+'.hf.space'

def check(space,reader=read_json):
    sid=space['id']
    output={'name':space['name'],'space':sid,'endpoint':space['endpoint'],'space_url':'https://huggingface.co/spaces/'+sid,
        'metadata':'unverified','api_schema':'unverified','gpu_job_submitted':False,'image_uploaded':False,'billing':'none'}
    meta,err=reader('https://huggingface.co/api/spaces/'+quote(sid,safe='/'))
    if err or not isinstance(meta,dict):
        output.update(status='connection_failed',reason=err or 'Metadata is not JSON object')
        return output
    output['metadata']='reachable'
    runtime=meta.get('runtime') or {}
    output['stage']=runtime.get('stage','unknown') if isinstance(runtime,dict) else 'unknown'
    output['sdk']=meta.get('sdk',(meta.get('cardData') or {}).get('sdk'))
    output['api_info_url']='https://'+host_from_metadata(meta,sid)+'/gradio_api/info'
    schema,err=reader(output['api_info_url'])
    if err or not isinstance(schema,dict):
        output.update(status='metadata_only',reason=err or 'API schema is not JSON object')
        return output
    output['api_schema']='reachable'
    endpoints=schema.get('named_endpoints') or {}
    if not isinstance(endpoints,dict):
        output.update(status='schema_unexpected',reason='Missing named_endpoints map')
    elif space['endpoint'] in endpoints:
        output.update(status='api_endpoint_visible',reason='Endpoint published; GPU render not yet tested')
    else:
        output.update(status='api_endpoint_changed',reason='Expected endpoint missing',available_endpoints=list(endpoints)[:12])
    return output

def main(argv=None):
    parser=argparse.ArgumentParser(description='Read-only ZeroGPU public API connection test')
    parser.add_argument('--json',dest='jsonfile',type=Path)
    args=parser.parse_args(argv)
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'type':'read-only metadata/API check',
            'results':[check(s) for s in SPACE_CONFIG]}
    for item in report['results']:
        print(f"{item['name']}: {item['status']} ({item.get('reason','')})")
    if args.jsonfile:
        args.jsonfile.parent.mkdir(parents=True,exist_ok=True)
        args.jsonfile.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
            f.write('## Cyberfamilie – gratis GPU-API controles\n\n| Dienst | Status | API |\n|---|---|---|\n')
            for item in report['results']:
                f.write('| {} | {} | {} |\n'.format(item['name'],item['status'],item['endpoint']))
            f.write('\n*Alleen metadata en API-schema gecontroleerd; geen GPU-generatie en geen betaling.*\n')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
