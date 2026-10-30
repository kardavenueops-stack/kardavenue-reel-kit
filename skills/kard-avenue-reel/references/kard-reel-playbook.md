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

- **Kard Avenue logo** (white, transparent PNG) **top-left** on every scene: x 60, y 120, width 300, 85% opacity.
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
