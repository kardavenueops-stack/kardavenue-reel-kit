---
name: kard-finecard-reel
description: Make a Kard Avenue card-story Reel in the cinematic "Fine Card" style (full-bleed slow camera moves, blur dissolves, one-line captions, editorial type-on hook, Bahasa VO), 45–60s, 9:16.
---

# Kard Avenue Reel — Fine Card style

A calm, premium, documentary-style Reel after @thefinecard: every shot fills the screen with a real photo or macro close-up that is always slowly moving, shots cut every 1.5–3s with soft blur dissolves, and captions are small one-line chunks. It's the sibling of the `kard-avenue-reel` skill (graphic style). Same script rules, different look. A video is one JSON config of **scenes** (one VO line each), and each scene is a list of **shots**.

## 0. Setup (once per chat)

The files come from the first of these that exists: (1) this skill's own folder, if it has `engine/` and `assets/`; (2) the GitHub repo `kardavenueops-stack/kardavenue-reel-kit` (attach it to the session and clone it), using `skills/kard-finecard-reel/` as the skill root; (3) the skill zip (`kard-finecard-reel.zip`) attached in chat; otherwise ask the user to attach the zip.

Everything is in the skill folder. From the skill root, the example runs as-is:
```
python3 engine/fc_reel.py engine/example.json check     # generates sfx/ on first run, must print OK
```
| Path | Use |
|---|---|
| `engine/fc_reel.py` | Renderer. Copy `engine/` into the work folder (it finds `fonts/` and `make_sfx.py` next to itself) |
| `engine/editor_template.html` | Review page template, used by the `page` command |
| `engine/make_sfx.py` | Sound-effect generator; `check`/`render` run it automatically into `sfx_dir` if WAVs are missing |
| `engine/fonts/` | Inter SemiBold + Bold (.otf), Lora Italic (.ttf), NotoSansCJKsub-Bold.otf (Japanese/Chinese names); licences in `OFL.txt` |
| `engine/requirements.txt` | Python packages (Pillow, numpy); ffmpeg must be installed too |
| `engine/example.json` | Finished config (Dream Painting Pikachu); paths are relative to the config file (`../assets`, `../sfx`) |
| `assets/07_kard_logo.png`, `assets/07_kard_logo_dark.png`, `assets/23_end_card.png` (+ `23_end_card_original.webp`) | Brand files: white/dark logo and the FOLLOW US! CTA end card; copy into every new video's assets folder |
| `assets/` (other files) | The example's images and voiceover |
| `reference/visual-style.md` | What the style is and why |

