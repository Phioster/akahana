#!/usr/bin/env python3
"""The mill: axle creak once a quarter turn (Muehle.TURN = 36 s) over a soft trickle and drips. -> wav (loop)."""
import sys, numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
SR=44100; T=36.0; n=int(SR*T); rng=np.random.default_rng(5)
out=np.zeros(n)
# the trickle: soft band noise, slowly breathing, and small drips
noise=sosfilt(butter(2,[900,3800],'bandpass',fs=SR,output='sos'),rng.normal(0,1,n))
t=np.arange(n)/SR
out+=0.05*noise*(0.7+0.3*np.sin(2*np.pi*t/5.3)*np.sin(2*np.pi*t/2.1))
for t0 in np.cumsum(rng.exponential(0.35,200)):
    if t0>T-0.2: break
    k=int(t0*SR); L=int(0.05*SR); tt=np.arange(L)/SR
    f=rng.uniform(1300,2300)*(1-3*tt)
    out[k:k+L]+=rng.uniform(0.03,0.07)*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*70)
# the creak: stick-slip at the axle, once a quarter turn
def creak(dur):
    L=int(dur*SR); x=np.zeros(L); p=0.0
    while p<dur:
        u=p/dur; rate=28+50*u+10*np.sin(9*u)
        x[int(p*SR)]=(np.sin(np.pi*u)**0.7)*rng.uniform(0.6,1)
        p+=1/rate*rng.uniform(0.85,1.15)
    tt=np.arange(int(0.03*SR))/SR
    body=sum(a*np.sin(2*np.pi*f*tt)*np.exp(-tt*d) for f,a,d in ((330,1,140),(640,.6,180),(1180,.35,260),(2100,.15,400)))
    return np.convolve(x,body)[:L]
for q in range(4):
    t0=q*T/4+2.5; c=creak(rng.uniform(0.55,0.8)); k=int(t0*SR)
    out[k:k+len(c)]+=0.07*c
out=out/np.abs(out).max()*0.25
wavfile.write(sys.argv[1],SR,(out*32767).astype(np.int16))
