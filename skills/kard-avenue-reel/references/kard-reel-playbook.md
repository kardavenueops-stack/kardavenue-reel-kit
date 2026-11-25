# Kard Avenue Reel Playbook

Instructions for making Kard Avenue card-story Reels with Claude. Read this first in every new video chat. It replaces re-explaining preferences and avoids most revision rounds.

**This playbook always wins.** Older script docs (`claude/video-NN-*.md`) are content records only: their facts, lines and assets can be reused, but voice, register ("kamu"), format, layout and workflow always come from this file, even where an old doc says otherwise (e.g. Video 01's "Zandhira" / "lo").

Reference style: `claude/reference-thefinecard-style.md`.
Engine (v2.1, config-driven): `claude/kard-reel-renderer.py` (save as `kard_reel.py`) + `claude/kard-reel-editor-template.html` (save as `editor_template.html` next to it) + `claude/kard-reel-sfx.py`.
Example config: `claude/kard-reel-example-config.json` (the Chinese Sylveon reel).

---

## 1. How to start a new video (token-efficient workflow)

1. **New chat per video**, inside the VIDEO GENERATION project. Long chats re-read every screenshot on every step; a fresh chat costs roughly half per change.
2. **First message = everything at once:**
   - Topic + the one card/product to sell
   - Facts or screenshots you already have (PSA pop, release info)
   - **One zip** of all images, already named per §6
   - Any changes to the defaults in this file
3. Claude then does, in order, with **three approval stops**:
   1. Verify facts (web) → write script in the §3 structure (in "kamu" register) → **you lock the script** *(check-in 1)*
   2. Build the video from the engine → send a **contact sheet of stills** (the key moments of every scene: reveals, zooms, highlights) → **you approve** *(check-in 2)*
   3. Render full MP4 + update the editor page → final review *(check-in 3)*
   4. **Voiceover:** after the script is locked, you make the voiceover in any tool and attach the MP3. Claude never generates it unless you ask. Claude then re-times the scenes to the voice and re-renders.
4. **Feedback in batches.** Use the editor page's note boxes per timestamp, then "Copy notes for Claude" and paste once. Ten notes in one message is far cheaper than ten separate messages.
5. Screenshots only when needed; describe the timestamp instead ("0:12 grid too small") when you can.
6. **Single-scene fixes** are reviewed with `clip` (just that scene, with audio), not a full re-render. Full render only for the final.

## 2. Format

| Setting | Value |
|---|---|
| Size | 1080×1920 (9:16), 30 fps, H.264 |
| Length | **Minimum 45s, maximum 60s.** Follows the voiceover inside that range. Script budget at ~3 words/sec: **135–170 words** of voiceover. Under 45s → add a detail beat; over 60s → cut the weakest beat, never speed up the voice. |
| Platforms | Instagram Reels first, then TikTok / YouTube Shorts |
| Voice | **Any MP3 you attach** (any tool, or a human recording). Bahasa Indonesia, casual but polished: use **"kamu"**, never "lo". Calm storyteller. |
| Captions | English, burned in |
| Music | **None baked in**. Added in Instagram (trending audio). Sound effects only. |

**Pacing:** every scene 2–6s. Never hold a still frame for more than ~2.5s without motion (zoom, sweep, pop). If a scene feels long, cut time, don't add filler.

## 3. Script rules

**Structure** (thefinecard formula, every video):
1. **Hook**: one paradox or bold claim about one card ("This Sylveon? You'll never pull it in English, Japanese, or even Indonesian.")
2. **Origin**: "In [month year], Pokémon released…"
3. **Detail**: what makes it special (set, artwork, finish)
4. **Twist**: "But here's the surprise…"
5. **Artist**: full name and handle when known
6. **Proof**: one hard number (PSA pop report)
7. **Payoff + soft call to action**: "The only way to get one? … in stock at Kard Avenue."
8. **End card**: "Follow Kard Avenue and download the app on Google Play and the App Store." over the FOLLOW US! poster.

**Rules:**
- Bahasa register: **"kamu"** (casual, polished). Never "lo".
- Narrator tone: a knowledgeable collector telling a story. No hard selling in the voiceover; selling goes in the post caption.
- **Every fact verified** with a source before it goes in. Drop anything unconfirmed (example: we dropped "guaranteed SAR per box").
- **Exact numbers, not rounded** (1,596 not "around 1,500"). PSA pop always shows **"as of [date]"** on screen and gets re-checked on posting day.
- **The script doc is the single source of truth.** Video captions, the script doc and the editor page must match word for word; Claude runs an automated check after every change.
- About **3 words per second** of voiceover. Numbers read long in Bahasa ("2.050" = "dua ribu lima puluh"), so budget extra time.
- Never mention **TGA** (project on hold).

## 4. Layout rules (frame composition)

- **Center everything.** Content block (cards + text) and caption are vertically balanced as one group. Engine setting `OY = 60` shifts content down; caption centre at **y ≈ 1565**.
- **Gap card → caption ≥ 60px.** Nothing may touch or overlap the caption.
- **Caption:** max 3 lines, max width 900px, centred. Avoid a single orphan word on the last line; shorten the line in the script if needed.
- **Instagram safe zone:** keep captions and key content above **y ≈ 1680**. The bottom ~400px is covered by username, caption and audio in the app.
- **Headings** (e.g. "SAME ART", "ALL BY rika") sit at the **midpoint between the logo and the cards**, not touching the cards.
- **Side margin ≥ 30px**; cards never cut off by the frame edge (except intentional zooms).
- **Card sizes (minimum heights):**

| Use | Height |
|---|---|
| Hero card, single | 1000px |
| Featured card, own scene | ~980px |
| Row of 3 | 450–560px (slight fan/overlap is fine) |
| 3×3 grid | 360px |
| Small supporting card | Never below 300px |

- **If the voiceover names a card, it gets its own big frame.** Don't leave it as a thumbnail (lesson: rika's Dragonair/Mantyke/Umbreon).
- **Detail callouts zoom in** (camera zoom into the card number, not just a red circle).
- **Artist scene:** avatar alone, large and centred, with name, ILLUSTRATOR and @handle. Don't repeat the hero card next to it.

