# Worn footpath camp -> tree -> shrine, stone bench, gravel forecourt, small wooden lanterns.
import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev
from field6 import WH,L1,MG,DG,K
from tree import PK
from fire import FL
from objects2 import STONE,MOSS3,WOOD,put,hx
SOIL=[hx(c) for c in ['#3e3530','#5a4d44','#76675a','#93836f','#ad9d86']]
def path_mask(H,W,pts,rng,bulges=()):
    tck,_=splprep(np.array(pts,float).T,s=0,k=3)
    u=np.linspace(0,1,600); px,py=splev(u,tck)
    yy,xx=np.mgrid[0:H,0:W]
    length=np.hypot(np.diff(px),np.diff(py)).sum()
    if length/200<=3.5:                                       # short paths: 200 samples ~3 px apart, as always
        d=np.full((H,W),99.0); along=np.zeros((H,W))
        for k in range(0,600,3):
            dd=np.hypot(xx-px[k],yy-py[k]); m=dd<d; d[m]=dd[m]; along[m]=u[k]
    else:                                                     # long ones (through several zones): samples 1.5 px apart,
        from scipy.spatial import cKDTree                     # else they fall apart into round slabs
        n=int(length/1.5); u=np.linspace(0,1,n); px,py=splev(u,tck)
        dd,i=cKDTree(np.stack([px,py],1)).query(np.stack([xx.ravel(),yy.ravel()],1),distance_upper_bound=40)
        d=np.where(np.isinf(dd),99.0,dd).reshape(H,W); along=u[np.minimum(i,n-1)].reshape(H,W)
    n=ndi.gaussian_filter(rng.normal(0,1,(H,W)),1.5); n/=n.std()
    width=2.0+1.0*np.sin(along*13)+0.4*np.sin(along*31)+0.45*n   # narrow in places, wider where people step aside
    for (at,amt,spread) in bulges:                           # wider where people cut the corner
        width=width+amt*np.exp(-((along-at)/spread)**2)
    core=d<width; fray=(d<width+1.6)&(rng.random((H,W))<0.30)  # ragged, trodden-out edge
    return core|fray, core, d, width
def draw_path(img,mask,core,d,width,rng):
    H,W,_=img.shape
    g=rng.random((H,W)); bn=ndi.gaussian_filter(rng.normal(0,1,(H,W)),1.0); bn/=bn.std()
    DUST=[hx(c) for c in ['#6f6458','#877a6b','#9f927f','#b6aa95','#cbc0ab']]   # trodden, dusty earth
    v=0.62-0.10*(d/np.maximum(width,0.5))+0.12*bn
    v=np.clip(v,0,0.999)*5; i=np.floor(v).astype(int); f=v-i
    ci=np.clip(i+(g<f*0.9),0,4)
    edge=mask&~core
    img[core]=np.array(DUST)[ci][core]
    keep=edge&(g<0.55)                                   # edge: only some pixels worn, the rest stays ground
    img[keep]=np.array(DUST)[np.clip(ci-1,0,4)][keep]
    # pebbles and a few grass blades left standing in the trodden earth
    peb=core&(g<0.025); img[peb]=L1
    peb2=core&(g>0.985); img[peb2]=MG
    blade=mask&~core&(g>0.85); img[blade]=DG
def forecourt(H,W,cx,cy,rx,ry,rng):
    yy,xx=np.mgrid[0:H,0:W]
    n=ndi.gaussian_filter(rng.normal(0,1,(H,W)),1.8); n/=n.std()
    return ((xx-cx)/rx)**2+((yy-cy)/ry)**2+0.25*n<1
def draw_gravel(img,mask,rng):
    H,W,_=img.shape; g=rng.random((H,W))
    bn=ndi.gaussian_filter(rng.normal(0,1,(H,W)),0.7)
    GRV=[hx(c) for c in ['#7d736a','#9d9285','#bcb2a3','#d8cfbf','#eee8dc']]
    v=np.clip(0.55+0.25*bn+0.2*(g-0.5),0,0.999)*5
    img[mask]=np.array(GRV)[v.astype(int)][mask]
    # scattered small stones (same style as the fire ring stones)
    yy,xx=np.mgrid[0:H,0:W]
    ys,xs=np.where(mask)
    rim=mask&~ndi.binary_erosion(mask,iterations=1); rys,rxs=np.where(rim)
    for k in range(14):
        if k<9: j=rng.integers(len(rys)); sx,sy=rxs[j],rys[j]
        else: j=rng.integers(len(ys)); sx,sy=xs[j],ys[j]
        rx,ry=rng.uniform(1.3,2.2),rng.uniform(0.9,1.4)
        e=((xx-sx)/rx)**2+((yy-sy)/ry)**2
        img[(e<=1.9)&(e>1.0)&((yy-sy)>-0.5)]=K
        m=e<=1.0; lit=(xx-sx)+(yy-sy)*1.3<-0.5
        img[m]=MG; img[m&lit]=L1; img[m&lit&(e<0.3)]=WH
