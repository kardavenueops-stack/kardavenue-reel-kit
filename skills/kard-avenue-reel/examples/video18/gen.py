"""gen.py - builds reel.json for Video 18 (mangaka who drew Pokémon cards) from the retimed VO segments."""
import json

T = json.load(open('/home/claude/v18/vo/timing75.json'))
PAD = .03
SEG = [(a + PAD, b - PAD) for a, b in T['segs']]          # true speech start/end on the 75s timeline
END = 75.53


def cut(k):   # scene boundary before segment k = middle of the pause
    return 0.0 if k == 0 else round((SEG[k - 1][1] + SEG[k][0]) / 2, 3)


# (start segment or absolute time, scene dict). Absolute times are used for mid-sentence splits.
P = []
def sc(start, **s): P.append((start, s))


sc(0, beat='Hook', type='prerender', frames='../w_hook1', keys=[(.5, 'manga space, b/w covers'), (1.35, 'ink burst -> Pichu'), (3.4, 'both cards in 3D')], vo='Ilustrator Detective Conan dan Chiikawa pernah menggambar kartu Pokémon!',
   caption='The illustrators of Detective Conan and Chiikawa have drawn Pokémon cards!',
   visual='Manga cover -> card ink wash: Conan cover becomes Spiky-eared Pichu, Chiikawa cover becomes Simisear VSTAR',
   sfx=[[0, 'swoosh', .3], [1.0, 'tap', .35], [2.05, 'tap', .35]])
sc(1, beat='Hook', type='prerender', frames='../w_hook2', keys=[(.3, 'ink slam impact'), (1.15, 'Hokuto cover'), (2.0, 'Palafin'), (3.0, 'Palafin + Crasher, x2')], vo='Dan ilustrator Hokuto no Ken, baru saja bikin kartu keduanya!!',
   caption='And the Fist of the North Star illustrator just made his second!',
   visual='Hokuto no Ken cover washes into Palafin ex; Crasher Wake\'s Passion slides in beside it, x2',
   trans='glitch', xfade_in=.3, sfx=[[0, 'bit8', .3], [1.45, 'reveal', .25], [2.15, 'swoosh', .35]],
   badges=[{'text': '× 2', 'at': 2.45, 'hl': True}])
sc(2, beat='Aoyama', type='prerender', frames='../w_aoyama', keys=[(1.0, 'noir desk: Conan cover'), (3.8, 'name title')], vo='Nah, mulai dari Gosho Aoyama. Tahun dua ribu sembilan, dia gambar Pokémon untuk pertama kalinya.',
   caption='First up: Gosho Aoyama. In 2009, he drew a Pokémon for the first time ever.',
   visual='Conan cover as paper cut-out, name title; 2009 / FIRST POKÉMON EVER chips', trans='ink', xfade_in=0.5,
   badges=[{'text': '2009', 'at': 1.75}, {'text': 'HIS FIRST POKÉMON EVER', 'at': 2.9, 'hl': True}], sfx=[[0, 'drop', .3]])
sc(4, beat='Pichu', type='prerender', frames='../w_pichu', keys=[(.4, 'card rises off desk'), (1.7, 'product shot')], img='c_pichu.png', vo='Hasilnya? Spiky-eared Pichu,', caption='The result? Spiky-eared Pichu,',
   visual='Reversed fly-over: Pichu card starts close, pulls back and tips away', trans='focus', xfade_in=0.45,
   badges=[{'text': 'SPIKY-EARED PICHU · 042/DPt-P', 'at': .5}])
sc('S4b', beat='Sunday', type='macro3d', img='p_sunday_insert.png', card=False, dof=0, focus={'axis': 'y', 'at': .5, 'width': .6},
   from_={'fx': .42, 'fy': .52, 'h': 1950, 'rot': -2, 'tx': -.08, 'ty': .05}, to={'fx': .48, 'fy': .64, 'h': 2150, 'rot': 1, 'tx': .06, 'ty': .02},
   highlight=[{'box': [.094, .450, .878, .590], 't0': .25, 'dur': .9, 'style': 'lift', 'mask': 'hl_sunday_1.png'}, {'box': [.139, .842, .833, .908], 't0': 1.45, 'dur': .9, 'style': 'lift', 'mask': 'hl_sunday_2.png'}],
   follow=True, noir=True, spot={'w': 1050, 'h': 400, 'dark': .80}, hl_bold=False, hl_boost=1.35, hl_glow=1.0,
   vo='yang diselipkan di majalah Shonen Sunday, rumahnya Detective Conan.', caption='tucked into Shonen Sunday, Conan\'s home magazine.',
   visual='Real 2009 Sunday insert, noir + marker on 青山剛昌 and スペシャルカード', trans='page', xfade_in=0.45,
   badges=[{'text': 'SHŌNEN SUNDAY #33 · JULY 2009', 'at': .2}])
