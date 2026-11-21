# CYBERFAMILIE — Gratis verbonden filmstudio (21 november 2026)

**Wat is nu echt gekoppeld?** Eén lokaal productieprogramma dat **drie publieke gratis videomodeldemos** kan aanroepen: Wan 2.2 (China), HunyuanVideo 1.5 (China), LTX-2.3 (Israël). Daarnaast bevat het een **import-koppeling voor negen plus overige diensten**: Viggle, Vidu, PixVerse, Dreamina, Kandinsky/GigaChat, Alice/Yandex, Shotloom, Varya, Animaker, Qwen. Het programma verwerkt hun MP4's in **dezelfde film**, maar beschikt niet over hun accounts of betaalde API-sleutels.

## Wat kost het?
Het programma gebruikt alleen publieke Hugging Face ZeroGPU-quota voor automatische videoaanvragen. Demos kunnen wachtrijen, tijdslimieten of inlogvereisten hebben. Als gratis renderen niet kan, volgt een foutmelding. **Nooit een betaalde provider, geen automatische TikTok-publicatie.** Je behoudt je recht om het eindresultaat te beoordelen voordat je iets publiceert. Bevestig zelf commerciële gebruiksrechten bij iedere dienst.

## Eenvoudigste manier voor Windows
Pak het ZIP-bestand uit, installeer Python 3.10+ en FFmpeg. Dubbelklik `START_HIER_WINDOWS.bat`. Het programma installeert Python-benodigdheden, toont scènes en laat gratis proberen, controleren of monteren.

## Via terminal
```
python -m pip install -r requirements.txt
python pipeline.py prepare
python pipeline.py status
python pipeline.py render --provider auto
python pipeline.py render --provider wan --shot shot_01
python pipeline.py import --shot shot_02 --file "C:/Downloads/mijn_gegenereerde_video.mp4"
python pipeline.py assemble
```

- `prepare` schrijft per scène de prompts en alle bezoekslinks naar `handoff/`.
- `render` probeert Wan, Hunyuan en LTX opeenvolgend, maar accepteert alléén echte videobestanden. Met `--provider` kun je één videomodel testen.
- `import` accepteert echte MP4's die je bij andere gratis diensten hebt gemaakt; bestaande clips worden niet overschreven.
- `assemble` controleert elke clip op afspeelbaarheid, een minimale duur en beeldverandering, normaliseert 24 fps / 720×1280, en monteert via FFmpeg één film naar `output/Cyberfamilie_De_mysterieuze_knop.mp4`.
- Automatische lipsync is **niet geïntegreerd** omdat een echte Nederlandse audio-/viseme-workflow nog niet is gevalideerd. LTX kan eigen audio genereren, maar de huidige montage exporteert bewust zonder geluid om te voorkomen dat onjuiste of verzonnen dialogen als kloppend worden gepresenteerd.

## Huidige productiegegevens
- Bronillustratie: `assets/neonfamilie.png` (in dit ZIP, niet publiek op GitHub gezet).
- 2 shots van 4 seconden met natuurlijk lopen, rennen, armbewegingen en reacties.
- De optische beeldveranderingscontrole bewijst niet of iedere lichaamsbeweging anatomisch goed is. De film moet ook door een mens bekeken worden.
- Geen gedownloade video: de bronomgeving had op 21 november geen DNS/internet, dus de externe generatie is **nog niet uitgevoerd**.

## Herkomst van gekoppelde API's (controleer op updates)
- Wan: https://huggingface.co/spaces/zerogpu-aoti/wan2-2-fp8da-aoti-faster/blob/main/app.py
- Hunyuan: https://huggingface.co/spaces/multimodalart/Hunyuan-Video-1-5/blob/main/app.py
- LTX: https://huggingface.co/spaces/Lightricks/LTX-2-3/blob/main/app.py
- Officiële PixVerse-billing: https://docs.platform.pixverse.ai/subscribe-api-plans-882969m0
- Officiële Viggle API: https://viggle.ai/developers

## Veiligheid en beperkingen
- Alleen een uitdrukkelijk gestarte `render` doet externe requests met de eigen referentieafbeelding.
- Er worden geen betaalmiddelen aangeroepen of credentials opgeslagen.
- De gebruiker moet bij elke derde partij toestemming/licentie voor hun diensten zelf controleren.
- De publieke gratis demos kunnen stoppen, veranderen of andere inputparameters krijgen. Het programma stopt dan met een duidelijke melding.

## Echte gratis GPU-koppeling — 21 november 2026
De GitHub Actions-netwerktest heeft de Gradio API's van **Wan 2.2, HunyuanVideo 1.5 en LTX-2.3** daadwerkelijk bereikt:
https://github.com/tiktok-agent/cartoon-generator/actions/runs/44925020645

Een aparte eenmalige **anonieme gratis** proefrender met een **kunstmatig robotbeeld** heeft via Wan 2.2 een echte H.264 MP4 geproduceerd (560×832, 25 frames bij 16 fps, circa 1,56 seconde). Bewijs:
https://github.com/tiktok-agent/cartoon-generator/actions/runs/44925192265

Bestanden: `gpu_connection_check.py` en `render_free_smoke.py`; workflows in `.github/workflows`.

De originele Cyberfamilie-foto is **niet op de publieke GitHub geplaatst** en niet naar de gratis proefrender gestuurd. Het originele verhaal is nog niet geproduceerd; er is nog geen bruikbare Nederlandse lipsync. Andere cloud-GPU's vereisen eigen accounts en zijn geen actieve nodes.