class Bench:
    """Simple stone bench: a slab on two blocks, seen from the front and above."""
    def __init__(s,x,y): s.x,s.y=x,y
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x)/12)**2+((yy-s.y+2)/6)**2<=1
    def draw(s,img):
        x,y=s.x,s.y; G=np.random.default_rng(81).random((16,32))
        def q(v,i,j):
            v=np.clip(v,0,0.999)*5; k=int(v); return STONE[min(4,k+(G[j%16,i%32]<(v-k)*0.9))]
        for i in range(0,18):                                     # cast shadow
            for j in range(0,5):
                if ((i-9)/10)**2+((j-2)/2.6)**2<1: put(img,x-3+i,y+j-1,DG)
        for bx in (-8,5):                                         # legs with dark undersides
            for j in range(-2,1):
                for i in range(0,4): put(img,x+bx+i,y+j,q(0.40-0.12*i,i,j+8))
            for i in range(0,4): put(img,x+bx+i,y+1,K)
        for i in range(-10,11): put(img,x+i,y-2,K if abs(i)<9 else DG)   # shadow line under the slab
        for j in range(-6,-2):                                    # slab: top light, front darker
            for i in range(-10,11):
                if abs(i)==10 and j==-6: continue                 # rounded corners
                v=(0.86 if j<-4 else 0.40)-0.25*(i/10)
                c=q(v,i+16,j+8)
                if G[(j+8)%16,(i*3+5)%32]<0.08: c=MOSS3[1] if j<-3 else MOSS3[0]
                put(img,x+i,y+j,c)
        for (i,j) in [(-4,-6),(2,-5),(6,-6)]: put(img,x+i,y+j,PK[3])   # fallen petals
class WoodLantern:
    """Small wooden post lantern (andon): post, paper box glowing, tiny roof, glow + light pool."""
    def __init__(s,x,y): s.x,s.y=x,y
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x)/4)**2+((yy-s.y+6)/9)**2<=1
    def draw(s,img,t,L):
        t=t%L; H,W,_=img.shape; x,y=s.x,s.y; ph=2*np.pi*t/L
        fl=0.5+0.35*np.sin(ph*11+s.x)+0.15*np.sin(ph*31+s.y)
        yy,xx=np.mgrid[0:H,0:W]
        pd=np.hypot((xx-x)/9,(yy-y-1)/4); pa=np.clip(1-pd,0,1)**1.4*(0.32+0.06*fl)
        sel=pa>0.01; img[sel]=np.clip(img[sel]*(1-pa[sel,None])+np.array([250,150,64])*pa[sel,None],0,255).astype(np.uint8)
        for j in range(0,9): put(img,x,y-j,WOOD[2] if j%3 else WOOD[1]); put(img,x+1,y-j,WOOD[0])   # post
        for j in range(9,13):                                     # paper box
            for i in range(-1,3):
                if i in (-1,2): c=WOOD[1] if i==2 else WOOD[3]
                else: c=FL[6] if (fl>0.55 and i==0) else FL[5] if j in (10,11) else FL[4]
                put(img,x+i,y-j,c)
        for i in range(-2,4): put(img,x+i,y-13,WOOD[3] if i<1 else WOOD[1])   # little roof
        for i in range(-1,3): put(img,x+i,y-14,WOOD[2] if i<1 else WOOD[0])
        cy=y-11; d=np.hypot(xx-x-0.5,(yy-cy)*1.1)/8; a=np.clip(1-d,0,1)**2*(0.28+0.07*fl)
        sel=a>0.01; img[sel]=np.clip(img[sel]*(1-a[sel,None])+np.array([246,176,82])*a[sel,None],0,255).astype(np.uint8)

def draw_earth(img,mask,rng):
    """Trodden earth around the camp: same tones as the path, edge breaks up into the grass."""
    H,W,_=img.shape
    DUST=[hx(c) for c in ['#6f6458','#877a6b','#9f927f','#b6aa95','#cbc0ab']]
    g=rng.random((H,W)); bn=ndi.gaussian_filter(rng.normal(0,1,(H,W)),1.0); bn/=bn.std()
    inner=ndi.binary_erosion(mask,iterations=2)
    v=np.clip(0.55+0.14*bn,0,0.999)*5; i=np.floor(v).astype(int); f=v-i
    ci=np.clip(i+(g<f*0.9),0,4)
    img[inner]=np.array(DUST)[ci][inner]
    edge=mask&~inner&(g<0.55)
    img[edge]=np.array(DUST)[np.clip(ci-1,0,4)][edge]
    peb=inner&(g<0.02); img[peb]=L1
    tuft=mask&~inner&(g>0.9); img[tuft]=DG