## 5. Branding

- **Kard Avenue logo** (white, transparent PNG) **centred at the top** on every scene, same size and position as the logo on the FOLLOW US! poster: width 370, y 150, 100% opacity.
- **Badges** (`badges: [{text, at, hl}]` on any scene) pop in midway between the logo and the cards; yellow when `hl` is true.
- **Caption panel** (`caption_bg: true`) puts a dark rounded panel behind the caption; use it on full-frame zooms and b-roll.
- Content offset OY 120, caption centre y 1560.
- **Hidden on the end card**, because the promo image has its own logo.
- **No draft tags or watermarks** in anything delivered (no "DRAFT v…").
- **End card (call to action) = always the Kard Avenue "FOLLOW US!" poster** (`23_follow_us_cta.jpg`: logo, "FOLLOW US! / TO GET THE LATEST KARD AVENUE'S UPDATE.", "AUTHENTIC. GUARANTEED.", phone showing @kardavenue, App Store + Google Play badges). Every video ends with it, shown full-bleed (9:16) with a slow push-in. No burned-in caption and no logo overlay on it; the voiceover still plays.
- **Brand files live in the skill folder** (`assets/07_kard_logo.png`, `assets/23_follow_us_cta.jpg`) so they don't need re-attaching. If they're missing there, Claude asks once.
- **Never draw App Store / Google Play badges ourselves.** Use the official artwork only.
- Colours: background deep navy/purple gradient with soft bokeh + light grain. Highlight yellow `#FFD84D` for numbers and key words. Pink `#FF5CAA` for the Follow pill. Red `#EB2D3C` for ✗ stamps and arrows. Green for ✓.
- **Fonts: Telegraf** (brand font, bundled in `engine/fonts/`): Telegraf UltraBold for captions (60px, white, 7px dark stroke), headings, labels and numbers; Telegraf Regular / UltraLight available for secondary text. The typed date uses a mono font. Telegraf is wider than Inter, so keep captions tight to stay within 3 lines.

## 6. Assets

**Naming convention** (send in one zip):
```
01_<main card>.png          hero card (≥1000px tall)
02–05_<comparison cards>    other languages / versions (≥700px tall)
06_<booster box>.png        product shot (own stock photo preferred)
07_kard_logo.png            (bundled with the skill — no need to send)
08–10_<artist other cards>
11–19_<set / grid cards>
20_<booster pack>.png
21_<psa slab>.png           optional
22_<artist avatar>.png      from the artist's public profile
23_follow_us_cta.jpg        (bundled with the skill — the end-card CTA, no need to send)
voiceover.mp3               when ready (any tool)
```
- Original files, not chat- or WhatsApp-compressed copies. Card scans ≥ 700px tall; hero ≥ 1000px.
- Claude's workspace **cannot download from TCGplayer / TCG Collector / X / Google Images**; you or an agent must supply files. Claude can convert any format (AVIF/WebP/JPG) and remove backgrounds.
- The Google Drive connector sees only files owned by the connected account. **Attaching files or a zip in chat is the reliable route.**

## 7. Motion & transitions

- **Smooth eases, 0.4–0.6s.** Fades and slides; text rises in with a short stagger.
- **One white flash max per video**, only on the big reveal. **No coloured or stacked flashes** (lesson: the yellow PSA glitch).
- Hook pattern that works: starburst background → known versions pop in with ✗ → blacked-out mystery card + "?" → flash reveal.
- **Don't draw Pokémon characters or silhouettes.** Use the real card art (e.g. a blacked-out card for mystery shots). Reference styles are recreated, not copied.
- Starburst/background layers must cover the full frame while rotating (no exposed corners).

## 8. Sound

- Synthesised SFX kit from `kard-reel-sfx.py` (free): whoosh, impact, stamp, pop, ding, tick, typing, flick, shimmer, riser.
- One sound per visual event, kept under the voice. Big hits only for the reveal; soft whoosh + pop for highlights.
- **Voiceover = any MP3 you attach, no default tool.** Make it wherever you like (Gemini TTS in Google AI Studio, CapCut, ElevenLabs, or a human recording). Claude waits for the file; it doesn't generate the voice unless you ask.
- Delivery to aim for: calm storyteller, ~3 words/sec, "kamu" register, a short pause before the reveal. Export as MP3 or WAV, one file for the whole script, no music.
- *Optional:* a "Kard Avenue Narrator" voice clone (e.g. ElevenLabs Instant Voice Clone from 1–2 minutes of clean Bahasa speech) is one possible source of the MP3. Only clone a voice you own or have written permission to use.

## 9. Deliverables per video

1. MP4 (1080×1920) + web copy for review
2. **Editor page** (artifact): player, clickable scene list (time · voice · caption · visual · sound), per-scene notes, "Copy notes for Claude"
3. Script doc in the project: `claude/video-NN-<topic>-script.md`
4. Post caption (format below)

**Post caption format:**
```
[Hook line + 1 emoji]

[Full card label, PSA style — e.g. 2026 Pokémon Simplified Chinese CSV9.5C Terastal Gathering 234 Sylveon ex SAR — illus. rika (@artist)]

[Product] ready di @[Kard Avenue IG] · Download Kard Avenue di Google Play & App Store

[hashtags for the game, below]
```
`@[Kard Avenue IG]` is filled from the config's `ig_handle` by the `caption` command.

**Hashtags by game** (4–5, always start with `#kardavenue #reels`):
| Game | Hashtags |
|---|---|
| Pokémon | `#kardavenue #reels #pokemon #pokemontcg #pokemonindonesia` |
| Disney Lorcana | `#kardavenue #reels #disneylorcana #lorcana #tcgindonesia` |
| One Piece | `#kardavenue #reels #onepiececardgame #onepiecetcg #tcgindonesia` |
| Other / mixed | `#kardavenue #reels #tcg #tradingcards #tcgindonesia` |

