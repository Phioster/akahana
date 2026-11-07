#!/usr/bin/env python3
"""Preview loop of the mill (wheel turning, flume glints, falling water): frames for an MP4. args: out_dir n_frames"""
import os, sys, time
import numpy as np
from PIL import Image
T='/data/data/com.termux/files/home/mohnweg/tools/world/west'
sys.path[:0]=[T, T+'/../lib', T+'/..', T+'/../south']
from field6 import ground_organic
import mood_map, objects_west as o
rng=np.random.default_rng(2); H,W=100,150
base=ground_organic(H,W,np.full((H,W),0.6),np.full((H,W),0.3),rng).astype(float)*np.array([0.88,1,0.86])*0.7
yy,xx=np.mgrid[0:H,0:W]
bw=lambda x:(30+0.55*x, 3.5+x/60)
cy,hw=bw(xx)
base[np.abs(yy-cy)<hw]=o.hx('#4e5a65')
G=np.random.default_rng(3).random((H,W))
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
N=int(sys.argv[2]); fps=12
for f in range(N):
    t0=time.time()
    img=base.copy(); m=o.Muehle(110,62,brook=bw); m.t=f/fps
    m.draw(img,G)
    Image.fromarray(np.clip(mood_map.grade(img),0,255).astype(np.uint8)).resize((W*5,H*5),Image.NEAREST).save(f'{out}/f{f:03d}.png')
    if f==0: print('frame s', round(time.time()-t0,2), flush=True)
