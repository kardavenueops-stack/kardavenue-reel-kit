"""prep.py - copy assets with clean names, cut cards to their rounded shape (transparent corners), 2x upscale cards."""
import os, shutil, numpy as np
from PIL import Image, ImageDraw
R='/home/claude/v18/raw/video18_mangaka'; O='assets'
KIT='/home/claude/kardavenueops-stack/kardavenue-reel-kit/skills/kard-avenue-reel/assets'
CARDS={'01_crasher_wakes_passion_sar.jpg':'c_crasher.png','02_spiky_eared_pichu_dpt-p042.png':'c_pichu.png','03_simisear_vstar_sar.jpg':'c_simisear.png',
 '04_palafin_ex_sar.jpg':'c_palafin.png','05_glaceon_ex_sar.jpg':'c_glaceon.png','11_ninetales_shirahama.png':'c_ninetales.png',
 '12_druddigon_shirahama.png':'c_druddigon.png','13_doublade_shirahama.jpg':'c_doublade.png'}
for i,f in enumerate(['14_eevee_ex_sar.jpg','15_vaporeon_ex_sar.jpg','16_jolteon_ex_sar.jpg','17_flareon_ex_sar.jpg','18_espeon_ex_sar.jpg','19_umbreon_ex_sar.jpg','19b_leafeon_ex_sar.jpg','19c_sylveon_ex_sar.jpg']):
    CARDS[f]=f'w_eevee_{i}.png'
def rounded(im):
    im=im.convert('RGBA'); w,h=im.size
    # trim existing transparent margin
    bb=im.split()[3].point(lambda a:255 if a>40 else 0).getbbox(); im=im.crop(bb); w,h=im.size
    m=Image.new('L',(w*4,h*4),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w*4-1,h*4-1],radius=int(0.047*w*4),fill=255)
    m=m.resize((w,h),Image.LANCZOS)
    a=np.minimum(np.asarray(im.split()[3]),np.asarray(m)); im.putalpha(Image.fromarray(a)); return im
for s,d in CARDS.items():
    im=rounded(Image.open(f'{R}/{s}'))
    im=im.resize((im.width*2,im.height*2),Image.LANCZOS)
    im.save(f'{O}/{d}')
OTHER={'06_sunday_2009_insert.jpg':'p_sunday_insert.png','06b_sunday_2009_card.jpg':'p_sunday_card.png','06c_sunday_2009_cover.jpg':'p_sunday_cover.png',
 '10_hara_interview.jpg':'a_hara_interview.png','10b_hara_interview_body.jpg':'a_hara_body.png','20_inside_games_nagano.jpg':'a_insidegames.png',
 '21_yahoo_pichu_sold.jpg':'a_yahoo.png','22_avatar_hara.jpg':'v_hara.png','22_avatar_nagano.jpg':'v_nagano.png','22_avatar_shirahama.jpg':'v_shirahama.png',
 '30b_cover_detective_conan_v1_large.jpg':'m_conan.png','31_cover_chiikawa_v1.jpg':'m_chiikawa.png','FotNS-UltimateEdition-Volume1COVER.webp':'m_hokuto.png',
 '32_cover_hokuto_no_ken_v1_shinsoban2023.jpg':'m_hokuto2.png','33_cover_witch_hat_atelier_v1.jpg':'m_witchhat.png'}
for s,d in OTHER.items():
    im=Image.open(f'{R}/{s}').convert('RGB')
    sc=max(1,int(np.ceil(1400/max(im.size))))   # small photos/covers up to ~1400px
    if sc>1: im=im.resize((im.width*sc,im.height*sc),Image.LANCZOS)
    im.save(f'{O}/{d}')
for f in ['07_kard_logo.png','23_follow_us_cta.jpg']: shutil.copy(f'{KIT}/{f}',O)
os.makedirs('sfx',exist_ok=True)
for f in os.listdir(f'{KIT}/sfx'): shutil.copy(f'{KIT}/sfx/{f}','sfx')
print(sorted(os.listdir(O)))
