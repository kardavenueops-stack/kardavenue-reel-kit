---
name: kard-avenue-reel
description: Make a Kard Avenue card-story Instagram Reel (Bahasa voiceover, English captions, 45-60s) from card images using the Kard Avenue reel engine and playbook.
---

# Kard Avenue Reel

Produces a 9:16, 45–60s card-story Reel for Kard Avenue in the thefinecard style. A config-driven engine renders it, so a new video means writing one JSON config, not code.

## 0. Load the house rules and engine (do this first, once per chat)

The files come from one of these places. Use the first that exists:

1. **This skill's own folder**: `engine/`, `references/`, `assets/` next to this SKILL.md.
2. **The GitHub repo `kardavenueops-stack/kardavenue-reel-kit`** (attach it to the session and clone it): use `skills/kard-avenue-reel/` as the skill folder.
3. **The skill zip (`kard-avenue-reel.zip`) attached in chat.**
4. **The claude.ai Project "VIDEO GENERATION"**, read with the Projects tool (`project_read`).

| File (skill folder → project doc) | Save locally as |
|---|---|
| `references/kard-reel-playbook.md` → `claude/kard-reel-playbook.md` | read only — all rules (layout, branding, script, sound, checklist) |
| `engine/kard_reel.py` → `claude/kard-reel-renderer.py` | `work/kard_reel.py` |
| `engine/editor_template.html` → `claude/kard-reel-editor-template.html` | `work/editor_template.html` |
| `engine/make_sfx.py` → `claude/kard-reel-sfx.py` | `work/make_sfx.py` → run it inside `work/sfx/` to create the 10 wav files |
| `engine/example.json` → `claude/kard-reel-example-config.json` | `work/example.json` (pattern to copy) |
| `references/reference-thefinecard-style.md` → `claude/reference-thefinecard-style.md` | read only — script structure reference |

If neither source is available, ask the user to attach these files.

