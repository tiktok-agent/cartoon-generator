# Cyberfamilie: wereldwijd gratis GPU's combineren

**Onderzocht: 21 november 2026.** Geen enkele derde-partij-account is automatisch aangemaakt, gekoppeld of geverifieerd. Gratis toegang = afhankelijk van persoonlijke quota, land, goedkeuring, identiteit en voorwaarden.

## Techniek: wat kan echt?

- **Parallelle filmproductie werkt:** onafhankelijke scènes worden per GPU-server gemaakt, daarna in FFmpeg gemonteerd. Dit is de route die `gpu_pool.py` ondersteunt.
- **Eén virtuele GPU van alle vrije GPU's wereldwijd maken werkt meestal niet:** onvergelijkbare API-only servers geven geen SSH/CUDA- of ROCm-toegang; WAN-latentie en netwerkbeperkingen maken het opdelen van één video-inferentierun erg lastig. Ray en torch.distributed werken alleen met eigen toegankelijke compute-nodes en bijbehorende netwerkconfiguratie.
- **Gratis demo ≠ huur-GPU:** een HF ZeroGPU Space exposeert app-functionaliteit, niet de GPU-root. `gpu_pool.py` gebruikt alleen geautoriseerde publieke Gradio-apps, geen hardware-pooling of toegangsbeperkingsomzeiling.
- **Strikt €0:** geen automatische betaalde fallback, nieuwe trial-account, activatie van betaald gebruik of betaling. Providers waar een trial na afloop betaald wordt, blijven *catalog-only*.

## Beste gecontroleerde bronnen

