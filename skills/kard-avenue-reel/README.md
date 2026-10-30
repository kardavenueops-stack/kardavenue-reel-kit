# Kard Avenue Reel — shareable skill package

Everything another Claude needs to make Kard Avenue card-story Reels: 9:16, 45–60s, Bahasa voiceover ("kamu"), English captions, thefinecard storytelling style.

## Start here (for Claude)
1. Read `SKILL.md` — the step-by-step workflow with three approval stops (script lock → stills → final).
2. Read `references/kard-reel-playbook.md` — all house rules. **It wins over anything else**, including old script docs.
3. Use the engine in `engine/` (no code edits; one JSON config per video).

## Contents
| Path | What it is |
|---|---|
| `SKILL.md` | The skill: workflow, check-ins, hard rules |
| `references/kard-reel-playbook.md` | House rules: format, script, layout, branding, assets, motion, sound, checklist, engine commands |
| `references/reference-thefinecard-style.md` | Script structure and voice reference |
| `engine/kard_reel.py` | Renderer (v2.1): `check`, `stills` (key moments), `clip` (partial render), `render`, `cover`, `script`, `page`, `frame`, `caption` |
| `engine/fonts/` | Telegraf (brand font for all video text), Inter Bold (stills labels) and DejaVu Sans Mono (typed date). Keep next to `kard_reel.py` |
| `engine/editor_template.html` | Review page with per-scene notes (published by `page`) |
| `engine/make_sfx.py` | Generates the 10 sound-effect WAVs (run it inside an empty `sfx/` folder) |
| `engine/example.json` | Example config (Chinese Sylveon reel) to copy |
| `assets/` | Brand files: `07_kard_logo.png`, `23_follow_us_cta.jpg` (add them if missing) |

## Requirements
Python 3, Pillow, numpy and ffmpeg. Fonts are bundled. Works on Linux, macOS and Windows. If the agent can't run Python/ffmpeg, `SKILL.md` §0 says what it does instead (script only).

## Set once per team (in each video's config)
- `"ig_handle": "@yourhandle"` — fills the post caption
- `"stock_confirmed": true` — only after confirming the featured product is in stock

## Quick test
```
mkdir work && cd work && cp -r ../engine/* . && mkdir sfx && (cd sfx && python3 ../make_sfx.py)
# put card images + brand files in work/assets/, then:
python3 kard_reel.py example.json check
python3 kard_reel.py example.json stills stills.png
```

## Using it in Claude
- **claude.ai:** Settings → Capabilities → Skills → upload this folder as a zip (it must contain `SKILL.md` at its root folder).
- **Claude Code / other agents:** place the folder in the skills directory, or just attach the zip and say "read README.md and follow SKILL.md".