**Stock rule:** "ready / in stock at Kard Avenue" (voiceover, caption, READY STOCK stamp) only after the user confirms stock for that video. The config's `stock_confirmed: true` records it; `check` fails without it when a stock scene exists.

## 10. Pre-posting checklist

- [ ] Length between 45s and 60s
- [ ] Script locked, captions = script (automated check passed)
- [ ] Facts sourced; PSA pop re-checked today, date on screen updated
- [ ] No draft tags; logo on every scene except end card
- [ ] Every card named in the voiceover gets a big frame
- [ ] Nothing below y≈1680 that matters; no caption overlaps
- [ ] Watch once on a phone in Instagram's preview (safe zone, readability)
- [ ] Tag the artist (e.g. @0__rika__0) and add trending audio in Instagram
- [ ] Cover frame: pick a clean frame (hero card) as the Reel cover

## 11. Engine v2.1: how Claude builds a video (no code edits)

A video is **one JSON config**: global settings + a list of scenes. Claude copies the example config, swaps the images and lines, and runs:

| Command | What it does | When |
|---|---|---|
| `python3 kard_reel.py reel.json check` | Lint: 45–60s length, missing/low-res images, missing voiceover file, caption >3 lines or orphan word, VO too fast (>3.6 words/s), cards touching edges/below safe line, anything within 60px of the caption, forbidden words (TGA) | Before every render, must say **OK** |
| `... stills sheet.png` | Contact sheet of **key moments**: each scene type shows its important frames (versions ✗ / mystery / reveal; circle / zoom; each featured card / fan; chart / highlight…), labelled | Check-in 2 |
| `... clip out.mp4 SPEC` | **Partial render** with audio. SPEC = `6` (scene 6), `5-7` (scenes 5–7) or `12.5:20` (seconds) | Reviewing a single-scene fix |
| `... render out.mp4` | Full video + SFX (+ voiceover if set), all CPU cores | After stills approved / final |
| `... cover cover.png` | Reels cover: hero card + title (emoji stripped) | With the final |
| `... script script.md` | Script doc table generated **from the config**, so captions and script can never drift | Every change |
| `... page DIR out.mp4` | Editor page (`index.html` + `scenes.json` + web video), same page every time | Final review |
| `... frame T out.png` | One frame at T seconds | Spot checks |
| `... caption [out.txt]` | Final Instagram post caption, IG handle filled in | With the final |

`check` also fails on missing sound-effect files and on a stock scene without `stock_confirmed`, and warns when the IG handle isn't set. Fonts are bundled in `fonts/` next to the engine.

**Scene types** (fields in brackets):

| Type | Use for | Key fields |
|---|---|---|
| `hook_mystery` | Opening: known versions ✗ then mystery card reveal | `known:[{img,label}]`, `hero` |
| `hero_stamp` | Big card + ✓/✗ stamp | `img`, `stamp:{kind,label}` |
| `product_intro` | Box + pack + typed date | `box`, `pack`, `date_text`, `subtitle` |
| `card_grid` | Up to 9 cards (set overview) | `cards:[img]`, `keep` (index that stays) |
| `card_lineup` | 2–3 cards compared, heading + credit | `cards:[{img,label}]`, `heading`, `credit`, `riser` |
| `reveal_zoom` | Reveal + zoom into a detail (number, stamp, signature) | `img`, `wipe_from`, `zoom:{fx,fy,tag}` |
| `artist` | Artist avatar centred | `avatar`, `name`, `handle` |
| `featured_cards` | Each card full-size, then fan | `cards:[{img,label}]`, `heading` |
| `stat_chart` | PSA pop bars + counter + highlight | `bars`, `total`, `source`, `highlight:{at,lines}` |
| `cta_product` | Product + stamp (READY STOCK) | `img`, `stamp_text` |
| `broll` | Opener: one slow, steady left-to-right pan across the card, soft fade in (≈2s, carries the start of the hook line) | `img`, `pan:{fx0, fx1, fy, h}`, `caption_bg: true` |
| `end_card` | Closing call to action, every video (full-bleed FOLLOW US! poster, no caption burned in) | `img: 23_follow_us_cta.jpg` |

Every scene also has `dur`, `beat`, `vo` (Bahasa, "kamu") and `caption` (EN). Use `continue_caption: true` to hold the previous caption across a scene. Global options:
- `caption_mode`: `lines` or `chunks`. Chunks are 2–4 word captions, used once the voiceover exists.
- `voiceover`: the attached MP3/WAV, mixed in with sound effects ducked under it. `voiceover_offset` shifts it (seconds).
- `highlight_words`: words shown in yellow.
- `forbidden_words`
- `cover:{img,title}`
- `post_caption`
- `open_decisions`
- `stock_confirmed`: `true` once the user confirms the featured product is in stock
- `ig_handle`: Kard Avenue's Instagram handle, e.g. `"@kardavenue"`

**After the voiceover arrives:** Claude finds where each line starts (pauses via `ffmpeg -af silencedetect`, or the ElevenLabs transcription tool if connected), sets each scene's `dur` to the voice timing (staying inside 45–60s), sets `caption_mode: "chunks"`, adds the `voiceover` path, re-runs `check`, then renders.

**New scene type needed?** Claude adds one draw function + its `_sfx` list + its `_keys` list (stills moments) to the engine and documents it here. It doesn't hand-edit timelines.

## 12. Suggested improvements for next videos

- **Make the cover frame intentional:** a 1s title frame or a clean hero shot so the Reels grid looks consistent.
- **Loop-friendly ending:** end on a frame that flows back into the hook (raises replays).
- **Word-chunk captions** (2–4 words, synced to the voice) once the voiceover exists, like the reference.
- **A series format** ("Cuma ada di China #1, #2…") reuses the same engine with new assets.
- **Batch production:** prepare 3–5 scripts at once, then render them in one session.
- **Own footage when possible** (hands tilting the real card) beats scans for trust, since Kard Avenue's brand is authentication.