For a new video, make a work folder with its own `assets/` (the user's images + the two brand files), copy `example.json` there as `fc.json`, and set `"assets_dir": "assets"`, `"sfx_dir": "sfx"`.

Needs Python 3 with Pillow + numpy (`pip install -r engine/requirements.txt`) and ffmpeg. The bundled CJK subset covers kana and CJK ideographs for artist names; without it the `person` shot falls back to the romaji name.

If the user's project has a `claude/kard-reel-playbook.md`, read it: its script, voice, branding and checklist rules apply here too. Layout and motion rules in this file replace its §4 and §7.

## 1. Intake (one message)
Topic, the one product/card to sell, facts, and **one zip of images** (naming as in the playbook: `01_` hero, `06_` box, `20_` pack, `22_` artist photo…). Unzip into its own empty folder, convert to PNG, and check every image on a contact sheet.

**This style lives or dies on image resolution.** Macro shots crop deep into an image, so ask for originals ≥2500px tall where possible. The user's own phone photos of real stock (box sides, figures, slabs, cards in hand) beat any online scan and fit Kard Avenue's authentication brand. Product photos on white work well with the `white` plate. The workspace can't download from Instagram, TCGplayer, X or Google Images, so give the user exact links and a copy-paste brief for their own agent instead.

## 2. Script → stop for lock
Same as the playbook: verify every fact with a source; Hook → Origin → Detail → Twist → Artist → Proof → Payoff → End card; Bahasa "kamu" voiceover, 135–170 words for 45–60s; English captions; never mention TGA; "in stock at Kard Avenue" only after the user confirms stock (`stock_confirmed: true`). The end card's line is the follow + download line. Run `python3 fc_reel.py fc.json script script.md`, show the table, and **stop until the user locks it**.

Voiceover is whatever MP3/WAV the user attaches (e.g. Google AI Studio TTS). If they ask for a style/expression version for AI Studio, give a **Style** paragraph plus the same lines with `[tags]` in brackets, and keep the spoken words identical to the locked script.

## 3. Shot design (the style rules)
- **Every shot is full-bleed and moving.** Use `from`/`to` (`[cx, cy, zoom]`) for a slow push/pan, or `keys` (`[[t, cx, cy, zoom], …]`) for a hold-then-glide. Typical zoom 1.0→1.12; macros 1.7–2.6; detail glides up to ~4.
- **Cut every 1.5–3s.** A 5–6s line gets 2–3 shots. The last shot of a scene takes the remaining time. `check` warns on any shot held over 5.5s.
- **Plates:** `cover` (image fills the frame, for card art), `white` (object on a soft studio sweep, for boxes, figures, packs and slabs; `fill` = height share, `y` = vertical centre), `blur` (the image over a blurred copy of itself, for a card you'll zoom into).
- **Hook:** a clean studio shot (`white` plate) with the hook typed on top-left using `title` (`*words*` become italic serif). Set `no_caption: true` on that scene.
- **Detail:** macro pans across the card art, then wide-to-macro on the same card. For a credit or number, use `keys` to glide from the full card into it.
- **Archival/older cards:** `film` shot type (film-strip frame).
- **Artist:** `person` shot type: photo over the blurred hero card, with name in Japanese + romaji.
- **Proof:** `split` (two views stacked, e.g. card art over figure or slab label), then a type-on number with `title` (e.g. `*143 : 1*`). If there's a PSA slab, macro on its label and end the proof on the slab.
- **Branding:** the logo is drawn small top-left automatically (it goes dark on bright shots). Add one red `FOLLOW` pill at ~7s and, if stock is confirmed, an `IN STOCK · KARD AVENUE` pill on the payoff (`pills` in the config).
- **No** starbursts, stamps, charts, coloured flashes or drawn characters. The look is calm and premium.
- **End:** the last scene is one `{"type": "end"}` shot (the fixed FOLLOW US! card, no caption).

## 4. Build → stop for stills approval
1. Copy `example.json` to `fc.json`; set `assets_dir`, `sfx_dir`, scenes and shots.
2. `python3 fc_reel.py fc.json check` must print **OK**. Fix errors; read the softness warnings and tell the user which images would look better at higher resolution.
3. `python3 fc_reel.py fc.json stills stills.png`: one frame per shot. Look at it yourself (framing, nothing important cut off, captions readable), then send it. **Stop for approval**, and collect feedback in one batch.
4. Single-shot fixes: `python3 fc_reel.py fc.json frame T out.png` to look, and `clip out.mp4 6` (scene 6) or `clip out.mp4 12.5:20` (seconds) to review with audio. Don't re-render the whole video for one fix.

## 5. Voiceover → render
1. Find each line's start from pauses: `ffmpeg -i vo.wav -af silencedetect=n=-38dB:d=0.25 -f null -`. Where two lines run together, find the quietest dip between them.
2. If the read is over 60s, shorten long pauses (keep a dramatic beat before the reveal), then apply at most ~8% `atempo`. Pitch is preserved. Tell the user what you did. Never cut words.
3. Set each scene's `dur` from the line starts, scale any `keys` times in that scene by the same ratio, move the stock pill's `at`, set `"voiceover": "voiceover.mp3"`, run `check` again.
4. `python3 fc_reel.py fc.json render out.mp4` (about 6–10 min), then `page editor/ out.mp4` and publish `editor/` (index.html + scenes.json + video.mp4) as the review page.

## 6. Deliver
The MP4, the review page, the script doc (`script` command) saved to the project as `claude/video-NN-<topic>-finecard-script.md`, and the post caption. Pre-posting: 45–60s; captions = script; facts sourced; last scene is the end card; watch once on a phone (nothing important below y≈1680); tag the artist; add trending audio in Instagram (no music is baked in).

## Shot-type reference
| Type | Fields |
|---|---|
| `kb` (default) | `img`, `plate` cover/white/blur, `fill`, `y`, `from`/`to` or `keys`, `focus_in` (s), `title {text, at, per, size, y}`, `sfx [[t, name, gain]]`, `d` |
| `film` | same camera fields, shown in a film-strip frame |
| `split` | `top {…}`, `bottom {…}` (each a camera view) |
| `person` | `img` (photo), `bg` (image blurred behind), `name_jp`, `name_en` |
| `end` | none (uses `23_end_card.png`) |

Scene: `beat`, `dur`, `vo`, `caption`, `visual`, `no_caption`, `shots`. Global: `logo`, `assets_dir`, `sfx_dir`, `voiceover`, `pills`, `stock_confirmed`, `forbidden_words`, `ig_handle`, `post_caption`, `open_decisions`.
