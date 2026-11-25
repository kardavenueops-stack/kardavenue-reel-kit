import json
src=open('gen.py').read()
src=src.replace("open('scenetimes.json')","open('scenetimes_trial.json')").replace("open('reel.json','w')","open('reel_trial.json','w')")
src=src.replace("dict(text='SEPT 2026 · COMEBACK',at=L('sept'),hl=True)","dict(text='LIVE MY LIFE · SEPT 2026',at=L('sept'),hl=True)")
src=src.replace("assert len(S)==len(VO)==len(NS)==len(V)","""
VO[0:3]=[("Boy band ini punya enam member, tapi cuma empat yang nyanyi.","This boy band has six members, but only four sing."),
 ("Dua lagi? Penulis lagu dan produser.","The other two? A songwriter and a producer."),
 ("Dan sekarang, keenamnya jadi kartu!","And now, all six are cards!"),
 ("Namanya HEARTSTEEL, boy band virtual dari League of Legends.","They're HEARTSTEEL, League of Legends' virtual boy band.")]
V[0:3]=["The whole HEARTSTEEL group art, framed: all six members light up inside their outlines, then only the four singers stay lit",
 "Camera glides in to the two dark members; SONGWRITER chip under Aphelios, PRODUCER under Yone",
 "Glitch cut: all six HEARTSTEEL cards snap in as a fan",
 "Group artwork; the HEARTSTEEL logo rises in, 'League of Legends · virtual boy band'"]
ALL=['ezreal','kayn','aphelios','yone','ksante','sett']
T1=dict(beat='Hook',type='spot_groups',img='16_hs_group_art_pad.png',dim=.82,rim=.9,label_y=1330,
  cam=[[0,.5,.55,880]],
  groups=[dict(at=L('t_enam'),lit=ALL),dict(at=L('t_empat'),lit=['ezreal','kayn','ksante','sett'])],
  badges=[dict(text='6 MEMBERS',at=L('t_enam')),dict(text='ONLY 4 SING',at=L('t_empat'),hl=True)])
T2=dict(beat='Hook',type='spot_groups',img='16_hs_group_art_pad.png')
T3=dict(beat='Hook',type='card_lineup',cards=[dict(img=x) for x in HS],card_h=500,y=780,rows=2,row_gap=520,spread=332,fan=3,bg_img='16_hs_group_art_pad.png',t0=.12,step=.15,
  badges=[dict(text='RIFTBOUND · RADIANCE',at=L('t_kartu'),hl=True)],trans='glitch',xfade_in=.25,sfx=[[0,'bit8',.3]])
BR=dict(S[2]); BR['overlay']=dict(img='hs_logo_white.png',at=R(L('t_heartsteel')-.15),w=900,y=760)
BR['badges']=[dict(text='LEAGUE OF LEGENDS · VIRTUAL BOY BAND',at=L('t_boyband'))]
S[0:3]=[T1,T2,T3,BR]
assert len(S)==len(VO)==len(NS)==len(V)""")
src=src.replace("a3,a4=S[2],S[3]","a3,a4=S[3],S[4]").replace("S[2:4]=[m]","""S[3:5]=[m]
# hook lines 1+2: one continuous shot over the group art
h1,h2=S[0],S[1]; d1=h1['dur']
pa,pe=C['t_penulis'],C['t_produser']
h1.update(dur=R(d1+h2['dur']),vo=h1['vo']+' '+h2['vo'],caption=h1['caption']+' '+h2['caption'],vo_window=[h1['vo_window'][0],R(h2['vo_window'][1]+d1)],
  visual=h1['visual']+'; '+h2['visual'][0].lower()+h2['visual'][1:],
  caption_groups=[[h1['caption'],h1['vo_window'][0],h1['vo_window'][1]],[h2['caption'],R(h2['vo_window'][0]+d1),R(h2['vo_window'][1]+d1)]])
du=C['t_dua']
h1['cam']+= [[R(du-.25),.5,.55,1000,'lin'],[R(du+.7),.592,.44,3000],[R(d1+h2['dur']),.596,.44,3150,'lin']]
h1['groups'].append(dict(at=du,lit=['aphelios','yone'],chips=[dict(label='SONGWRITER',x=.51,at=pa,stay=True),dict(label='PRODUCER',x=.657,at=pe,stay=True)]))
for b_ in h1['badges']: b_['until']=R(du-.1)
S[0:2]=[h1]""")
src=src.replace("title='Video 17","title='Video 17 (TRIAL)").replace("'Video 17 — HEARTSTEEL x Riftbound'","'Video 17 — HEARTSTEEL x Riftbound (TRIAL)'")
exec(src)
c=json.load(open('reel_trial.json')); c['voiceover']='vo_trial.wav'; c.pop('cover',None); json.dump(c,open('reel_trial.json','w'),indent=1,ensure_ascii=False)
print(c['voiceover'],c.get('title'),[(s['type'],s['dur']) for s in c['scenes']][:5])