## 13. Motion & sound defaults (from Video 04 feedback)
- **Scene transitions:** every cut is a 0.45s dissolve (`"xfade": 0.45`). Logo stays fixed on top and fades out only into the end card.
- **Captions:** fade + small rise in (0.28s), quick fade out when the next chunk comes. No scale pop.
- **Sound:** `"sfx_style": "soft"`, `"sfx_gain": 0.5`. A light sound on every card motion, nothing when nothing moves: `swoosh` (airy) when a card arrives, sweeps or a zoom starts; `tap` (soft card tap) for each card flying into a grid or the circle callout; `drop` (water drop) when a badge, tag or avatar appears. No riser, impact, shimmer, stamp or ding.
- **B-roll opener:** a simple, slow left-to-right pan (`pan: {fx0: .36, fx1: .64, fy: .42, h: 2600}`), never jumpy multi-shot close-ups. It keeps moving under a longer 0.9s dissolve into the full card (`"xfade_in": 0.9` on the next scene).
- **Artist photo:** never stretched. Square crop with the face kept whole (`avatar_crop: [cx, top, size]` as fractions; default is a centred square from the top).

## 14. APPROVED DEFAULT STYLE — Video 05 v6 "3D thefinecard" (engine v3) — keep until the user says otherwise
Approved 29 Oct 2026 on Video 05 (Illustration Contest 2024). Every new reel starts from `engine/example_3d_illustration_contest.json` and keeps this level of motion, drama and finish unless the user asks for a change.

**Look**
- Dark navy background (no `bg_image`), warm bokeh: `"bokeh": [[255,170,80],[120,90,220],[255,90,140]]`.
- `"camera": {"punch": .03, "punch_t": .5, "breathe": .01, "drift": 4, "base": 1.02, "grade": {"sat": 1.1, "contrast": 1.08}}` — small zoom-settle on every cut, gentle handheld drift, light colour grade. Never dizzying.
- Captions: `"caption_style": "plain"`, `"caption_size": 50`, `"chunk_words": 4` — small plain white, soft shadow, no panel, no yellow words.
- `"xfade": .35`. Per-scene `"trans": "whip"` (motion-blur slide, `xfade_in` .25–.35) or `"leak"` (warm orange light leak, `xfade_in` .45). Mix them; don't use the same one twice in a row.
- Sound: `sfx_style: soft`, `badge_sfx: "pop"`, `cut_sfx: "swoosh"`, `sfx_gain` ~.55, `highlight_sfx_once: true` (circle/tag highlight sound only the first time).
- **Never stretch anything.** All 3D uses true rotation (proportions kept). Full-bleed close-ups scale evenly to cover; objects shown whole use `"cover": false`.
- Card scans: cut the white scan corners to transparent PNG before use (flood-fill from corners).

**Scene types added in v3**
| Type | Use | Key fields |
|---|---|---|
| `macro3d` | Tilted 3D close-up of a card/pack with depth of field; the camera keeps moving | `img`, `from`/`to`: `{fx, fy, h, rot, tx, ty}` (tx/ty = yaw/pitch, ±.2 max), `focus: {axis: x|y, at, at1 (rack focus), width}`, `dof` (px), `cover` (false = whole object, e.g. pack turntable) |
| `slam` | Drama hit: big words slam in with shake over dim cards + red tint | `words: ["BUT THEN…", "DRAMA"]`, `cards`, `at`, `shake: 1`, `shake_at` |
| `wall` | "Many entries" beat: blacked-out cards on a tilted wall, counter, rapid ✗ stamps, glitch bursts | `cards`, `counter`, `count_end`, `x_at`, `x_step`, `x_tiles` (keep in the middle rows), `tilt`, `scroll`, `glitch: [[t0,t1],…]` (short, ≤.15s each) |

**Options added to existing scenes:** `hero_stamp` `reflect: true` + `h` (glossy floor reflection); `card_grid` `soft: .45` (items fade/rise in one by one); `reveal_zoom` `zoom.pan: .07` (slow left→right drift while zoomed); any scene `mono: true` / `mono_at` (desaturate), `tint: [r,g,b,a]`, `shake`, `glitch`, `punch`. Global: `float` (idle bob), `confetti`, `rays`, `bg_image` exist but are OFF in this style.

**Approved Video 05 structure (pattern to reuse):** macro3d hook (face) → whip → reflect hero + badge → leak → macro3d detail stamp → whip → macro3d tilt-down art → grid (facts as badges) → slam "BUT THEN… DRAMA" → wall (counter / ✗ / glitch) → leak → reflect hero (winner) → whip → macro3d with badge → whip → macro3d rack-focus pan (card 2) → whip → macro3d swing (card 3) → leak → macro3d pack turntable (`cover: false`) with date badges → soft one-by-one grid payoff → end card.

**Performance:** macro3d renders straight from the source scan in one warp (~0.4s/frame); a 53s reel renders in ~8–10 min. Use `clip` for single-scene reviews.

**Asset wish list (improves this style most):** scans ≥2000px tall (close-ups enlarge 4–6×), phone footage of a hand tilting each card/pack over a dark table, screen recordings of official results pages. Never use others' event photos without rights.


## 15. APPROVED DEFAULT STYLE — Video 06 Delta Reign "brand mono" (engine v3.1), approved 2 Nov 2026
Supersedes §14 colours and sounds; all §14 motion rules still apply.

### Engine v3.1: new features and config keys