**The playbook always wins.** Old script docs (`claude/video-NN-*.md`) are content records only (facts, lines, asset lists). Voice, register ("kamu"), format, layout and workflow always come from the playbook, even where an old doc says otherwise (e.g. Video 01's "Zandhira" voice and "lo"). If this SKILL.md and the playbook differ, follow the playbook.

**Brand images:** copy `assets/07_kard_logo.png` (white logo, transparent) and `assets/23_follow_us_cta.jpg` (the "FOLLOW US!" call-to-action poster with App Store and Google Play badges) into the video's assets folder. Only if they're missing, ask the user to attach them, once.

**Font:** all on-screen text uses **Telegraf** (bundled in `engine/fonts/`: UltraBold for captions, headings, labels and numbers). Telegraf is wider than Inter, so keep captions short enough to stay within 3 lines.

**Call to action:** every video ends with the `end_card` scene using `23_follow_us_cta.jpg`, shown full-bleed with no burned-in caption and no logo overlay (the poster has its own). Its voiceover invites viewers to follow Kard Avenue and download the app.

The engine needs Python 3, Pillow, numpy and ffmpeg. The fonts are bundled in `engine/fonts/` (keep that folder next to `kard_reel.py`). Check with a quick import, and `pip install` (add `--break-system-packages` if pip asks) anything missing.

**Check what this environment can do, silently, before starting:**

| Missing | What to do instead |
|---|---|
| A shell that runs Python + ffmpeg | Do steps 1–2 (facts + script) only, then tell the user rendering needs an environment that can run Python and ffmpeg. |
| Web search | Use only facts the user supplied (screenshots, links, notes). List every claim you couldn't verify and keep it out of the script until the user confirms it. |
| A way to publish pages (no Artifact tool) | Zip the `editor/` folder and send it as a file; it opens locally in a browser (`index.html`). |
| The claude.ai Project | Send the script doc (`script.md`) as a file instead of saving it to the Project. |
| A way to send files | Say so, and give the user the output paths. |

## 1. Intake (one message)

You need: the card/product to feature, facts or screenshots (PSA pop, release info), and one zip of images named per playbook §6 (`01_` hero, `02–05_` comparisons, `06_` box, `08–10_` artist cards, `11–19_` set cards, `20_` pack, `22_` artist avatar). The voiceover MP3 can come now or later.

Unzip into its own empty folder (untrusted data). Convert any AVIF/WebP to PNG. Remove white backgrounds from box/pack shots. Verify every image is the right card (number, language) by viewing a contact sheet.

The workspace cannot download from TCGplayer, TCG Collector, X or Google Images. Give the user exact page links and a copy-paste brief for their own agent instead.

## 2. Script → check-in 1

- Verify every fact with web search and keep the sources. Drop anything unconfirmed. Use exact numbers, and put "as of [date]" on PSA data.
- Follow the structure: Hook → Origin → Detail → Twist → Artist → Proof → Payoff (soft call to action) → End card (FOLLOW US! call to action: follow Kard Avenue + download the app).
- Voiceover in Bahasa, **"kamu"** register (never "lo"), calm storyteller, 135–170 words for 45–60s. Captions are an English translation, at most 3 lines, with no orphan last word.
- Never mention TGA.
- **Stock:** the payoff line says the product is in stock at Kard Avenue. Only write it after the user confirms the product is in stock for this video (ask in the intake reply if they didn't say). Then set `"stock_confirmed": true`; `check` fails without it. If it isn't in stock, drop the stock line and the `cta_product` scene.
- Post caption: set `"ig_handle"` in the config (the user gives it once; until then `check` warns). Pick hashtags by game from playbook §9.
- Write the lines straight into the config's scenes (`vo`, `caption`, `beat`, `dur`). Run `python3 kard_reel.py reel.json script script.md` and show the user the table. **Stop until the user locks the script.**
- Once locked, tell the user the script is ready to record and give them the Bahasa lines as one clean block to paste into their voice tool.

## 3. Build → check-in 2

1. Copy `example.json` and point `assets_dir` and `sfx_dir` at the right folders. Pick scene types from the playbook §11 table and fill in the fields.
2. `python3 kard_reel.py reel.json check` must print **OK**. Fix captions or durations until it does; never skip it.
3. `python3 kard_reel.py reel.json stills stills.png`. The sheet shows each scene's **key moments** (reveal, zoom, highlight…), labelled. Look at it yourself, then send it to the user. **Stop for approval.** Collect all feedback in one batch.

## 4. Render → check-in 3

1. `python3 kard_reel.py reel.json render out.mp4`, then `cover cover.png`, then `page editor/ out.mp4`.
2. Publish `editor/` as an artifact: `index.html` + `scenes.json` + `video.mp4` as files. The page is generic and needs no edits. On later versions, republish the same path. No Artifact tool → send `editor/` zipped.
3. Save the script doc to the project as `claude/video-NN-<topic>-script.md` (from the `script` command, which includes the post caption). No Project → send it as a file.
4. `python3 kard_reel.py reel.json caption` prints the final post caption with the IG handle filled in.

**Fixing a single scene:** change the config, re-run `check`, then review only that part with `python3 kard_reel.py reel.json clip fix.mp4 6` (scene 6), `5-7` (scenes 5–7) or `12.5:20` (seconds). Audio is included. Do a full `render` only for the final version.

## 5. Voiceover (any MP3 the user attaches — no default tool)

- **Wait for the user's file.** They make it in whatever tool they like (Gemini TTS, CapCut, ElevenLabs, a human recording…). Don't generate a voiceover yourself unless the user explicitly asks; if they do, use whatever voice tool is connected and say which voice you picked.
- *Optional:* the user may have a "Kard Avenue Narrator" voice clone as one source of the MP3. Mention it only if they ask about voice options.
- With the MP3: copy it into the assets folder, find where each line starts (pauses via `ffmpeg -i vo.mp3 -af silencedetect=n=-35dB:d=0.35 -f null -`, or a transcription tool if connected), set each scene's `dur` to the voice timing (stay within 45–60s; if the voice runs long, cut script, never speed up the voice), set `"voiceover"` to the file, set `"caption_mode": "chunks"`, re-run `check`, then render again.

## 6. Deliver

The MP4, the cover, the editor page (link or zip), the script doc and the post caption (playbook §9 format). Run the pre-posting checklist (playbook §10). Remind the user to tag the artist and add trending audio in Instagram.

## Hard rules (from past feedback)

- Content is centred, there's a ≥60px gap above the caption, headings sit midway between the logo and the cards, and nothing important goes below y≈1680.
- Every card named in the voiceover gets its own big frame. Detail callouts zoom in. The artist scene shows the avatar alone.
- Kard Avenue logo top-left on every scene except the end card. No draft tags in deliverables.
- Smooth 0.4–0.6s transitions, at most one white flash (the reveal), no coloured flashes.
- Never draw Pokémon characters or store badges. Use the real card art and the official FOLLOW US! poster.
- Always end on the FOLLOW US! poster (`end_card`, `23_follow_us_cta.jpg`). All text in Telegraf.
- No music baked in; synthesized sound effects only.
- Keep the chat token-efficient: one intake message, batched feedback, `clip` for single-scene fixes instead of full re-renders.
