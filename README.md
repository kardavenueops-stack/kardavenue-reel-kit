# Kard Avenue Reel Kit

Everything needed to make Kard Avenue card-story Instagram Reels with Claude: engines, fonts, brand files and instructions for both styles.

| Skill | Style | Folder |
|---|---|---|
| `kard-avenue-reel` | Graphic and punchy: starburst hook, stamps, grids, PSA chart, Telegraf captions | `skills/kard-avenue-reel/` |
| `kard-finecard-reel` | Cinematic "Fine Card": full-bleed slow camera moves, blur dissolves, one-line captions | `skills/kard-finecard-reel/` |

Both end on the Kard Avenue FOLLOW US! call-to-action poster and follow the same script rules (Bahasa "kamu" VO, English captions, 45–60s, 9:16).

## Using it in a new chat

Say: *"Use the kard-avenue-reel skill (or kard-finecard-reel). The files are in github.com/kardavenueops-stack/kardavenue-reel-kit."*
Claude clones the repo and uses `skills/<skill>/` as the skill folder. Then send the card, facts and one zip of images.

Requirements: Python 3, Pillow, numpy, ffmpeg.