| Key | Where | What it does |
|---|---|---|
| `"bg_color": [[26,26,26],[10,10,10]]` | global | Flat brand background (centre → edge). #0a0a0a black. Replaces the navy gradient. |
| `"bokeh": [[250,250,250],[150,150,150],[210,210,210]]` | global | Neutral soft light spots (no colour). |
| `"mono_ui": true` | global | Highlight badges and the cover title use #fafafa instead of yellow. |
| `PAPER` / `INK` constants | engine | #fafafa / #0a0a0a used for all text, chips and captions (chip = #fafafa bg, #0a0a0a text). |
| `"slam_tint": [20,20,20]`, `"slam_color": [250,250,250]` | global | Slam scene: dark tint + white words (no red). |
| `"leak_color": [255,236,210]` | global | Light-leak transition colour (soft white, not orange). |
| `"cols": 2`, `"col_gap": 375` | `card_grid` | 2×2 (or any column count) grids. Used for the 4 Mega ex. |
| `"crowd": {cards, h, cols, alpha, speed, blur, tilt}` | any scene | **Moving crowd of cards** behind the scene: columns drift up/down in opposite directions on a slight tilt, dimmed. Fixes "empty / boring" scenes. Negative `speed` reverses direction. |
| `"flare": {t0, t1, y, strength, color}` | any scene | Warm anamorphic lens flare sweeping across (glow + streak + ghost orbs). Paired with the fire whoosh at the start. |
| `"sfx": [[t, "name", gain]]` | any scene | Extra per-scene sounds (e.g. `fire_long` on the hook, `reveal` on a card reveal, `coin` on products). |

### Sound map (user's pack → engine names)

| Engine name | Source file | Used for |
|---|---|---|
| `swoosh` | whoosh-1.mp3 | Scene cuts (`cut_sfx`), card moves |
| `shutter` (also `tap`) | camera-shutter-dslrr.mp3 | Every badge (`badge_sfx`), grid cards landing |
| `coin` (also `drop`) | coin_1.mp3 | Products / pack counts |
| `fire` (also `impact`) | fire-whoosh.mp3 | Slam ("TOP CHASE") |
| `fire_long` | fire-whooshing.mp3 | Hook macro (fire art) |
| `reveal` | magic-reveal-audio.mp3 | Big card reveal, Kyogre promo |
| `metal_whoosh` | ambient-metal-whoosh-2.mp3 | Box turntable |
| `sent`, `bit8` | mail-sent.mp3, 8-bit-sound.mp3 | Not used yet |

### Playbook additions (new §15: Video 06 style, approved 2 Nov 2026)

- **Colours:** Kard Avenue essentials only: black #0a0a0a background, white #fafafa for all text, badges and captions. Captions white only (no highlight colours). Colour comes from the card art.
- **Never leave a scene empty:** grids, slams and simple hero shots get a moving `crowd` of real set cards behind them.
- **Products:** one scene per product (3D turntable, `cover: false`), each with its own caption and label, never one combined layout.
- **"What's inside" montage:** one quick 3D-turntable shot per item, in the same order as the voiceover, ending on the promo card with a close-up pan. Add short pauses in the VO between items so it isn't rushed.
- **Comparing two versions of a card:** use slow text pans (macro3d across the printed text), English first, then the other language.
- **Hook:** slow, relaxed push-in on the Pokémon's face (small zoom, almost no rotation, wide focus band), with a lens flare matched to the opening sound.
- **Captions:** one caption per shot, split so each line matches what is on screen (never let a long line spill across several shots via `continue_caption` chains).
- **Voiceover over 60s:** shorten silent gaps (never speed up the voice), keep ~0.1s between phrases.
- **Timing without a transcription tool:** use `ffmpeg silencedetect` (n=-32dB, d=0.07–0.12) to find phrase boundaries, then set each scene's start and `vo_window` to the phrase it shows.


## 16. APPROVED STYLE UPGRADE — Video 11 Mitsuhiro Arita (engine v3.2), approved 13 Nov 2026
Builds on §15 (brand mono) and §14 motion. Reference config: `engine/example_editorial_arita.json`.

### Engine v3.2: new features and config keys
| Key / type | Where | What it does |
|---|---|---|
| `"trans": "glitch"` | any scene | Digital glitch cut (RGB split + torn bands, hard switch mid-way). Pair with `sfx [0,"bit8",.35]`. `xfade_in` .25–.3 |
| `"trans": "zoom"` | any scene | Punch-zoom cut: old shot rushes at camera, new one settles in. `xfade_in` .3–.35 |
| `macro3d` `"card": false` | scene | Use the image flat (no rounded card corners) — for article screenshots, artworks, sprites |
| `macro3d` `"highlight": [{box:[x0,y0,x1,y1], t0, dur}]` | scene | **Editorial highlighter**: bright yellow marker sweeps across the words (multiply, text stays black). Boxes are fractions of the image — **measure them with OCR (tesseract), never estimate** |
| `"follow": true` | macro3d + highlight | Camera glides along each line in sync with the marker, then to the next line. Set each `t0/dur` to the VO phrase (silencedetect) |
| `"noir": true` | macro3d + highlight | Detective look: page drained + darkened; only the line being marked is bright, lightly bold and yellow |
| `"spot": {w, h, dark, flicker}` | macro3d | Spotlight on the line + heavy shadow closing in from the edges |
| `macro3d` `"plane": 2.2, "cover": false, "focal": 2600` | scene | **Fly-over**: card lying almost flat (`ty` ≈ 1.35) seen from its bottom edge, camera rises and pushes forward to near-frontal (`ty` ≈ .2, bigger `h`) |
| `artist` `"cutout": true` | scene | Artist photo as a scissor-cut paper cut-out (`photo_crop`, `photo_h`, `photo_y`, `name_y`) |
| `card_wall` | scene type | Full-screen wall of cards on black, slow drift, 3D tilt that changes axis, black fades top/bottom (`cards`, `tile_h`, `cols`, `drift`, `tilt:{tx0,tx1,ty0,ty1}`) |
| `mono_ui: true` | global | Now also turns every accent (yellow/pink/red role text, callout circle and tag) white; navy/purple tints removed engine-wide |

