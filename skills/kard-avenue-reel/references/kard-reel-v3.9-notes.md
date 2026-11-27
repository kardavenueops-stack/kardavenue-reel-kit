# Kard Avenue Reel engine v3.9 — Video 18 (Mangaka × Pokémon) update

Approved on 26 Nov 2026 (Video 18 v4). This builds on v3.8.1 from `kardavenueops-stack/kardavenue-reel-kit`.

## What's in this package

| Path | What it is |
|---|---|
| `engine/kard_reel.py` | Main engine v3.9 (replaces v3.8.1) |
| `engine/worlds.py` | New: procedural monochrome "worlds" and 3D card helpers; renders frames for `prerender` scenes |
| `engine/living.py` | New: layered 2.5D living-card renderer (traced character layer + parallax plate, camera-only motion) |
| `tools/trace_mask.py` | Traces a glyph mask from coloured print for `lift` highlights |
| `examples/video18/` | `gen.py` (config builder), `reel.json` (final config), `prep.py` (asset prep), the two traced Sunday masks |
| `editor_template.html` | Review/notes editor page |

## Engine changes (`kard_reel.py`)

- **`prerender` scene type.** It plays a folder of JPG frames (`f_0000.jpg…`, 30 fps, nearest-frame fallback) inside the normal flow, so it gets the same captions, badges, logo and transitions. `frames` is a path relative to `assets/`.
- **New transitions:**
  - `ink`: an ink-bleed wipe
  - `focus`: a defocus cross-dissolve
  - `page`: a page turn
  - `iris`: an iris open
- **Highlight styles on `macro3d` article/insert shots:**
  - default: the multiply marker. It now takes `hl_boost` (brightness) and `hl_glow` (a soft bloom), so the highlighted words are the brightest thing on screen.
  - `style: 'band'`: a translucent band for light text on dark art.
  - `style: 'lift'`: no marker. The object is shown in its real colours, brighter, on the dimmed page.
    - `mask: 'file.png'`: a traced glyph mask, the same size as the image, so exactly the letters light up. Use it for coloured print such as magazine lettering.
    - `text_only` plus `colors`: a quick colour-class mask when there is no traced mask.
- **Noir page** is darkened to 0.30. `spot` sizes are in pixels (for example `w 1050, h 340, dark .80`); never use fractions there.
- **`caption_groups`** on any scene: `[[text, t0, t1], …]`, so captions follow the voice inside one long scene.
- Small fixes: `card_lineup` takes `enter_y`, and the description lookup uses `DESC.get`.

## `worlds.py` (new)

- **Worlds:** manga panels, noir desk with rain, charcoal bokeh, ink action, arena spotlights, gallery wall, studio. All are monochrome; colour comes only from the cards.
- **`card3d`:** a physical card with thickness, soft shadow, optional reflection, light sweep and glow. **`focus_blur`:** depth of field along x or y.
- **Scene recipes from Video 18:**
  - `S_versus`: a split screen, two full-height close-ups panning in opposite directions, subjects at the same height.
  - `S_flip`: macro close-ups gliding over the real JP card back (logo slide, Poké Ball push, low sweep), a pull back to the whole card, then a flip to the new card on its name.
  - `S_payoff`: a 3D showcase ring. On each name the ring swings that card to the front and the B/W cover inks into the card. After the last name it opens into a drifting fan, so it never sits still.
- **`FOOTERS` / `footer()`:** the bottom two-line credit line (for example "CHAPTER 01 · GOSHO AOYAMA" / "DETECTIVE CONAN · SINCE 1994"). The bottom band is never left blank. `frame=True` adds the dashed outline frame (used on the opening hook).
- **Run:** `python3 worlds.py NAME OUTDIR [t1 t2 …]`. With times it renders only those frames, which lets you split a scene across CPUs or resume.

### v3.9.1 additions (after the photos and the trial, 26–27 Nov 2026)

- **`popout()`:** a small scissor-cut photo frame. The person (a background-removed cut-out) is scaled up inside it, and their head and shoulders break out over the top edge. `shift` moves the person sideways so the body isn't cropped; `poff` is for extra rows added above the photo. Used for Aoyama and Kamome Shirahama.
  - Cut people out with rembg `isnet-general-use` plus alpha matting, so caps and hair keep their edges.
  - If the photo crops the top of the hair, trim a clean rounded arc along the hair. Don't invent hair: a rebuilt crown looked bad.
- **`S_trialhook`:** the trial roll-call hook. Each cover slams in big at the centre on its name, and the previous one slides behind to the side, so the three build up into a fan. Then they ink into the cards. `shuchusen()` adds manga focus lines; it was used with mirrored, darker panels so the trial background differs from the main hook.
- **`tools/cover_v18.py`:** the Video 18 cover (card-focused layout, B/W manga-cover wall). The hero can be a person cut-out, with the held art swapped for a card through a perspective warp. Clean any leftover photo background from the mask, and check the body isn't chopped.
- **`examples/video18/reel_trial.json`:** the trial config. The first two main scenes are replaced by one 6.0s hook, and the VO is the new hook plus the main VO from 7.04s.

## `living.py` (new)

- **Layers:**
  - the character layer, traced along its black outline (whole character, no straight cuts)
  - an inpainted plate (`grow`, `sharp=True` for tight clean fills)
  - locked text and frame on top
- **Camera-only motion.** The rigs, bounces, trails and ghost hands are off because they looked funny. `use_rig` must be set explicitly to use a rig. `sharp=True` on a shot turns the focus band off.
- **`reveal=(t0, t1, n)`:** the background art lights up wedge by wedge around the figure. It was used for "the hands kept multiplying" on Crasher Wake's Passion.
- **Run:** `python3 living.py NAME OUTDIR [--stills | t1 t2 …]`.

## Workflow notes learned on Video 18

- The workspace has only 2 CPUs. Render prerender frames in two halves (`miss[part::2]`), and run each pass in the foreground under 10 minutes. Background jobs get killed when the reply ends.
- Article highlights: segment the glyph columns of each text line, map the highlighted words to what the VO says at that moment (`silencedetect -32dB d=.08` gives phrase gaps), and highlight in VO order.
- The top text badge must never overlap the main object, and name titles stay clear of the caption.
- Canva AI video refuses Pokémon characters (`moderation_rejected`) but makes b-roll without characters. Its download host is blocked in the workspace, so the user has to download the clip.
- Every preview and render goes on the editor page artifact.
