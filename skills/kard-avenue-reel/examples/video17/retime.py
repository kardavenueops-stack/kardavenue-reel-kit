import wave, numpy as np, json
w=wave.open('vo_raw2.wav'); sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16)
b=np.load('beats.npy')
seg=[(0.21,1.23),(1.37,3.24),(3.56,5.17),(66.31,71.3),(10.47,11.7),(11.99,12.51),(12.71,13.0),(13.19,13.75),(13.9,14.25),(14.46,14.89),(15.04,15.37),(15.89,17.31),(17.47,17.68),(17.8,18.33),(18.49,20.61),(20.94,24.09),(24.42,26.88),(27.3,28.57),(28.89,30.8),(31.33,32.64),(32.81,35.12),(35.92,38.18),(38.37,38.7),(38.83,39.98),(40.15,41.36),(41.83,42.34),(42.58,44.7),(45.18,46.58),(46.91,48.22),(48.59,52.78),(53.17,55.23),(55.4,56.52),(57.04,58.68),(59.14,60.45),(60.76,61.42),(61.76,63.52),(63.75,65.24)]
# line index of each segment
LN=[0,0,1,2,3,3,3,3,3,3,3,4,4,4,4,5,6,6,6,7,7,8,8,8,8,9,9,10,10,11,12,12,13,13,13,14,14]
G={(0,1):.32,(1,2):.75,(2,3):.5,(3,4):.55,(4,5):.5,(5,6):.6,(6,7):.6,(7,8):.7,(8,9):.6,(9,10):.6,(10,11):.55,(11,12):.55,(12,13):.7,(13,14):.55}
NAMES=set(range(5,11))   # L4 name segments: give each name a little air
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
import os; os.makedirs('assets',exist_ok=True)
o=wave.open('assets/vo_final.wav','wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(bb.tobytes()); o.close()
def M(x):
    for s,e,n in pieces:
        if s-1e-6<=x<=e+1e-6: return n+(x-s)
    best=min(pieces,key=lambda p:min(abs(x-p[0]),abs(x-p[1]))); return best[2]+(x-best[0])
def beat_at(s,e,frac):
    q=b[(b>=s)&(b<=e)]; return float(q[int(round(frac*(len(q)-1)))])
SP=[(0.21,3.24),(3.56,5.17),(66.31,71.3),(10.47,15.37),(15.89,20.61),(20.94,24.09),(24.42,26.88),(27.3,30.8),(31.33,35.12),(35.92,38.18),(38.37,41.36),(41.83,44.7),(45.18,48.22),(48.59,52.78),(53.17,56.52),(57.04,58.68),(59.14,61.42),(61.76,65.24)]
NS=[(M(s),M(e)) for s,e in SP]
B=[0]+[round((NS[i][1]+NS[i+1][0])/2,2) for i in range(len(NS)-1)]+[round(t,2)]
raw=dict(video=1.37+.1,ezreal=11.99,kayn=12.71,aphelios=13.19,yone=13.9,ksante=14.46,sett=15.2,anggota=10.47,
 paranoia=17.8,baekhyun=beat_at(18.49,20.61,11/17),worlds=beat_at(20.94,24.09,10/19),seoul=beat_at(20.94,24.09,16/19),
 sept=beat_at(24.42,26.88,8/19),baek2=27.3,anderson=beat_at(28.89,30.8,6/17),
 kartu8=beat_at(32.81,35.12,1/12),radiance=beat_at(35.92,38.18,10/13),enam=38.37,pertama=40.15,
 makeover=beat_at(42.58,44.7,7/13),lirik=46.91,nomor=48.59,dari=beat_at(48.59,52.78,20/31),sig=beat_at(53.17,55.23,7/12),ttd=55.4)
cues={k:round(M(v),2) for k,v in raw.items()}
json.dump(dict(B=B,NS=NS,cues=cues),open('scenetimes.json','w'))
print('total',round(t,2))
for i,(x,y) in enumerate(NS): print(i+1,B[i],B[i+1],round(B[i+1]-B[i],2),'speech',round(x-B[i],2),round(y-B[i],2))
print(cues)
