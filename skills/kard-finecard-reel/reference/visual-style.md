# Visual style reference — @thefinecard Reel (ANA Pikachu & Larvitar promos)

Source: reference MP4 supplied by YME on 29 Oct 2026 (49s, 720×1280, 30fps). YME wants Kard Avenue Reels to look more like this. Companion to `reference-thefinecard-style.md` (script structure).

## What the reference does

| Area | Reference | Our engine v2.2 today |
|---|---|---|
| Framing | Every shot is **full-bleed**: a real photo, archival clip or **macro close-up** fills the whole 9:16 frame | Cards float on a navy/purple bokeh background |
| Motion | Constant slow camera move on every shot: push-in, pan, tilt, rack-focus. Shots change about every 1.5–3s | Scene templates with pops, slides, stamps; scenes last 3–6s |
| Transitions | Soft **blur/defocus dissolves** and match cuts (wide card → macro of the same card). No flashes | White flash on the reveal, slide-ins |
| Hook | Clean studio product shot (Pikachu figure on white), slow push-in. Editorial headline types on word by word, **top-left**, sans + *italic serif* mix ("Pokemon once created *two cards* that were…") | Starburst, ✗ stamps, mystery card, big caption |
| Captions | **Small, one line, 2–4 words**, white sans with soft shadow, lower third. No yellow highlights, no heavy stroke | 60px ExtraBold, up to 3 lines, yellow keywords, 7px stroke |
| Branding | Small white stacked wordmark top-left on every shot. One red "FOLLOW" pill pops once, early (~7s). Photo credits (@source) small bottom-right | Logo top-left; no follow pop; no credits |
| Archival | Old footage/ads shown inside a **film-strip / VHS frame** with grain ("Back in 2001") | Typed date over box + pack |
| Detail | Macro pans across card art, set symbol, HP, attack text; wide and close shots of the same card | Circle + arrow + zoom on a flat scan |
| People | Artist as a **photo cut-out** in front of a blurred card wall, name in Japanese + romaji | Round avatar with yellow ring |
| Proof | Shows the **graded slab**: macro on the PSA label, then a **2-up split** (card top, slab label bottom), then the slab as the final hero | Bar chart + counter + full-screen number |
| Ending | Slab hero → sponsor logo on black | FOLLOW US! end card |
| Tone | Calm, premium, documentary. No stamps, starbursts or charts | Energetic, graphic |

## What it needs from us
- **High-resolution photos**: macro crops need ≥2500px-tall scans or real photos. Phone photos of our own stock (card, figure, slab, box) are best and fit Kard Avenue's authentication brand.
- A short archival or "origin" visual per video (product launch image, ad, event photo), with source credit.
- The engine needs new full-bleed shot types: `kenburns` (image + start/end crop rectangles), `macro_pan`, `split_2up`, `title_typeon`, `filmstrip`, `cutout_person`, plus blur-dissolve transitions and a one-line caption mode.
