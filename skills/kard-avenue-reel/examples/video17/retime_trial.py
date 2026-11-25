import wave, numpy as np, json
def load(f):
    w=wave.open(f); return w.getframerate(), np.frombuffer(w.readframes(w.getnframes()),np.int16)
sr,A=load('vo_raw2.wav'); sr2,T=load('trial/vo_trial_raw.wav'); assert sr==sr2
T=np.clip(T.astype(float)*10**(-4.4/20),-32768,32767).astype(np.int16)    # match main VO loudness (-13.8 -> -18.2 LUFS)
OFF=73.0; a=np.concatenate([A,np.zeros(int((OFF-len(A)/sr)*sr),np.int16),T])
b=np.load('beats.npy'); bt=np.load('trial/beats_t.npy')
o=lambda x:round(x+OFF,3)
TS=[(0.29,1.82),(2.06,3.19),(3.49,3.93),(4.33,5.62),(5.96,7.95),(8.24,9.32),(9.63,11.38)]
TL=[0,0,1,1,2,3,3]
MS=[(10.47,11.7),(11.99,12.51),(12.71,13.0),(13.19,13.75),(13.9,14.25),(14.46,14.89),(15.04,15.37),(15.89,17.31),(17.47,17.68),(17.8,18.33),(18.49,20.61),(20.94,24.09),(24.42,26.88),(27.3,28.57),(28.89,30.8),(31.33,32.64),(32.81,35.12),(35.92,38.18),(38.37,38.7),(38.83,39.98),(40.15,41.36),(41.83,42.34),(42.58,44.7),(45.18,46.58),(46.91,48.22),(48.59,52.78),(53.17,55.23),(55.4,56.52),(57.04,58.68),(59.14,60.45),(60.76,61.42),(61.76,63.52),(63.75,65.24)]
ML=[3,3,3,3,3,3,3,4,4,4,4,5,6,6,6,7,7,8,8,8,8,9,9,10,10,11,12,12,13,13,13,14,14]
seg=[(o(s),o(e)) for s,e in TS]+MS
LN=TL+[x+1 for x in ML]          # trial line numbers: 0-2 hook, 3 bridge, 4.. = main lines 3..
NAMES=set(range(len(TS)+1,len(TS)+7))
# gaps between lines (trial line index pairs); main pairs keep their old values
Gm={(0,1):.32,(1,2):.75,(2,3):.5,(3,4):.55,(4,5):.5,(5,6):.6,(6,7):.6,(7,8):.7,(8,9):.6,(9,10):.6,(10,11):.55,(11,12):.55,(12,13):.7,(13,14):.55}
G={(0,1):.45,(1,2):.45,(2,3):.6,(3,4):.5}|{(i+1,j+1):v for (i,j),v in Gm.items() if i>=3}
lead,tail,pad=.15,.6,.03; out=[np.zeros(int(lead*sr),np.int16)]; t=lead; pieces=[]
for i,(s,e) in enumerate(seg):
    s0,e0=s-pad,e+pad; pieces.append((s0,e0,t)); out.append(a[int(s0*sr):int(e0*sr)]); t+=e0-s0
    if i<len(seg)-1:
        raw=seg[i+1][0]-e-2*pad
        if LN[i]!=LN[i+1]: g=G[(LN[i],LN[i+1])]
        elif i+1 in NAMES or i in NAMES: g=max(raw,.3)
        else: g=raw
        out.append(np.zeros(int(g*sr),np.int16)); t+=g
t+=tail; out.append(np.zeros(int(tail*sr),np.int16)); bb=np.concatenate(out)
w=wave.open('assets/vo_trial.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(bb.tobytes()); w.close()
def M(x):
    for s,e,n in pieces:
        if s-1e-6<=x<=e+1e-6: return n+(x-s)
    raise ValueError(x)
def beat_at(s,e,frac,q=b):
    z=q[(q>=s)&(q<=e)]; return float(z[int(round(frac*(len(z)-1)))])
tb=lambda s,e,f: o(beat_at(s,e,f,bt))
SPt=[(0.29,3.19),(3.49,5.62),(5.96,7.95),(8.24,11.38)]
SPm=[(10.47,15.37),(15.89,20.61),(20.94,24.09),(24.42,26.88),(27.3,30.8),(31.33,35.12),(35.92,38.18),(38.37,41.36),(41.83,44.7),(45.18,48.22),(48.59,52.78),(53.17,56.52),(57.04,58.68),(59.14,61.42),(61.76,65.24)]
NS=[(M(o(s)),M(o(e))) for s,e in SPt]+[(M(s),M(e)) for s,e in SPm]
B=[0]+[round((NS[i][1]+NS[i+1][0])/2,2) for i in range(len(NS)-1)]+[round(t,2)]
raw=dict(ezreal=11.99,kayn=12.71,aphelios=13.19,yone=13.9,ksante=14.46,sett=15.2,anggota=10.47,
 paranoia=17.8,baekhyun=beat_at(18.49,20.61,11/17),worlds=beat_at(20.94,24.09,10/19),seoul=beat_at(20.94,24.09,16/19),
 sept=beat_at(24.42,26.88,8/19),baek2=27.3,anderson=beat_at(28.89,30.8,6/17),
 kartu8=beat_at(32.81,35.12,1/12),radiance=beat_at(35.92,38.18,10/13),enam=38.37,pertama=40.15,
 makeover=beat_at(42.58,44.7,7/13),lirik=46.91,nomor=48.59,dari=beat_at(48.59,52.78,20/31),sig=beat_at(53.17,55.23,7/12),ttd=55.4)
cues={k:round(M(v),2) for k,v in raw.items()}
tc=dict(t_enam=tb(.29,1.82,5/7),t_empat=tb(2.06,3.19,2/5),t_dua=o(3.49),t_penulis=o(4.33),t_produser=tb(4.33,5.62,4/5),
 t_keenam=tb(5.96,7.95,4/9),t_kartu=tb(5.96,7.95,7/9),t_heartsteel=tb(8.24,9.32,3/5),t_boyband=o(9.63))
cues.update({k:round(M(v),2) for k,v in tc.items()}); cues['video']=cues['t_enam']
json.dump(dict(B=B,NS=NS,cues=cues),open('scenetimes_trial.json','w'))
print('total',round(t,2))
for i,(x,y) in enumerate(NS[:6]): print(i+1,B[i],B[i+1],round(B[i+1]-B[i],2),'speech',round(x-B[i],2),round(y-B[i],2))
print({k:cues[k] for k in tc})