| Herkomst / dienst | Wat is officieel gratis | Beperking | Voor Cyberfamilie |
|---|---|---|---|
| Internationaal / [HF ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu) | Bestaande publieke GPU-Spaces; 48GB / 96GB GPU-toewijzingen onder quota; gratis persoonlijk hosten van max twee ZeroGPU Spaces voor geverifieerde accounts >30d | wachtrij, dagquota, GPU-tijd kort; voor hosting Gradio app nodig | **1e keuze** voor korte AI-videoscènes via publieke Spaces |
| China / [Alibaba PAI DSW](https://help.aliyun.com/en/pai/product-overview/free-trial-guide) | Eerste gebruikers: 250 CU-uren per maand, 3 maanden. A10 24GB kost 6.991 CU/u = ca. 35.8 echte uren/maand | ID-controle, Chinese regio's, 1 GPU instantie tegelijk, na trial automatisch betaald tenzij gestopt | **Goede zelfstandige GPU**, maar *niet automatisch starten* |
| China / [ModelScope AMD](https://www.modelscope.cn/posts/433641) | ontwikkelprogramma met tot 1000+ GPU-uren bij deelname; aparte xGPU hosted inference | niet gegarandeerd, account + toegang/badges/activiteiten | veelbelovend voor GPU-hosting (ook AMD) |
| Mondiaal / [AMD Developer Cloud](https://www.amd.com/en/developer/resources/cloud-access/amd-developer-cloud.html) | na aanvraag tot US$100 credits volgens AMD | goedkeuring, ROCm GPU (MI300X 192GB), storage mogelijk betaald, credit loopt af | **zwaar model**, alleen na goedkeuring en strikte kostenbewaking |
| Mondiaal / [Modal](https://modal.com/pricing) | Starter: US$30 compute/maand (volgens site vanaf sept. 2026) | boven gratis bedrag kan facturatie doorgaan; eigen account + spend limit nodig | geschikte programmeerbare GPU-jobs, handmatig instellen |
| VS / [Kaggle Notebooks](https://www.kaggle.com/docs/notebooks) | gratis GPU-notebooks (T4x2/P100 afhankelijk van beschikbaarheid), dynamische weekquota | notebooks geen 24/7 GPU-cluster; alleen volgens gebruiksvoorwaarden | kleinere/quants GPU-video-prototypes |
| Mondiaal / [Google Colab](https://research.google.com/colaboratory/faq.html) | gratis notebook GPU met fluctuerende quota | geen gegarandeerde GPU, beperkte looptijd, niet misbruiken als onbewaakte remote server | interactieve test, niet onze permanente externe worker |
| Mondiaal / [Lightning AI](https://platform.lightning.ai/studio) | 5 introductiecredits en gratis CPU Studio | GPU-uren via eindig tegoed, account nodig | test-/ontwikkelbron |
| Mondiaal / [Paperspace Gradient](https://docs.digitalocean.com/products/paperspace/pricing/) | gratis M4000 GPU-notebook volgens officiële prijslijst | oudere GPU en wachtrij, legacy API gestopt | kleine modellen, weinig VRAM |
| India / [Yotta Shakti Studio](https://yotta.com/newsletter/yotta-spark-edition-aug-sep-2026/) | aanbod van INR 10.000 gratis rekencredits in Aug-Sep 2026 publicatie | voorwaarden/geografische aanmelding en actuele claimstatus nog verifiëren | mogelijk krachtige GPU-proef |
| India / [Yotta Shambho](https://yotta.com/shambho/) | voor gekwalificeerde startups tot US$35.000 basiscredits, meer onder programmaprogressie | **startup-programma** met toelating, niet algemeen gratis | alleen bij geschiktheid |
| India / [IndiaAI Compute](https://compute.indiaai.gov.in/eligibilitycriteria) | subsidie op GPU voor goedgekeurde Indiase instellingen en startups | ***niet*** vrij beschikbare GPU voor Nederlanders | niet als gratis standaardoptie inzetten |
| Rusland / [Selectel ML Platform](https://selectel.ru/services/gpu/) | twee weken gratis test volgens Selectel | claim afhankelijk van account/aanvraag; GPU-toegang niet gegarandeerd; lokale betaal- en jurisdictievereisten | alleen optioneel na expliciete voorwaardencheck |
| Europa / [AI Horde](https://github.com/Haidra-org/AI-Horde) | gratis wereldwijde vrijwillige GPU-workers voor **beelden en tekst** | geen aangetoonde algemene video-rendering of GPU-root toegang | referentiebeelden, **niet** videomodellen |

## Afgewezen schijnopties

- [Yandex Cloud](https://yandex.cloud/en/docs/getting-started/free-trial/concepts/limits): november 2026, geen free trial voor nieuwe klanten en trial-GPU quota `0`.
- [AWS SageMaker Studio Lab](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-lab-overview.html): gratis GPU voor **bestaande** klanten, maar sinds **30 juli 2026** gesloten voor nieuwe klanten.
- [Featurize](https://docs.featurize.cn/docs/activity/welcome-bonus) China: eerst minimaal 5 CNY opladen voor 1 uur gratis coupon — voldoet niet aan strikt €0.
- [Akash trial](https://akash.network/docs/getting-started/quick-start/): slechts US$1 gratis en high-end GPU's niet in proef beschikbaar.

## Plan voor een echte proefscène

1. Gebruik `python gpu_pool.py catalog` om beschikbare bronnen en restricties te tonen.
2. Gebruik `python gpu_pool.py plan` om twee losse scènes over Wan en Hunyuan te verdelen.
3. Gebruik alleen na account-/quota-check `python gpu_pool.py render-free-parallel --workers 2` voor **max. 2 parallelle gratis publieke demo-aanvragen**. Geen automatische VPN, regio-omzeiling, betalingen of accountcreatie.
4. Verifieer dat personen echt lopen, armen bewegen en de scène meer is dan camerapan. `python pipeline.py assemble` monteert gevalideerde echte MP4's.
5. Mocht geen ZeroGPU-quota beschikbaar zijn: wacht op toegestane reset of gebruik *handmatige* export van een andere gratis bron. Niet onbeperkt retries of extra accounts aanmaken om limieten te omzeilen.

**Status:** GitHub bevat de planner; er zijn geen GPU-accounts van andere aanbieders gekoppeld, geen betaalde instanties gestart en geen Cyberfamilie-videoclip succesvol gerenderd.