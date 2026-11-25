---
name: kard-avenue-reel
description: Make a Kard Avenue card-story Instagram Reel (Bahasa voiceover, English captions, 45-60s) from card images using the Kard Avenue reel engine and playbook.
---

# Kard Avenue Reel

Produces a 9:16, 45–60s card-story Reel for Kard Avenue in the thefinecard style. A config-driven engine renders it, so a new video means writing one JSON config, not code.

## 0. Load the house rules and engine (do this first, once per chat)

**Before starting any reel:** read the project memory file `areas/kard-avenue-reels.md` and playbook §16–§21. **After the user approves a video:** write what was learned (revisions asked for, what worked) back to that memory file and to the playbook, so the same revision never has to be asked twice.

The files come from one of these places. Use the first that exists:

1. **This skill's own folder**: `engine/`, `references/`, `assets/` next to this SKILL.md.
2. **The GitHub repo `kardavenueops-stack/kardavenue-reel-kit`** (attach it to the session and clone it): use `skills/kard-avenue-reel/` as the skill folder.
3. **The skill zip (`kard-avenue-reel.zip`) attached in chat.**
4. **The claude.ai Project "KARD VIDEO GENERATIONS"**: only the playbook (`claude/kard-reel-playbook.md`) lives there. Never use an engine, config or sound script from the Project.

