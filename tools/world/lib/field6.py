# Ground + poppies drawn with the game's rules: flat tones, checker/dot patterns,
# thin dark grass stalks, poppies = red blobs with a dark checker heart.
import numpy as np
from scipy import ndimage as ndi
hx=lambda h:np.array([int(h[i:i+2],16) for i in (1,3,5)],np.uint8)
WH,L1,MG,DG,K=hx('#e8e4dc'),hx('#c3bfba'),hx('#8e888a'),hx('#57505 2'.replace(' ','')),hx('#2e2829')
R,RD=hx('#d8363c'),hx('#93282d')
def ground(H,W,fog,flow,rng):
    yy,xx=np.mgrid[0:H,0:W]; chk=((xx+yy)%2==0)
    img=np.empty((H,W,3),np.uint8)
    f=fog+ndi.gaussian_filter(rng.normal(0,0.06,(H,W)),1.0)
    pale=f>0.62; mid=(f<=0.62)&(f>0.3); dark=f<=0.3
    img[pale]=np.where(chk[pale,None],WH,L1)
    img[mid]=np.where(chk[mid,None],L1,MG)
    img[dark]=np.where(chk[dark,None],MG,DG)
    # grass: thin vertical dark stalks, some with a cross tick; denser in shade and among flowers
    dens=0.15+0.25*(1-f)+0.35*flow
    for _ in range(int(H*W*0.26)):
        x,y=int(rng.integers(1,W-1)),int(rng.integers(1,H-5))
        if rng.random()>dens[y,x]: continue
        c=K if rng.random()<0.5 else DG
        n=int(rng.integers(2,5)); img[y:y+n,x]=c
        t=rng.random()
        if t<0.35: img[y+1,x-1]=c; img[y+1,x+1]=c          # cross
        elif t<0.5: img[y+2,x-1]=c                          # leaf
    return img
# one poppy head, 5x4: '.' none, 'R' red, 'r' dark red, 'k' near-black heart
HEADS=[
 [".RR..","RkRR.","RRkR.",".rR.."],
 [".RRR.","RkRkR","RRkRR",".rRr."],
 ["RR..","RkR.","RRr."],
 [".RR.","RkRR","RRkR","rRr."],
]
CMAP={'R':R,'r':RD,'k':K}
def make_heads(rng,n=60):
    out=[]
    for _ in range(n):
        w,h=int(rng.integers(3,6)),int(rng.integers(3,5))
        yy,xx=np.mgrid[0:h,0:w]
        e=((xx-(w-1)/2)/(w/2))**2+((yy-(h-1)/2)/(h/2))**2+rng.normal(0,0.18,(h,w))
        m=e<1.0
        rows=[]
        for j in range(h):
            row=''
            for i in range(w):
                if not m[j,i]: row+='.'; continue
                # dark heart: short horizontal dashes in the middle rows, checker spaced
                if 0<j<h-1 and abs(i-(w-1)/2)<w/3 and (i+j)%2==0 and rng.random()<0.7: row+='k'
                elif j==h-1 or (j>=h-2 and rng.random()<0.4): row+='r'
                else: row+='R'
            rows.append(row)
        out.append(rows)
    return out
def patches(H,W,flow,blocked,rng,tries=150000):
    """Return flower list [(x,y,head,phase)] in patches of 1-5 touching blooms."""
    occ=np.zeros((H,W),bool); gap=np.zeros((H,W),bool); F=[]
    for _ in range(tries):
        cx,cy=int(rng.integers(5,W-6)),int(rng.integers(5,H-7))
        if gap[cy,cx] or blocked[max(0,cy-5):cy+7,max(0,cx-5):cx+7].any(): continue
        if rng.random()>np.clip((flow[cy,cx]-0.12)/0.3,0,1): continue
        n=int(rng.choice([1,2,3,4,5],p=[.1,.2,.3,.25,.15]))
        for _ in range(n*8):
            x=cx+int(rng.integers(-4,5)); y=cy+int(rng.integers(-3,4))
            if not (2<=x<W-6 and 2<=y<H-6): continue
            if occ[y+1:y+3,x+1:x+4].any(): continue      # blooms may touch, not stack
            occ[y:y+4,x:x+5]=True
            F.append((x,y,int(rng.integers(0,len(HEADS))),rng.random()*6.283))
            n-=1
            if n==0: break
        gap[max(0,cy-6):cy+7,max(0,cx-7):cx+8]=True
    F.sort(key=lambda f:f[1]); return F
def draw_flower(img,x,y,k,dx,blocked):
    H,W,_=img.shape; head=HEADS[k]; h=len(head)
    # leaves/stem under the bloom stay rooted
    for s in range(h,h+2):
        for sx in (x+1,x+2):
            if 0<=sx<W and y+s<H and not blocked[y+s,sx] and (sx+y+s)%2==0: img[y+s,sx]=DG
    for j,row in enumerate(head):
        for i,ch in enumerate(row):
            if ch=='.': continue
            px,py=x+i+dx,y+j
            if 0<=px<W and 0<=py<H and not blocked[py,px]: img[py,px]=CMAP[ch]
def ground_organic(H,W,fog,flow,rng):
    """Ground without any grid: grainy stochastic tones, soft patches, curved grass tufts."""
    from scipy import ndimage as ndi
    yy,xx=np.mgrid[0:H,0:W]
    def fbm(scale,octs=4):
        out=np.zeros((H,W)); a=1; t=0
        for o in range(octs):
            n=ndi.gaussian_filter(rng.normal(0,1,(H,W)),scale/(2**o)); n/=n.std()+1e-9
            out+=a*n; t+=a; a*=0.5
        return out/t
    patch=fbm(10)                                       # earth / moss patches of many sizes
    tone=fog*0.62+0.12-0.24*np.clip(patch,-1.5,1.5)/1.5-0.15*flow
    grain=ndi.gaussian_filter(rng.random((H,W)),0.6)    # clumped grain, not single-pixel noise
    grain=(grain-grain.mean())/grain.std()
    v=tone+0.10*grain
    ramp=[DG,MG,L1,WH]
    cuts=[0.30,0.48,0.70]
    idx=np.digitize(v,cuts)
    img=np.array(ramp)[idx].astype(np.uint8)
    # tufts: 3-5 curved blades fanning out from one root
    dens=0.10+0.25*(1-fog)+0.35*flow
    for _ in range(int(H*W*0.05)):
        x,y=int(rng.integers(3,W-3)),int(rng.integers(5,H-1))
        if rng.random()>dens[y,x]: continue
        c=K if rng.random()<0.35 else DG
        nb=int(rng.integers(3,6)); lean=rng.normal(0.4,0.3)       # wind leans them right
        for b in range(nb):
            spread=(b-(nb-1)/2)*0.55+lean
            L=int(rng.integers(2,5))
            for s in range(L):
                bx=x+int(round(spread*s*0.7+0.15*s*s*np.sign(spread)))
                by=y-s
                if 0<=bx<W and 0<=by<H: img[by,bx]=c if s<L-1 else (DG if c is K else MG)
    # pebbles: small rounded blobs with a lit top-left pixel
    for _ in range(int(H*W*0.0015)):
        x,y=int(rng.integers(2,W-3)),int(rng.integers(2,H-3))
        if flow[y,x]>0.3: continue
        w,h=int(rng.integers(2,4)),int(rng.integers(1,3))
        img[y:y+h,x:x+w]=MG; img[y,x]=WH; img[y+h-1,x+w-1]=DG
    return img