### Rules learned on Video 11
- **Opening shot:** the fly-over above (bottom-right → top-left, steep flat angle → close near-frontal). No lens flare.
- **Mix the cards:** never repeat the same card scene after scene; use many TAG TEAM GX cards and other eras.
- **Vary the 3D moves by axis:** yaw swing, pitch tilt-down/up, roll, diagonal push, turntable, straight push-in — and move the focus. Mix transitions (glitch / zoom / whip / leak), never the same twice in a row.
- **Editorial beats (articles/interviews):** zoom close (text large), detective noir + spotlight, yellow marker exactly on the words (OCR boxes), camera follows the text with the voice, highlighted line lightly bold only. Paint out cursors in screenshots. Credit the source on screen (`SOURCE: … , YEAR`) and get permission before posting.
- **Highlight sound:** one smooth, quiet, bright sweep (no bass, no scratchy texture) lasting exactly the marker stroke; soft swoosh when the camera moves to the next line.
- **Callouts:** zoom exactly on the detail (e.g. energy symbols); prefer a card where the detail is most interesting (mixed energy types on a TAG TEAM card).
- **Strictly black/white UI and backgrounds;** colour only from the art (and the yellow highlighter).
- **Trial Reel:** different hook + hook edit only; slower opening shots; no cover needed.

### Cover (main Reel only)
Yuka Morii / Atsuko Nishida layout: two big glowing cards (mirrored ±8°) running off the edges behind a **large** artist photo (starts just under the logo, objects fill ~y 370–1300), soft fade to black, ARTIST SPOTLIGHT pill, NAME in uppercase, light Bahasa tagline. **Background must differ from earlier covers** and never feel empty: Video 11 used TAG TEAM GX cards flying at different depths + soft light rays + particles, kept dim.

## 17. MOTION LIBRARY — Video 12 "Ranked Countdown" (engine v3.3), added 16 Nov 2026
Builds on §16. Same pillar (verified card stories, brand-mono look), a different pattern per topic. Reference config: `engine/example_countdown_most_graded.json` (its card file names are placeholders; swap in real scans). Status: layouts built and checked with placeholder cards; not yet approved on a finished video.

### Pick a pattern per topic (never the same one twice in a row)
| Pattern | Use for | Reference |
|---|---|---|
| Artist Spotlight | one illustrator's story | `example_editorial_arita.json` (§16) |
| Set preview | a new set and its products | `example_brand_mono_delta_reign.json` (§15) |
| Ranked Countdown | top-N lists, data stories | `example_countdown_most_graded.json` (this section) |

### Engine v3.3: new scene types
| Type | Use | Key fields |
|---|---|---|
| `rank` | One countdown beat: giant outlined rank numeral behind a card that swings in in true 3D; the counter rolls to the exact count | `n`, `img`, `count`, `unit`, `enter` (left/right/top/bottom), `side` (1/-1: where the numeral peeks out), `swing: [tx0, ty0, tx1, ty1]`, `h`, `count_at`, `count_dur` |
| `bar_race` | Comparing two numbers: bars grow at the same speed, so the bigger one visibly overtakes | `bars: [{label, value, win}]`, `img` (card above), `race_dur`, `start`, `source` |
| `leaderboard` | Ranking board the video keeps returning to; the bar scale can "zoom out" | `rows: [{rank, name, value, lit, hide, at}]`, `title`, `bars`, `max0` → `max1`, `scale_at`, `scale_dur`, `step`, `source` |
| `coverflow` | 3D carousel: centre card faces the camera, neighbours turn away; advances card by card | `cards`, `labels` (big text over the centre card), `step`, `h` |
| `deal` | Cards dealt from the corners slap down onto a centre pile, each at its own angle | `cards`, `step`, `start`, `h` |
| `conveyor` | "One every N seconds": cards ride a belt in perspective; a ring timer restarts and a counter ticks per card | `cards`, `period`, `h`, `ring: {secs, unit}`, `counter: {label}`, `tilt` |

Also new: `"max_len": 75` in the config raises the 60s limit for one video; `check` now accepts `mystery:` / `flip:` image prefixes.

### Rules learned on Video 12
- **Do not overuse the card wall.** `card_wall` and the moving `crowd` background read as the same frame. Use that look at most once per video; pick `deal`, `coverflow`, `conveyor`, `rank` or a `macro3d` move for the other "many cards" beats.
- **Every repeated beat gets a different entrance.** In a countdown, each `rank` scene uses a different `enter`, `side`, `swing` axis and transition.
- **Longer cut on request:** up to 75s when the user asks, so each scene holds 3–6s and transitions are not rushed. Add pauses, not words; never speed up the voice.
- **Data stories:** exact counts, the month and source on screen ("PSA · JUNE 2026"), and a monthly figure is never presented as all-time. Derived numbers (e.g. "one every 18 seconds") are labelled as averages in the voiceover.
- **Comparisons with athletes or other real people:** names as text only, no photos.
- **Hooks for lists:** never tell the viewer they already know the answer; lead with the surprise in the middle of the list.


## 18. Video 13 "TAG TEAM GX" (engine v3.4), approved 16 Nov 2026
Builds on §16–§17. (v3.4 features were rebuilt in engine v3.5/v3.6, see §19.)

### Engine v3.4: new features
| Key / type | Where | What it does |
|---|---|---|
| `versus` | scene type | Pair face-off: two cards slide in from opposite edges, turned toward each other in true 3D, meet as equals; divider + joiner ("+"), name chips. `cards: [A, B]`, `labels`, `joiner`, `h`, `gap`, `joiner_at`, `label_at` |
| `deal` `counter: {label}` | scene | Counter ticks up as each card lands (e.g. "9 · NEW TAG TEAM-GX") |
| `slam` `rain: {cards, n, h, alpha, front, seed, slow, slow_len}` | scene | Cards dropping from the top like real cards (air drag + terminal speed, 3D flutter/tumble, sway, spin), 3 depth layers + blurred foreground cards in front of the words, motion blur, slow-motion beat when the words land |
| `hl_bold: false` | macro3d + highlight | Marked text keeps its normal weight (no bold) |