sc(6, beat='Price', type='macro3d', img='p_sunday_cover.png', card=False, dof=8, focus={'axis': 'y', 'at': .3, 'at1': .5, 'width': .45},
   from_={'fx': .45, 'fy': .25, 'h': 2600, 'rot': 2, 'tx': .1, 'ty': .05}, to={'fx': .52, 'fy': .45, 'h': 2300, 'rot': -1, 'tx': -.08, 'ty': .03},
   vo='Harga majalahnya cuma dua ratus enam puluh yen.', caption='The magazine cost just ¥260.',
   visual='Shonen Sunday #33 cover macro slide; ¥260 chip', trans='glitch', xfade_in=.3, sfx=[[0, 'bit8', .25]],
   badges=[{'text': '¥260', 'at': .9, 'hl': True}])
sc(7, beat='Price', type='macro3d', img='a_yahoo.png', card=False, dof=0, focus={'axis': 'y', 'at': .45, 'width': .6},
   from_={'fx': .40, 'fy': .28, 'h': 2700, 'rot': 0, 'tx': 0, 'ty': 0}, to={'fx': .40, 'fy': .63, 'h': 2900, 'rot': -1, 'tx': -.04, 'ty': .03},
   highlight=[{'box': [.348, .267, .402, .291], 't0': .5, 'dur': .7}, {'box': [.348, .620, .410, .643], 't0': 1.7, 'dur': .7}],
   follow=True, noir=True, spot={'w': 1050, 'h': 340, 'dark': .80}, hl_bold=False, hl_boost=1.35, hl_glow=1.0,
   vo='Sekarang, kartunya bisa laku lebih dari dua ratus kali lipat!', caption='Now the card can sell for over 200 times that!',
   visual='Yahoo! Auctions sold listings, noir + marker on ¥55,000 then ¥110,000', trans='whip', xfade_in=.3,
   badges=[{'text': 'YAHOO! AUCTIONS · SOLD · OCT 2026', 'at': .15}, {'text': '200×+', 'at': 2.35, 'hl': True}],
   sfx=[[2.35, 'coin', .35]])
sc(8, beat='nagano', type='prerender', frames='../w_nagano', keys=[(1.2, 'fun world: bear cut-out')], vo='Terus ada nagano. Pas kartu ini keluar,', caption='Then there\'s nagano. When this card dropped,',
   visual='nagano\'s bear self-character as paper cut-out, name title', trans='zoom', xfade_in=.3)
sc('S6b', beat='nagano', type='macro3d', img='a_insidegames.png', card=False, dof=0, focus={'axis': 'y', 'at': .43, 'width': .6},
   from_={'fx': .45, 'fy': .42, 'h': 2900, 'rot': 0, 'tx': 0, 'ty': 0}, to={'fx': .30, 'fy': .44, 'h': 3100, 'rot': -1, 'tx': -.04, 'ty': .02},
   highlight=[{'box': [.522, .406, .608, .431], 't0': .25, 'dur': .5}, {'box': [.132, .437, .300, .463], 't0': .8, 'dur': 1.0}],
   follow=True, noir=True, spot={'w': 1050, 'h': 340, 'dark': .80}, hl_bold=False, hl_boost=1.35, hl_glow=1.0,
   vo='fans langsung curiga, kok mirip Chiikawa?', caption='fans wondered: why does it look like Chiikawa?',
   visual='inside-games article, noir + marker on the fan quote 「ちいかわみたい…」', trans='focus', xfade_in=0.45,
   badges=[{'text': 'SOURCE: INSIDE GAMES, NOV 2022', 'at': .2}])
sc(12, beat='nagano', type='prerender', frames='../w_versus', keys=[(.5, 'split screen opens'), (1.9, 'both close-ups panning')], vo='Ternyata benar, pencipta Chiikawa sendiri yang gambar!',
   caption='Turns out the Chiikawa creator drew it herself!', visual='Split screen: Chiikawa (left) | Simisear VSTAR (right), each a close-up 3D pan side to side', trans='whip', xfade_in=.3)
