#!/usr/bin/env python3
"""One-off anonymous free Wan ZeroGPU render with a synthetic image only.
No original character artwork, user secrets, tokens, retries, or paid API.
"""
import shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw

def synthetic_image(path):
    im=Image.new('RGB',(512,768),(19,26,49))
    d=ImageDraw.Draw(im)
    d.rectangle((0,585,512,768),fill=(39,67,100))
    d.ellipse((135,165,370,410),fill=(225,175,70),outline=(30,30,35),width=5)
    d.ellipse((192,260,210,280),fill=(14,18,32))
    d.ellipse((293,260,311,280),fill=(14,18,32))
    d.arc((206,270,301,346),start=10,end=170,fill=(40,25,35),width=6)
    d.rectangle((205,405,295,610),fill=(10,150,210))
    d.line((205,440,150,520),fill=(225,175,70),width=22)
    d.line((295,440,352,516),fill=(225,175,70),width=22)
    d.line((226,610,210,714),fill=(225,175,70),width=26)
    d.line((275,610,290,714),fill=(225,175,70),width=26)
    im.save(path)

def video_path(obj):
    if isinstance(obj,str) and obj.lower().split('?')[0].endswith(('.mp4','.webm','.mov')):return obj
    if isinstance(obj,(list,tuple)):
        for x in obj:
            v=video_path(x)
            if v:return v
    if isinstance(obj,dict):
        for k in ('path','video','name','url'):
            if k in obj:
                v=video_path(obj[k])
                if v:return v
    return None

def main():
    output=Path('gpu-smoke-output');output.mkdir(exist_ok=True)
    image=output/'synthetic_robot.png';synthetic_image(image)
    from gradio_client import Client,handle_file
    client=Client('zerogpu-aoti/wan2-2-fp8da-aoti-faster',verbose=False)
    print('Submitting ONE anonymous free Wan GPU request with SYNTHETIC image',flush=True)
    result=client.predict(input_image=handle_file(str(image.resolve())),
      prompt='A cheerful little cartoon robot takes two natural steps toward the camera, waving its right arm, full body articulation, smooth movie animation, static camera, no zoom',
      steps=4,negative_prompt='still image, zoom, pan, morphing, stiff figure, slideshow',
      duration_seconds=1.6,guidance_scale=1,guidance_scale_2=1,seed=41,randomize_seed=False,api_name='/generate_video')
    src=video_path(result)
    if not src:raise RuntimeError('API did not return a video file')
    path=Path(src)
    if not path.is_file() or path.stat().st_size<4000:raise RuntimeError('No usable MP4 video')
    target=output/'wan_free_gpu_test.mp4'
    shutil.copyfile(path,target)
    print('SUCCESS: genuine AI video bytes:',target.stat().st_size,flush=True)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print('FREE GPU RENDER UNAVAILABLE:',type(e).__name__,str(e)[:700],flush=True)
        sys.exit(1)