| File (skill folder) | Save locally as |
|---|---|
| `references/kard-reel-playbook.md` (also `claude/kard-reel-playbook.md` in the Project) | read only — all rules (layout, branding, script, sound, checklist) |
| `engine/kard_reel.py` (v3.9) + `engine/worlds.py` + `engine/living.py` | `work/` (keep all three and `fonts/` together; `living.py` imports `worlds.py`) |
| `engine/editor_template.html` | `work/editor_template.html` |
| `assets/sfx/*.wav` (the user's sound pack) | copy into `work/sfx/` (no synthesized sounds; never run an old make_sfx.py) |
| `engine/example_editorial_arita.json` | `work/example.json` (**default pattern to copy**, approved Video 11 editorial style) |
| `engine/example_countdown_most_graded.json` | reference for top-N / data-story reels (Video 12 "Ranked Countdown"; card file names are placeholders) |
| `engine/example_rivalry_lore_vendetta.json` | reference for story/lore reels (Video 15 "Rivalry Lore": `versus`, `versus_rows`, `diptych`, `shadow_clones`, `seal`, rain slam, editorial marker on card text) |
| `examples/video17/` (`reel.json`, `reel_trial.json`, `gen.py`, `gen_trial.py`, `retime.py`, `retime_trial.py`, `beats.py`) | reference for group-art / music-band reels (Video 17 HEARTSTEEL: `player_freeze`, `spotlight`, `flip`, `spot_groups`) and the VO retime + trial workflow (playbook §20). The scripts are Video 17's working copies: adjust their file paths before reuse |
| `tools/make_masks.py` + `tools/hs_boxes.json` | outline masks + rim lights for `spotlight` (trace mode) / `spot_groups`: `python3 tools/make_masks.py ART.png boxes.json --preview` (needs `rembg[cpu]`, model `isnet-anime`; check the preview, re-run one member with `--only key`) |
| `examples/video18/` (`gen.py`, `reel.json`, `prep.py`, `hl_sunday_*.png`) | reference for v3.9 (Video 18 Mangaka × Pokémon: `prerender` scenes from `worlds.py` / `living.py`, ink/focus/page/iris transitions, traced `lift` highlights). Scripts use Video 18's working paths: adjust before reuse |
| `tools/trace_mask.py` | glyph mask from coloured print for `lift` highlights |
| `tools/trace_outline.py` | character outline mask for living cards (`living.py`) |
| `references/kard-reel-v3.9-notes.md` | full v3.9 change list (playbook §21) |
| `engine/example_brand_mono_delta_reign.json` | reference only (Video 06) |
| `engine/example_3d_illustration_contest.json` | reference only (Video 05) |
| `references/reference-thefinecard-style.md` | read only — script structure reference |

If none of these is available, ask the user to attach the skill zip.

**Default style (approved, keep until the user says otherwise):** the Video 11 editorial style in playbook §16, on top of the Video 06 "brand mono" base in §15 (black #0a0a0a / white #fafafa, the user's sound pack), built from `engine/example_editorial_arita.json` (engine v3.9, which keeps the v3.2 features: glitch + zoom transitions, `macro3d` with `"card": false`, editorial `highlight` with `follow` camera, `noir` + `spot` detective look, fly-over `plane` mode, artist `cutout`, `card_wall` scene; `mono_ui` turns all accents white, no navy/purple tints). Start every new reel from that example. Use only the files in this skill folder; if `engine/` is missing here, use the GitHub repo, never an older Project copy.

**A different pattern per topic (playbook §17).** Keep the pillar and the approved look, but do not repeat the previous video's pattern: pick Artist Spotlight, Set preview or Ranked Countdown by topic, and build at least one motion that is new for this video. Engine v3.3 adds `rank`, `bar_race`, `leaderboard`, `coverflow`, `deal` and `conveyor`; v3.4–v3.6 add `versus`, `versus_rows`, `diptych`, `shadow_clones`, `seal`, the falling-cards `rain` slam and `"caption_shadow": "strong"` (playbook §18–§19); v3.7–v3.8 add `stage_table`, `player_freeze`, `spotlight` (trace mode + logo drive-through), `flip` and `spot_groups` (`mask_fmt`/`rim_fmt`), plus `card_lineup` `rows: 2`/`bg_img`, highlight `style: 'band'`, `caption_groups` and `chunk_list` (playbook §20); v3.9 adds the `prerender` scene type (plays a folder of JPG frames made by `worlds.py` — monochrome worlds, `card3d`, `S_versus` / `S_flip` / `S_payoff` recipes — or `living.py` layered 2.5D living cards, camera-only motion), `ink` / `focus` / `page` / `iris` transitions, `lift` highlights on `macro3d` (real colours on a dimmed noir page, exact letters via a traced `mask`), `hl_boost` / `hl_glow`, and `caption_groups` on any scene (playbook §21). Patterns now also include **Rivalry Lore** (one story per reel, §19). Use the `card_wall` / moving `crowd` look at most once per video. `"max_len": 75` allows a longer cut when the user asks for one.

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

1. Copy `example_editorial_arita.json` (default style, playbook §16 on top of §15) and point `assets_dir` and `sfx_dir` at the right folders. Pick scene types from the playbook §11 table and fill in the fields.
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

- **Voiceover sync (playbook §19, critical):** never place lines by estimated duration. Map every script line to the real recording (`silencedetect` pauses + syllable-beat counts per segment vs each line's syllables, confirmed by landmarks), build the timeline from that map, and after rendering check that no speech crosses a cut (except deliberate mid-sentence splits) and that frames at cue words show the right card.
- **Captions:** plain white with `"caption_shadow": "strong"`, never a box (`caption_bg` off). Use `caption_groups: [[text, t0, t1], …]` so captions follow the voice inside one long scene.
- **Bottom credit line (v3.9):** never leave the bottom band blank — use the two-line credit footer (`FOOTERS` / `footer()` in `worlds.py`, e.g. "CHAPTER 01 · GOSHO AOYAMA" / "DETECTIVE CONAN · SINCE 1994"; `frame=True` on the opening hook). The top badge never overlaps the main object, and name titles stay clear of the caption.
- **Highlights (v3.9):** coloured print → `style: 'lift'` with a mask traced by `tools/trace_mask.py`; highlight words in VO order (`silencedetect -32dB d=.08` for phrase gaps). `spot` sizes are pixels, never fractions.
- **2-CPU workspace:** render `prerender` frames in two halves (`miss[part::2]`, or `python3 worlds.py NAME OUTDIR t1 t2 …`), each pass in the foreground and under 10 minutes; background jobs are killed when the reply ends. Put every preview and render on the editor page artifact.
- **Video 17 rules (playbook §20):** fill the frame (no big empty bands); close-ups frame head + body and never overlap the Kard Avenue logo; trace/outline the subject instead of a round spotlight; never show the same image across two scenes in a row (make it one continuous shot); glitch between hook scenes; highlights sit exactly on the text; camera moves never stop and start mid-beat.
- **Trial Reel:** the user records only the new hook lines (+ optional bridge); splice them in front of the main VO (`retime_trial.py` / `gen_trial.py` pattern) and merge lines that share one image into one scene.
- **Small fixes:** render only the changed range with `clip OUT.mp4 a:b` and splice it in with ffmpeg (`-t a` on the first input, `-ss b` on the third; never two `trim`s on one input), audio copied from the original.
- **Opening shot:** reversed fly-over — the card starts close on the viewer's side, then pulls back and tips away.
- **Blurry scans that get zoomed:** upscale with Real-ESRGAN x4 before close-ups/signature zooms.

- Content is centred, there's a ≥60px gap above the caption, headings sit midway between the logo and the cards, and nothing important goes below y≈1680.
- Every card named in the voiceover gets its own big frame. Detail callouts zoom in. The artist scene shows the avatar alone.
- Kard Avenue logo centred at the top on every scene except the end card (same size and position as on the FOLLOW US! poster). No draft tags in deliverables.
- Transitions per playbook §14 motion rules: whip pans and soft white light leaks (`leak_color`, §15), 0.25–0.45s; at most one white flash, no other coloured flashes.
- Never stretch any card, pack or image; 3D tilts use true rotation. Cut white scan corners before use.
- Keep the approved Video 11 style (playbook §16 on top of §15, with §14 motion) until the user updates it: black #0a0a0a / white #fafafa only, white captions, one scene per product. Never leave a scene empty, but use the `card_wall` / moving `crowd` look at most once per video (§17).
- Never draw Pokémon characters or store badges. Use the real card art and the official FOLLOW US! poster.
- Always end on the FOLLOW US! poster (`end_card`, `23_follow_us_cta.jpg`). All text in Telegraf.
- No music baked in. Sound effects come only from the user's pack in `assets/sfx/` (sound map in playbook §15); no synthesized sounds.
- Keep the chat token-efficient: one intake message, batched feedback, `clip` for single-scene fixes instead of full re-renders.
