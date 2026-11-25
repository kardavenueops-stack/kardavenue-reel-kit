import json
T=json.load(open('scenetimes.json')); B=T['B']; NS=T['NS']; C=T['cues']
R=lambda x:round(x,2)
def L(k):
    j=max(x for x in range(len(B)-1) if B[x]<=C[k]); return R(C[k]-B[j])
HS=['hs_ksante.png','hs_aphelios.png','hs_ezreal.png','hs_yone.png','hs_kayn.png','hs_sett.png']   # 178..183
RAIN=HS+['11_radiance_cards.png','12_radiance_cards.png','14_radiance_cards.png','16_radiance_cards.png','40_rain.png','44_rain.png']
VO=[("Kartu-kartu ini muncul di sebuah music video!","These cards showed up in a music video!"),
("Lima minggu sebelum dirilis.","Five weeks before release."),
("Music video dari Live My Life, lagu comeback HEARTSTEEL, boy band virtual dari League of Legends.","The video for Live My Life, the comeback of HEARTSTEEL, League of Legends' virtual boy band."),
("Anggotanya enam champion: Ezreal, Kayn, Aphelios, Yone, K'Sante, dan Sett.","Six champions: Ezreal, Kayn, Aphelios, Yone, K'Sante and Sett."),
("Mereka debut Oktober dua ribu dua puluh tiga lewat PARANOIA, dengan suara Ezreal diisi Baekhyun dari EXO!!","They debuted in October 2023 with PARANOIA, with EXO's Baekhyun as the voice of Ezreal!"),
("Bulan berikutnya, mereka tampil live di final Worlds, di Seoul!","The next month, they performed live at the Worlds final in Seoul!"),
("Tiga tahun kemudian, September lalu, mereka comeback:","Three years later, last September, they came back:"),
("Baekhyun kembali sebagai Ezreal, kali ini bareng Anderson .Paak sebagai K'Sante!","Baekhyun returns as Ezreal, now joined by Anderson .Paak as K'Sante!"),
("Dan di tengah music video-nya, muncul kartu Riftbound dengan wajah mereka.","And mid-video, Riftbound cards with their faces appeared."),
("Oktober lalu, kartunya resmi rilis di Radiance:","Last October, they officially landed in Radiance:"),
("enam Overnumber HEARTSTEEL, pertama kalinya di Riftbound!!!!","six HEARTSTEEL Overnumbers, a Riftbound first!"),
("Kata Riot, para member datang dengan makeover fashion modern.","Riot calls it a modern fashion makeover."),
("Coba lihat teks kecil di bawahnya: itu potongan lirik PARANOIA!!!","Check the small text at the bottom: it's lines from PARANOIA!"),
("Nomornya seratus tujuh puluh delapan sampai seratus delapan puluh tiga, dari seratus enam puluh tujuh kartu.","They're numbered 178 to 183, out of 167."),
("Dan setiap kartu punya versi Signature, dengan tanda tangan artisnya!!","And each one has a Signature version, signed by the member!"),
("Radiance segera hadir di Kard Avenue.","Radiance is coming soon to Kard Avenue."),
("Member HEARTSTEEL favoritmu siapa? Tulis di komentar!","Who's your favorite HEARTSTEEL member? Comment below!"),
("Follow Kard Avenue untuk cerita kartu lainnya, dan download aplikasinya sekarang.","Follow Kard Avenue for more card stories, and download the app now.")]
TG=[dict(x=0.255,y=0.329,cx=0.255,cy=0.357,label='EZREAL',k='ezreal'),
    dict(x=0.125,y=0.477,cx=0.125,cy=0.506,label='KAYN',k='kayn'),
    dict(x=0.506,y=0.313,cx=0.506,cy=0.342,label='APHELIOS',k='aphelios'),
    dict(x=0.652,y=0.393,cx=0.652,cy=0.422,label='YONE',k='yone'),
    dict(x=0.843,y=0.458,cx=0.843,cy=0.487,label="K'SANTE",k='ksante'),
    dict(x=0.41,y=0.488,cx=0.41,cy=0.516,label='SETT',k='sett')]
for t in TG:
    kk=t.pop('k'); t['at']=L(kk); t['mask']=f'hsmask_{kk}.png'; t['rim']=f'hsrim_{kk}.png'