sc(14, beat='Simisear', type='prerender', frames='../lvw_simisear', vo='Lihat Simisear VSTAR-nya, lagi asyik makan Sitrus Berry sambil pose "yay". Dan ini satu-satunya kartu dia.',
   caption='Simisear VSTAR munching a Sitrus Berry, mid-"yay". Her only card.',
   visual='Living card: Simisear layers, macro onto the berry, hop on "yay", pull back', trans='zoom', xfade_in=.3,
   badges=[{'text': 'SIMISEAR VSTAR · SAR · 2022', 'at': .3}, {'text': 'HER ONLY POKÉMON CARD', 'at': 4.3, 'hl': True}],
   keys=[(1.0, 'macro'), (3.65, 'yay hop'), (5.8, 'full card in fun world')])
sc(16, beat='Hara', type='prerender', frames='../w_hara', keys=[(2.5, 'ink-action world: Kenshiro cut-out')], vo='Sekarang, Tetsuo Hara. Komiknya, Hokuto no Ken, laku lebih dari seratus juta kopi!',
   caption='Now, Tetsuo Hara. His Fist of the North Star sold over 100 million copies!',
   visual='Hara\'s Kenshiro drawing as paper cut-out, name; 100,000,000+ COPIES chip', trans='ink', xfade_in=0.5, sfx=[[0, 'drop', .3], [0, 'bit8', .3]],
   badges=[{'text': '100,000,000+ COPIES', 'at': 2.1, 'hl': True}])
sc(18, beat='Palafin', type='prerender', frames='../lvw_palafin', vo='Desember dua ribu dua empat, dia gambar Palafin ex. Lihat tinjunya, ninggalin bayangan kayak jurusnya Kenshiro!!',
   caption='Dec 2024: Palafin ex. Look at the fists, leaving afterimages like Kenshiro!',
   visual='Living card: Palafin layers, macro fist -> face, fists push with afterimage trails, pull back', trans='zoom', xfade_in=0.3,
   badges=[{'text': 'PALAFIN ex · SAR · DEC 2024', 'at': .3}], keys=[(.8, 'macro fist'), (3.2, 'afterimages'), (5.2, 'full card')])
sc(22, beat='Quote', type='macro3d', img='a_hara_interview.png', card=False, dof=0, focus={'axis': 'y', 'at': .88, 'width': .4},
   from_={'fx': .50, 'fy': .87, 'h': 2900, 'rot': 0, 'tx': 0, 'ty': 0}, to={'fx': .34, 'fy': .89, 'h': 3100, 'rot': -1, 'tx': -.04, 'ty': .02},
   highlight=[{'box': [.4341, .8975, .5208, .9217], 't0': .9, 'dur': .8}, {'box': [.4860, .8698, .6559, .8940], 't0': 2.0, 'dur': 1.1}, {'box': [.6559, .8698, .7657, .8940], 't0': 3.37, 'dur': .8}],
   follow=True, noir=True, spot={'w': 1050, 'h': 340, 'dark': .80}, hl_bold=False, hl_boost=1.35, hl_glow=1.0,
   vo='Kata Hara, bagian paling susahnya: tetap terasa Pokémon, tapi tetap keren ala dia.',
   caption='The hardest part, he said: keep it Pokémon, but make it his kind of cool.',
   visual='Official interview, noir + marker on the Pokémon-ness / his cool line', trans='focus', xfade_in=0.45,
   badges=[{'text': 'SOURCE: POKÉMON CARD GAME OFFICIAL, NOV 2026', 'at': .2}])
sc(23, beat='New card', type='prerender', frames='../w_flip', keys=[(1.5, 'arena: mystery card in spotlight'), (4.2, 'flipped: Crasher Wake')],
   vo='Nah, tanggal dua tujuh November, kartu keduanya rilis di Jepang. Namanya Crasher Wake\'s Passion, dari set Aura Seeker!',
   caption='Nov 27: his second card, Crasher Wake\'s Passion, lands in Japan in Aura Seeker!',
   visual='Blacked-out mystery card, 27 NOV date chip, 3D flip to Crasher Wake\'s Passion on its name', trans='iris', xfade_in=0.55,
   badges=[{'text': '27 NOV 2026 · JAPAN', 'at': .45}, {'text': 'AURA SEEKER · M7 · SAR', 'at': 3.3, 'hl': True}],
   sfx=[[0, 'metal_whoosh', .25], [0, 'bit8', .3], [2.9, 'reveal', .35]],
   caption_groups=[['Nov 27: his second card', .2, 1.42], ['lands in Japan.', 1.42, 2.78], ['Crasher Wake\'s Passion, from Aura Seeker!', 2.8, 5.45]])