### Rules learned on Video 13
- **Editorial highlight:** one continuous marker stroke per spoken line, camera sweeping smoothly with it. No step-by-step "cut cut" camera moves between short strokes. Marked text stays normal weight (`hl_bold: false`).
- **Editorial on card text works:** noir + spot + marker on a card's rule line (OCR boxes from a 5× upscale of the scan).
- **Slams can feel empty.** Use the falling-cards `rain` on at most one slam; for other dramatic beats prefer a different motion (e.g. a `rank`-style giant outlined numeral behind a card).
- **Don't repeat the same card scans close together:** when a card is named again later, show the Japanese print instead.
- **Fact wording on screen must not overclaim:** say "considered" when a source says "explored"; say "standard art" when only regular prints are by the artist.
- **Don't reuse facts** already used in an earlier video on the same artist.
- **Cover:** artist photo with background cut out (flood fill from edges), solid until ~83% height then a short fade; two glowing TAG TEAM cards mirrored ±8°; dim multi-depth TAG TEAM background.


## 19. Videos 14–15 Riftbound (engine v3.5 → v3.6), approved 18–20 Nov 2026
Builds on §16–§18. Engine: `engine/kard_reel.py` v3.6; reference config `engine/example_rivalry_lore_vendetta.json`.

### New pattern: Rivalry Lore (Video 15)
One story per reel. Teammate feedback on Video 14: visuals and card zooms great, but a "two sets in 75s" overview script reads like a spec sheet. Split broad topics into separate reels (Vendetta rivals → K/DA → Heartsteel), each with lore/story, then the product.

### Engine v3.5 / v3.6: new scene types and keys
| Key / type | Where | What it does |
|---|---|---|
| `versus` | scene | Pair face-off (v3.4, rebuilt): two cards slide in turned toward each other, joiner (`VS`, `+`, `?`, or ''), labels; balanced on the pair's total width; `card: false` for products; `enter: vertical`; `in_dur` (entrance speed, default .7) |
| `versus_rows` | scene | Two face-offs stacked; each row appears at its own `at` (when that pair is spoken). Use when a line names two pairs fast ("Zed lawan Shen. Nasus lawan Renekton!") |
| `diptych` | scene | Two connecting-art cards (Riftbound Rival/Connecting Overnumbers) drift in, slide together and join into one painting, light sweep over the seam. `join_at` (on the spoken words), `approach` (1.5s), `rest_gap`, `label`, `label_at` |
| `shadow_clones` | scene | Card in colour; darkened red-tinted copies fan out to both sides with ghost trails, shadows creep in from the edges. `clone_at`, `spread`, `tint` |
| `seal` | scene | Procedural carved stone doors (Shurima gold inlay) slam shut over a card (`mode: close`, `seal_at`, dust + thread of light) or grind open with light from the seam (`mode: open`, `open_at`) |
| `slam` `rain` | scene | Falling-cards background (v3.4, rebuilt) — at most one rain slam per video |
| `deal` `counter: {label, y}` | scene | Counter ticks up as each card lands |
| `coverflow` `start`, `label_y` | scene | Delay the carousel so each centred card matches its spoken name; labels below the card |
| `card_lineup` cards `at` | scene | Per-card label time (e.g. each mechanic label on its word) |
| `rank` `num_y`, `num_alpha` | scene | Move the outlined numeral above a wide (landscape) card |
| `"caption_shadow": "strong"` | global | **Default from now on:** white captions with a wide soft dark glow + tight drop shadow, **no box** (`caption_bg` removed everywhere) |

### Rules learned on Videos 14–15
- **VO sync (critical):** never estimate where lines fall from expected durations. Map every script line to the real audio: `silencedetect` pauses + syllable-beat counts per speech segment (band-passed envelope peaks), matched to each line's syllable count; landmarks (lists of names, short bursts) confirm the map. Then verify after the render: no speech may cross a scene cut except a deliberate mid-sentence split, and check frames at cue words (names, joins, counters) in the final MP4. Video 14 v1 slipped one line from the 3rd line on and had to be redone.
- **Fast VO beats:** if a line is spoken faster than its visuals can enter (e.g. 1.2s for two pairs), start the shot earlier by shortening the previous shot and speed the entrance (`in_dur` ≈ .35–.45) so cards are fully in before the name is said.
- **Opening shot (updates §16):** reversed fly-over — the card starts close on the viewer's side, then pulls back and tips away (Video 14 feedback).
- **Captions:** plain white + strong shadow, never a box.
- **Blurry scans that get zoomed:** upscale with Real-ESRGAN x4 (weights from the GitHub release, CPU torch) before close-ups/signature zooms.
- **Signed cards:** when the VO mentions signatures, show the signed card and zoom onto the signature, tagged with the artist's signature name.
- **Lore facts:** check against the official biography text (League wiki mirrors of universe.leagueoflegends.com) plus 2 more sources; prefer official product copy for product claims. Keep the simple official version of a story (no later retcons) unless asked.
- **Diptych/connecting cards:** confirm both halves line up before building; place the join on the words "satu lukisan" / the payoff question.
- **Highlight on yellow text** (e.g. Riftbound title bars): use `noir` so the marker is visible.
- **Landscape battlefield cards** show upside-down text in macro shots — use a portrait card for close-ups.
- **Cover (card-focused, Video 14/15):** balanced spacing — in the 3:4 grid crop the gap above the cards equals the gap below the title; two-line title lines tight (≈100px apart at 112px). Background: split blurred art of the two sides (left/right) + soft stage rays + mirrored floating cards + sparkles. Product box can be the hero in front of two tilted signed cards. Title in Bahasa question form ("KAMU TIM ZED / ATAU TIM SHEN?").
- **Trial Reel:** user records only the new hook lines; splice them in front of the main VO from line 3 on, with a slower opening (longer lead and pauses); re-verify sync; publish a trial editor page too.
- **No prices in Riftbound reels** (user request); "segera hadir" until stock arrives.

## 20. Video 17 HEARTSTEEL x Riftbound (engine v3.7 → v3.8.1), approved 25 Nov 2026
Builds on §16–§19 (everything there still applies). Engine: `engine/kard_reel.py` v3.8.1. Example configs for a full Reel are in `examples/video17/`: `reel.json` is the main Reel and `reel_trial.json` is the trial. The `gen.py` / `gen_trial.py` scripts that built them are there too.

### New scene types