qa=L('video')
S=[
 dict(beat='Hook',type='player_freeze',img='15_hs_ezreal_lml.png',cards=['hs_ksante.png','hs_ezreal_up.png','hs_sett.png'],zoom_card=1,freeze_at=R(qa+.15),zoom_at=R(qa+.85),card_h=400,title='▶  MUSIC VIDEO',y=700,pw=860,ph=1080,card_y=.6),
 dict(beat='Hook',type='macro3d',img='hs_ezreal_up.png',dof=8,focus=dict(axis='y',at=.35,width=.5),trans='glitch',xfade_in=.3,punch=.5,sfx=[[0,'bit8',.35]],
      **{'from':dict(fx=.5,fy=.36,h=1900,rot=0,tx=0,ty=0),'to':dict(fx=.52,fy=.32,h=2150,rot=2,tx=.06,ty=.02)},
      badges=[dict(text='SEPT 18 → OCT 23',at=.25),dict(text='5 WEEKS BEFORE RELEASE',at=.7,hl=True)]),
 dict(beat='Band',type='spotlight',img='16_hs_group_art_pad.png',targets=[],h0=2342,fy0=.59,overlay=dict(img='hs_logo_white.png',at=1.0,w=900,y=760),
      badges=[dict(text='LIVE MY LIFE · SEPT 2026',at=.3,hl=True),dict(text='LEAGUE OF LEGENDS · VIRTUAL BOY BAND',at=3.0)],trans='whip',xfade_in=.3),
 dict(beat='Band',type='spotlight',img='16_hs_group_art_pad.png',targets=TG,h0=2428,fy0=.59,h1=3780,dim=.8,rim=.9,label_y=1330,overlay=dict(img='hs_logo_white.png',at=-1,out=R(TG[0]['at']-.45),w=900,y=760),xfade_in=0,punch=0),
 dict(beat='Debut',type='macro3d',img='14_hs_ezreal_splash.png',card=False,cover=False,dof=0,
      **{'from':dict(fx=.62,fy=.42,h=2300,rot=-2,tx=-.1,ty=.04),'to':dict(fx=.66,fy=.38,h=2600,rot=1,tx=.08,ty=0)},
      badges=[dict(text='PARANOIA · OCT 2023',at=L('paranoia'),hl=True),dict(text='EZREAL · BAEKHYUN (EXO)',at=L('baekhyun'),hl=True)],trans='leak',xfade_in=.45),
 dict(beat='Worlds',type='slam',words=['LIVE AT','WORLDS'],at=R(L('worlds')-.1),shake=1,shake_at=R(L('worlds')+.15),
      rain=dict(cards=RAIN,n=26,h=420,alpha=1,front=3,seed=17,slow=.3,slow_len=.7),
      badges=[dict(text='SEOUL · NOV 2023',at=L('seoul'),hl=True)],trans='glitch',xfade_in=.25,sfx=[[0,'bit8',.3]]),
 dict(beat='Comeback',type='macro3d',img='15_hs_ezreal_lml.png',card=False,cover=False,dof=0,
      **{'from':dict(fx=.45,fy=.4,h=2200,rot=-2,tx=-.12,ty=.05),'to':dict(fx=.5,fy=.38,h=2400,rot=1,tx=.1,ty=0)},
      badges=[dict(text='3 YEARS LATER',at=.25),dict(text='SEPT 2026 · COMEBACK',at=L('sept'),hl=True)],trans='leak',xfade_in=.45),
 dict(beat='Comeback',type='versus',cards=['hs_ezreal_up.png','hs_ksante_up.png'],labels=['BAEKHYUN','ANDERSON .PAAK'],joiner='+',h=680,y=820,gap=40,in_dur=.45,joiner_at=L('anderson'),label_at=.4,trans='whip',xfade_in=.3),
 dict(beat='Teaser',type='player_freeze',img='15_hs_ezreal_lml.png',cards=['hs_kayn.png','hs_aphelios.png','hs_yone.png','hs_sett.png'],card_h=360,spread=.62,pop=[R(L('kartu8')+i*.35) for i in range(4)],p0=.45,p1=.7,title='HEARTSTEEL — LIVE MY LIFE',y=700,pw=860,ph=1080,card_y=.6,trans='glitch',xfade_in=.25,sfx=[[0,'bit8',.3]]),
 dict(beat='Radiance',type='macro3d',img='20_radiance_display.png',card=False,cover=False,dof=0,
      **{'from':dict(fx=.5,fy=.5,h=820,rot=-3,tx=-.24,ty=.05),'to':dict(fx=.5,fy=.5,h=900,rot=1,tx=.2,ty=.02)},
      badges=[dict(text='RADIANCE · OCT 23, 2026',at=L('radiance'),hl=True)],trans='zoom',xfade_in=.25),
 dict(beat='Overnumbers',type='deal',cards=HS,start=-.05,step=.22,h=760,y=760,counter=dict(label='HEARTSTEEL OVERNUMBERS',y=1210),
      badges=[dict(text='A RIFTBOUND FIRST',at=L('pertama'),hl=True)],xfade_in=.2,punch=.5),
 dict(beat='Makeover',type='flip',pairs=[dict(**{'from':'12_orig_sett.png'},to='hs_sett.png',at=.75),dict(**{'from':'09_orig_ezreal.png'},to='hs_ezreal.png',at=1.25),dict(**{'from':'10_orig_yone.png'},to='hs_yone.png',at=1.75)],h=600,gap=360,y=900,
      badges=[dict(text='“A MODERN FASHION MAKEOVER” — RIOT',at=L('makeover'),hl=True)],trans='whip',xfade_in=.3),
 dict(beat='Lyrics',type='macro3d',img='hs_ksante_up.png',dof=0,
      **{'from':dict(fx=.45,fy=.62,h=2100,rot=0,tx=0,ty=0),'to':dict(fx=.389,fy=.74,h=2500,rot=0,tx=0,ty=0)},
      highlight=[dict(box=[.10,.837,.68,.870],t0=L('lirik'),dur=.5,style='band'),dict(box=[.10,.871,.655,.899],t0=R(L('lirik')+.55),dur=.5,style='band')],follow=False,hl_bold=False,dim=.12,spot=dict(w=1150,h=520,dark=.55,y=1290),
      badges=[dict(text='PARANOIA LYRICS',at=R(L('lirik')+.3),hl=True)],trans='leak',xfade_in=.4),
 dict(beat='Numbers',type='card_grid',cards=HS,card_h=480,col_gap=350,row_gap=1.08,y=760,labels=[str(178+i) for i in range(6)],label_at=[R(.55+i*.42) for i in range(6)],label_size=44,
      badges=[dict(text='178–183 / 167',at=L('dari'),hl=True)],trans='zoom',xfade_in=.25),
 dict(beat='Signature',type='macro3d',img='02_sig_aphelios_179_up.png',dof=9,focus=dict(axis='y',at=.42,width=.4),
      **{'from':dict(fx=.5,fy=.45,h=2100,rot=-2,tx=-.08,ty=.04),'to':dict(fx=.66,fy=.42,h=3000,rot=1,tx=.04,ty=0)},
      badges=[dict(text='SIGNATURE · 179*/167',at=L('sig'),hl=True),dict(text='SIGNED BY APHELIOS',at=L('ttd'),hl=True)],trans='whip',xfade_in=.3),
 dict(beat='Payoff',type='versus',cards=['20_radiance_display.png','20b_radiance_pack.png'],labels=['',''],joiner='',card=False,h=560,gap=60,
      badges=[dict(text='COMING SOON · KARD AVENUE',at=.35,hl=True)],trans='leak',xfade_in=.4),
 dict(beat='Payoff',type='card_lineup',cards=[dict(img=f) for f in HS],card_h=430,fan=6,spread=172,y=770,heading="WHO'S YOUR BIAS?",trans='glitch',xfade_in=.25,sfx=[[0,'bit8',.3]]),
 dict(beat='End card',type='end_card',img='23_follow_us_cta.jpg',punch=.4),
]
V=["Kard-drawn video player plays the Live My Life art with three HEARTSTEEL cards; it freezes, brackets snap onto Ezreal and the camera dives in",
"HEARTSTEEL Ezreal close-up; 'Sept 18 → Oct 23' / '5 weeks before release'",
"Group artwork, HEARTSTEEL logo rises in; Live My Life and 'virtual boy band' badges",
"Roll call: the camera glides across the group art and a close spotlight picks out each member as he is named",
"Original HEARTSTEEL Ezreal splash, PARANOIA · Oct 2023 and Baekhyun (EXO) badges",
"LIVE AT / WORLDS slam over falling HEARTSTEEL + Radiance cards; Seoul · Nov 2023",
"Live My Life Ezreal art fly-over; 3 years later / Sept 2026 comeback",
"Ezreal + K'Sante HEARTSTEEL cards face-off: Baekhyun + Anderson .Paak",
"The video player again: HEARTSTEEL cards pop into the frame one by one",
"Radiance display fly-over, Oct 23, 2026",
"Six HEARTSTEEL Overnumbers dealt onto a pile, counter 1–6; 'a Riftbound first'",
"Makeover flip: original Sett, Ezreal, Yone cards turn over in 3D into their HEARTSTEEL versions",
"Zoom into the K'Sante card's flavor text under a spotlight; yellow marker sweeps the two PARANOIA lines",
"Six HEARTSTEEL cards in a 3×2 grid, number chips 178–183 pop on each card in order; '178–183 / 167'",
"Macro onto the member's signature on the Aphelios Signature card (179*/167)",
"Radiance display + booster pack, COMING SOON badge",
"Fan of all six HEARTSTEEL cards, WHO'S YOUR BIAS?",
"FOLLOW US! end card"]
assert len(S)==len(VO)==len(NS)==len(V)
for i,s in enumerate(S):
    s['dur']=R(B[i+1]-B[i]); s['vo'],s['caption']=VO[i]; s['vo_window']=[R(NS[i][0]-B[i]),R(NS[i][1]-B[i])]; s['visual']=V[i]
    if 'Anderson' in s['caption']: s['chunk_list']=['Baekhyun returns','as Ezreal,','now joined by','Anderson .Paak','as K\'Sante!']
    S[i]={k:s[k] for k in ['beat','dur','vo','caption','vo_window','visual']}|{k:v for k,v in s.items() if k not in('beat','dur','vo','caption','vo_window','visual')}