sc(28, beat='Hands', type='macro3d', img='a_hara_interview.png', card=False, dof=0, focus={'axis': 'y', 'at': .2, 'width': .4},
   from_={'fx': .50, 'fy': .17, 'h': 2700, 'rot': 0, 'tx': 0, 'ty': 0}, to={'fx': .50, 'fy': .22, 'h': 2900, 'rot': 1, 'tx': .04, 'ty': .02},
   highlight=[{'box': [.2354, .1509, .3512, .1878], 't0': .8, 'dur': .6}, {'box': [.3626, .1509, .7668, .1878], 't0': 1.5, 'dur': 1.1}],
   follow=True, noir=True, spot={'w': 1050, 'h': 340, 'dark': .80}, hl_bold=False, hl_boost=1.35, hl_glow=1.0,
   vo='Lucunya, tangan sebanyak itu awalnya enggak direncanakan.', caption='Funny thing: he never planned that many hands.',
   visual='Interview headline 「手の残像は、最初から描くつもりだった…」 noir + marker', trans='page', xfade_in=0.45,
   sfx=[])
sc(29, beat='Hands', type='prerender', frames='../lvw_crasher', vo='Makin digambar, makin nambah terus!!', caption='They kept multiplying as he drew!',
   visual='Living card: Crasher Wake, ghost-hand afterimages fan out one by one', trans='zoom', xfade_in=.3,
   sfx=[[.2, 'swoosh', .2], [.8, 'swoosh', .2], [1.4, 'swoosh', .22]], keys=[(.4, 'first hands'), (1.9, 'many hands')])
sc(30, beat='Shirahama', type='prerender', frames='../w_shirahama', keys=[(1.2, 'gallery wall'), (2.8, 'name title')], vo='Eh, satu lagi! Kamome Shirahama, pencipta Witch Hat Atelier.',
   caption='Oh, one more! Kamome Shirahama, creator of Witch Hat Atelier.', visual='Gallery wall: Witch Hat Atelier cover framed under a gallery light, her portrait card beside it, name title',
   trans='glitch', xfade_in=.25, sfx=[[0, 'bit8', .35]])
sc(33, beat='Shirahama', type='prerender', frames='../w_glaceon', keys=[(.9, 'Glaceon spotlight + snow'), (2.75, 'Marvel + Star Wars logos')], img='c_glaceon.png',
   vo='Dia pemenang Eisner Award, dan pernah gambar cover Marvel sampai Star Wars!!!!!',
   caption='Eisner Award winner, with covers for Marvel and Star Wars!',
   visual='Glaceon ex product shot in a single spotlight, slow orbit, falling snow; Marvel + Star Wars logos pop on their names', trans='leak', xfade_in=.45,
   badges=[{'text': 'GLACEON ex · SAR', 'at': .1}, {'text': 'EISNER AWARD 2020', 'at': .9, 'hl': True, 'until': 2.0}])
sc(35, beat='Payoff', type='prerender', frames='../w_payoff', keys=[(4.0, 'studio: cards landing on their names'), (5.85, 'all four, light sweep')], cards=[{'img': 'c_pichu.png', 'at': 0}, {'img': 'c_simisear.png', 'at': 0},
   {'img': 'c_palafin.png', 'at': 0}, {'img': 'c_glaceon.png', 'at': 0}], enter_y=-600,
   vo='Jadi, mau punya kartu dari mangaka favoritmu? Pichu, Simisear, Palafin, sampai Glaceon, ada di Kard Avenue!',
   caption='Want your favorite mangaka\'s card? Pichu, Simisear, Palafin and Glaceon: at Kard Avenue!',
   visual='Four in-stock cards land one by one on their names over a blurred Eeveelution SAR; READY AT KARD AVENUE', trans='whip', xfade_in=.3,
   badges=[{'text': 'READY AT KARD AVENUE', 'at': 0, 'hl': True, 'y': 1180, 'size': 40}])
sc(39, beat='End card', type='end_card', img='23_follow_us_cta.jpg', punch=.4, vo='Follow Kard Avenue, dan download aplikasinya Sekarang!!',
   caption='Follow Kard Avenue and download the app now!', visual='FOLLOW US! poster', trans='leak', xfade_in=.45)

