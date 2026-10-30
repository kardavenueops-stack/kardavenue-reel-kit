import numpy as np, wave, os
SR=48000
rng=np.random.default_rng(7)
def t(d): return np.arange(int(SR*d))/SR
def env(n,a,r,shape=4):
    x=np.ones(n); A=int(SR*a)
    if A: x[:A]=np.linspace(0,1,A)
    x*=np.exp(-np.linspace(0,shape,n)) if r else 1
    return x
def lp(x,c):  # one-pole lowpass, c in Hz (array or float)
    c=np.broadcast_to(c,x.shape); y=np.zeros_like(x); a=1-np.exp(-2*np.pi*c/SR); s=0.
    for i in range(len(x)): s+=a[i]*(x[i]-s); y[i]=s
    return y
def hp(x,c): return x-lp(x,c)
def norm(x,peak=0.9): return x/ (np.abs(x).max()+1e-9)*peak
def save(name,x):
    x=np.clip(x,-1,1); st=np.stack([x,x],1)
    with wave.open(name,'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())

# whoosh: filtered noise sweep, swell then fade
d=0.55; n=int(SR*d); tt=t(d)
noise=rng.standard_normal(n)
cut=300+5500*np.sin(np.pi*tt/d)**2
w=hp(lp(noise,cut),150)*np.sin(np.pi*tt/d)**1.5
save('whoosh.wav',norm(w,0.8))

# bass hit / impact: sine drop 90->35Hz + click + noise burst
d=1.2; tt=t(d); f=35+55*np.exp(-tt*9)
ph=2*np.pi*np.cumsum(f)/SR
body=np.sin(ph)*np.exp(-tt*3.2)
click=rng.standard_normal(len(tt))*np.exp(-tt*120)*0.6
sub=np.tanh(2.2*(body+click))
save('impact.wav',norm(sub,0.95))

# stamp thud: short low thump + paper slap
d=0.35; tt=t(d); f=60+120*np.exp(-tt*30)
th=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*14)
slap=hp(rng.standard_normal(len(tt)),1200)*np.exp(-tt*60)*0.5
save('stamp.wav',norm(np.tanh(1.8*(th+slap)),0.9))

# pop: quick pitch-up blip
d=0.12; tt=t(d); f=400+900*(tt/d)
save('pop.wav',norm(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*40)*np.minimum(1,tt*800),0.7))

# ding: bell-like partials
d=1.4; tt=t(d); x=sum(a*np.sin(2*np.pi*f*tt)*np.exp(-tt*k) for f,a,k in [(1318,1,3),(2637,.5,5),(3950,.25,7),(1975,.3,4)])
save('ding.wav',norm(x*np.minimum(1,tt*400),0.6))

# tick: tiny click for counters
d=0.03; tt=t(d)
save('tick.wav',norm(hp(rng.standard_normal(len(tt)),3000)*np.exp(-tt*300),0.5))

# typing: 10 random ticks
d=1.0; x=np.zeros(int(SR*d)); tk=hp(rng.standard_normal(int(SR*.02)),2500)*np.exp(-t(.02)*250)
for s in np.sort(rng.uniform(0,0.95,10)):
    i=int(s*SR); x[i:i+len(tk)]+=tk*rng.uniform(.5,1)
save('typing.wav',norm(x,0.5))

# card flick: bright short noise snap
d=0.09; tt=t(d)
save('flick.wav',norm(hp(rng.standard_normal(len(tt)),2000)*np.exp(-tt*55)*np.minimum(1,tt*2000),0.6))

# riser: noise + rising saw-ish tone, 2.5s, cuts hard at end
d=2.5; tt=t(d); n=len(tt)
f=120*2**(tt/d*3)
tone=np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*0.25+np.sin(2*np.pi*np.cumsum(f*2)/SR)*0.2
nz=hp(lp(rng.standard_normal(n),400+8000*(tt/d)**2),200)
x=(tone+nz)*(tt/d)**2
save('riser.wav',norm(x,0.75))

# shimmer: sparkly high partials with random pings
d=1.2; tt=t(d); x=np.zeros_like(tt)
for _ in range(14):
    s=rng.uniform(0,0.9); f=rng.uniform(2500,6000); m=tt>=s
    x[m]+=np.sin(2*np.pi*f*(tt[m]-s))*np.exp(-(tt[m]-s)*9)*rng.uniform(.3,1)
save('shimmer.wav',norm(x*np.sin(np.pi*tt/d),0.45))
print(sorted(os.listdir('.')))