# v3.8: scenes 3+4 are one continuous shot over the same artwork (no cut between two copies of the picture)
a3,a4=S[2],S[3]; d3=a3['dur']
for t in a4['targets']: t['at']=R(t['at']+d3)
a3['badges'][-1]['until']=R(a4['targets'][0]['at']+d3-.6) if False else None
ov=dict(a3['overlay']); ov['out']=R(a4['targets'][0]['at']-.55); ov['dur']=.75
m=dict(a3); m.update(dur=R(d3+a4['dur']),vo=a3['vo']+' '+a4['vo'],caption=a3['caption']+' '+a4['caption'],
  vo_window=[a3['vo_window'][0],R(a4['vo_window'][1]+d3)],visual='Group artwork; the HEARTSTEEL logo holds still, then the camera drives through it into the roll call: each member is traced and lit as he is named while the rest of the picture drops into shadow',
  caption_groups=[[a3['caption'],a3['vo_window'][0],a3['vo_window'][1]],[a4['caption'],R(a4['vo_window'][0]+d3),R(a4['vo_window'][1]+d3)]],
  targets=a4['targets'],h0=a4['h0'],fy0=a4['fy0'],h1=a4['h1'],dim=a4['dim'],rim=a4['rim'],label_y=a4['label_y'],overlay=ov)
m['badges']=[dict(b) for b in a3['badges']]; m['badges'][-1]['until']=R(ov['out'])
S[2:4]=[m]
cfg=json.load(open('/home/claude/v16/reel.json')); cfg={k:v for k,v in cfg.items() if k!='scenes'}
cfg.update(title='Video 17 — HEARTSTEEL x Riftbound',cover={'img':'hs_ezreal.png','title':'HEARTSTEEL'},open_decisions=['Approve storyboard'],
 post_caption="Kartu-kartu ini muncul di music video, lima minggu sebelum dirilis 🎤🃏\n\nRiftbound: League of Legends TCG — Radiance · HEARTSTEEL Overnumbers\n\nRadiance segera hadir di @kardavenue · Download Kard Avenue di Google Play & App Store\n\n#kardavenue #reels #riftbound #riftboundtcg #heartsteel #tcgindonesia",
 scenes=S)
json.dump(cfg,open('reel.json','w'),indent=1,ensure_ascii=False)
print('ok',len(S),round(sum(s['dur'] for s in S),2))