# resolve starts
starts = []
for st, s in P:
    if st == 'S4b': starts.append(round(SEG[4][0] + 1.75, 3))
    elif st == 'S6b': starts.append(round(SEG[9][0] + .95, 3))
    else: starts.append(cut(st))
scenes = []
for i, ((st, s), t0) in enumerate(zip(P, starts)):
    t1 = starts[i + 1] if i + 1 < len(P) else END
    s = dict(s); s['dur'] = round(t1 - t0, 3)
    if 'from_' in s: s['from'] = s.pop('from_')
    # speech window inside the scene
    sp = [(a, b) for a, b in SEG if b > t0 + .01 and a < t1 - .01]
    s['vo_window'] = [round(max(sp[0][0], t0) - t0, 2), round(min(sp[-1][1], t1) - t0, 2)] if sp else [.1, s['dur'] - .1]
    s['_t0'] = t0
    scenes.append(s)

# per-card landing times in the payoff (on each spoken name) and the stamp on "Kard Avenue"
pay = scenes[-2]; t0 = pay['_t0']
names = [SEG[37][0], SEG[37][0] + .55, SEG[38][0], SEG[38][0] + .95]
for c, tt in zip(pay['cards'], names): c['at'] = round(tt - t0, 2)
pay['badges'][0]['at'] = round(SEG[38][1] - .55 - t0, 2)
pay['sfx'] = [[c['at'], 'tap', .4] for c in pay['cards']] + [[pay['badges'][0]['at'], 'coin', .35]]
pay['caption_groups'] = [['Want your favorite mangaka\'s card?', 0.05, round(SEG[36][1] - t0 + .15, 2)], ['Pichu, Simisear, Palafin and Glaceon: at Kard Avenue!', round(SEG[37][0] - t0 - .05, 2), round(pay['dur'] - .05, 2)]]
gl = [s for s in scenes if s['beat'] == 'Shirahama'][1]
gl['cues'] = {'marvel': round(SEG[34][0] + 1.05 - gl['_t0'], 2), 'starwars': round(SEG[34][0] + 1.75 - gl['_t0'], 2)}
for s in scenes: s.pop('_t0')

cfg = {
    'title': 'Video 18 — Mangaka who drew Pokémon cards', 'assets_dir': 'assets', 'sfx_dir': 'sfx', 'logo': '07_kard_logo.png',
    'caption_mode': 'chunks', 'chunk_words': 4, 'highlight_words': [], 'forbidden_words': ['TGA'], 'sfx_gain': .55, 'sfx_style': 'soft',
    'xfade': .35, 'stock_confirmed': True, 'ig_handle': '@kardavenue', 'cover': {'img': 'c_palafin.png', 'title': 'MANGAKA x POKÉMON'},
    'bokeh': [[250, 250, 250], [150, 150, 150], [210, 210, 210]], 'highlight_sfx_once': True,
    'camera': {'punch': .03, 'punch_t': .5, 'breathe': .01, 'drift': 4, 'base': 1.02, 'grade': {'sat': 1.1, 'contrast': 1.08}},
    'badge_sfx': 'shutter', 'cut_sfx': 'swoosh', 'caption_style': 'plain', 'caption_size': 50, 'caption_shadow': 'strong',
    'bg_color': [[26, 26, 26], [10, 10, 10]], 'mono_ui': True, 'slam_tint': [20, 20, 20], 'slam_color': [250, 250, 250], 'leak_color': [250, 250, 250],
    'voiceover': 'vo_75.wav', 'voiceover_offset': 0, 'max_len': 76,
    'post_caption': 'Mangaka favoritmu ternyata pernah menggambar kartu Pokémon 🖌️🃏\n\nGosho Aoyama (Detective Conan) · nagano (Chiikawa) · Tetsuo Hara (Hokuto no Ken) · Kamome Shirahama (Witch Hat Atelier)\n\nSpiky-eared Pichu, Simisear VSTAR SAR, Palafin ex SAR & Glaceon ex SAR ready di @kardavenue · Download Kard Avenue di Google Play & App Store\n\n#kardavenue #reels #pokemon #pokemontcg #pokemonindonesia',
    'scenes': scenes,
}
json.dump(cfg, open('reel.json', 'w'), ensure_ascii=False, indent=1)
for i, s in enumerate(scenes): print(i + 1, s['type'], s['dur'], s['beat'])
print('total', round(sum(s['dur'] for s in scenes), 2))
