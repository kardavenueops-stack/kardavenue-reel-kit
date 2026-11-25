import wave, numpy as np
from scipy.signal import find_peaks, butter, sosfiltfilt
w=wave.open('vo_raw.wav'); sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
sos=butter(4,[300,2500],btype='band',fs=sr,output='sos'); b=sosfiltfilt(sos,a)
hop=int(sr*.01); env=np.sqrt(np.convolve(b**2,np.ones(hop*3)/(hop*3),'same'))[::hop]
env=np.convolve(env,np.hanning(7)/np.hanning(7).sum(),'same'); db=20*np.log10(env+1e-6)
pk,_=find_peaks(db,prominence=4,distance=8,height=db.max()-35)
t=pk*.01; np.save('beats.npy',t); print(len(t),'beats')