| Type | Use | Key fields |
|---|---|---|
| `player_freeze` | **Hook: a video player.** A drawn video-player frame plays an artwork with cards sitting in it. The picture freezes, brackets snap onto one card, and the camera dives into that card. With `pop` it works as a teaser instead: the cards pop into the frame one by one. | `img`, `cards` (list of images), `zoom_card` (index), `freeze_at`, `zoom_at`, `card_h`, `card_y` (0–1 inside the player), `title` (player bar text), `y`, `pw`/`ph` (player size). Teaser fields: `pop: [t…]`, `p0`/`p1` (camera push), `spread` |
| `spotlight` | **Roll call on a group artwork.** The camera moves to each member as he is named. In trace mode the member is lit inside his own outline (with a rim glow), the rest of the picture drops into shadow, and a name chip appears. | `img`, `targets: [{x, y, cx, cy, label, at, mask, rim}]` (`cx`/`cy` = camera framing point; aim so head + body fit and nothing sits on the logo), `h0`/`fy0` (opening wide shot), `h1` (close-up height), `dim`, `rim`, `label_y`. **Logo drive-through:** `overlay: {img, at, w, y, out, dur}`. The logo holds still, then blurs and fades while the camera zooms "through" it, and the blackout fades in (it doesn't pop) |
| `flip` | **Makeover / before→after.** Cards turn over in true 3D from one version to another. | `pairs: [{from, to, at}]`, `h`, `gap`, `y` |
| `spot_groups` | **"Who's who" beat.** One continuous shot over a group artwork. At each step a *set* of members stays lit inside their outlines and the rest drops into shadow. Optional name/role chips pop under them, and the camera glides between keyframes. | `img`, `cam: [[t, fx, fy, h(, 'lin')]…]` (`'lin'` = constant-speed drift into that key; otherwise eased; keep the art covering the frame once `h` ≥ 1920 because there are no hard edge clamps), `groups: [{at, lit: [keys], chips: [{label, x, at, stay}]}]`, `dim`, `rim`, `label_y`, `mask_fmt`/`rim_fmt` (default `hsmask_{}.png` / `hsrim_{}.png`). If `h` < 1920 the picture is framed over its own blurred copy |
| `stage_table` (v3.7) | Stage → table reveal (Video 16 K/DA). | see the Video 16 config |

**Masks for `spotlight` / `spot_groups`:** use `tools/make_masks.py ART.png boxes.json --preview`.
- `boxes.json` holds one loose box per member, in 0–1 fractions of the art. Each box must contain the whole figure; anything outside it is cut.
- The tool uses rembg with the `isnet-anime` model for illustrations, or `isnet-general-use` for photos.
- Always check the preview. Then re-run single members with `--only key` if a mask leaks.
- `tools/hs_boxes.json` is the Video 17 example. It reproduces the six HEARTSTEEL masks with IoU 0.74–0.86 against the hand-tuned ones.

### New options on existing scenes
- **`card_lineup`**
  - `rows: 2` + `row_gap`, `spread`, `fan`: two rows of 3 big cards that fill the frame (no empty band above or below).
  - `t0` + `step`: when the cards start landing and the gap between them (the tap sound follows).
  - `bg_img`: blurred art behind the cards instead of black.
  - Fans of 4–5 cards are also supported.
- **`macro3d` highlight**
  - `style: 'band'`: a translucent marker band, for light text on dark card areas (multiply only works on dark text over light).
  - `spot: {w, h, dark, y}`: a spotlight on the text, so a dark card isn't all dark.
  - Measure `box` on the actual scan: draw the boxes over the image and check them before rendering.
- **`deal`**: `y`, and `qmark_at` (a mono white "?" over a mystery card).
- **Badges**: `until` (badge leaves early).
- **Captions**
  - `caption_groups: [[text, t0, t1]…]`: two caption lines inside one merged scene.
  - `chunk_list`: hand-set caption chunks. Use it to keep a name such as "Anderson .Paak" on one line.
  - Captions now split only on spaces, so a non-breaking space also keeps words together.
- **Conveyor**: the ring and counter can be turned off. **`rank`**: depth entry and prefix.

### Fixes
- **Memory:** long zooms over large art grew the `scaled` cache until a render worker died and the render hung. Trace masks are now warped from a half-res copy (`trace_src`), and the cache is cleared when it holds more than 30 entries.
- **Spotlight offset:** the spot is now drawn with the `OY` offset.
- **`spot_groups` camera:** no hard edge clamps (they made the camera jump when the art crossed the frame size).

### Workflow learned on Video 17
- **VO retiming** (`examples/video17/retime.py`)
  - Find speech segments with silencedetect (`n=-38dB`, `d=0.12`). Get syllable beats from `beats.py`, at about 0.77 beats per syllable.
  - Map every script line to its segments and check each line by its beat count; one line was mis-split in Video 16.
  - Rebuild the VO with a gap table `G` (line-to-line pauses).
  - Scene boundaries sit at the midpoints of the gaps between speech.
  - Cues are mapped through `M()`. Names in a roll call get gaps of at least 0.3s.
- **Re-recorded line:** append it to the raw VO file at a fixed offset and point that line's segment at it. Match loudness with ebur128.
- **Trial Reel:** the user records only the new hook lines (plus an optional bridge line).
  - `retime_trial.py` puts them in front of the main segments.
  - `gen_trial.py` execs `gen.py` with string replacements.
  - Merge any two lines that share one image into one continuous scene.
- **Small fixes without a full re-render**
  - Render only the changed range: `clip OUT.mp4 a:b`, starting before the scene and ending after the next transition.
  - Splice it in with ffmpeg, using `-t a` on the first input and `-ss b` on the third. Do not use two `trim`s on the same input; that buffers every frame and gets the process killed.
  - Copy the audio from the original.
- **User feedback to apply by default**
  - Fill the frame; no big empty bands.
  - Close-ups frame the head and body and never overlap the Kard Avenue logo.
  - Trace or outline the subject instead of using a round spotlight.
  - Never show the same image across two scenes in a row; make it one continuous shot.
  - Use a glitch between hook scenes.
  - Highlights sit exactly on the text.
  - Camera moves never stop and start mid-beat.
