# Small campfire: organic stone ring, flickering flames, smoke drifting with the wind.
# Every motion uses whole cycles per LOOP, so frame LOOP == frame 0.
import numpy as np
from scipy import ndimage as ndi
from field6 import WH,L1,MG,DG,K
hx=lambda h:np.array([int(h[i:i+2],16) for i in (1,3,5)],np.uint8)
FL=[hx(c) for c in ['#5c161b','#8e2024','#c4302e','#e4532c','#f08a34','#f7bf52','#fde7a6','#fffbe8']]   # ember .. white-hot
SMOKE=[hx('#6e6769'),hx('#8f898b'),hx('#aaa4a2'),hx('#c9c4c0'),hx('#ebe7e1')]   # dark .. lit
def bilin(a,y,x):
    # smooth (sub-pixel) lookup in a wrapping texture, so shapes glide instead of hopping
    H,W=a.shape; y0=np.floor(y).astype(int); x0=np.floor(x).astype(int); fy=y-y0; fx=x-x0
    y0%=H; x0%=W; y1=(y0+1)%H; x1=(x0+1)%W
    return (a[y0,x0]*(1-fy)*(1-fx)+a[y0,x1]*(1-fy)*fx+a[y1,x0]*fy*(1-fx)+a[y1,x1]*fy*fx)
class Fire:
    def __init__(self,cx,cy,LOOP,rng):
        self.cx,self.cy,self.L=cx,cy,LOOP
        self.rng=rng
        # stones around an ellipse, each a lumpy blob
        self.stones=[]
        for k in range(9):
            a=2*np.pi*k/9+rng.normal(0,0.12)
            sx=cx+10.0*np.cos(a)+rng.normal(0,0.6); sy=cy+5.2*np.sin(a)+rng.normal(0,0.4)
            self.stones.append((sx,sy,rng.uniform(1.8,2.8),rng.uniform(1.3,2.0),rng.normal(0,1)))
        self.tex=rng.random((64,64))
        self.fnoise=rng.random((32,32))
        f2=ndi.gaussian_filter(rng.random((64,64)),1.2,mode='wrap'); self.fnoise2=(f2-f2.min())/(f2.max()-f2.min())
        ct=ndi.gaussian_filter(rng.random((64,64)),1.0,mode='wrap'); self.ctex=(ct-ct.min())/(ct.max()-ct.min())   # clumpy thinning
        # smoke puffs: emitted evenly over the loop, each lives exactly one loop
        self.puffs=[(i*LOOP/8+rng.uniform(-4,4),rng.uniform(-2,2),rng.uniform(0.7,1.3),rng.uniform(0,6.28)) for i in range(8)]
        # every puff gets its own look: texture offset, squash, stretch along the wind, base tone
        self.look=[dict(ox=rng.uniform(0,64),oy=rng.uniform(0,64),asp=rng.uniform(0.55,0.95),
                        stretch=rng.uniform(1.0,1.6),tone=rng.uniform(-0.45,0.45),scale=rng.uniform(0.7,1.4))
                   for _ in range(8)]
        self.pnoise=ndi.gaussian_filter(rng.normal(0,1,(40,40)),1.4); self.pnoise/=self.pnoise.std()
    def ground(self,img,blocked):
        """Static part: stone ring + ash. Marks the area so flowers stay out."""
        H,W,_=img.shape; yy,xx=np.mgrid[0:H,0:W]
        ash=((xx-self.cx)/8.5)**2+((yy-self.cy)/4.4)**2<=1
        img[ash]=np.where((self.tex[yy[ash]%64,xx[ash]%64]<0.5)[:,None],K,DG)
        for sx,sy,rx,ry,_ in self.stones:
            e=((xx-sx)/rx)**2+((yy-sy)/ry)**2
            img[(e<=1.9)&(e>1.0)&((yy-sy)>-0.5)]=K
            m=e<=1.0
            lit=(xx-sx)+(yy-sy)*1.3<-0.5
            img[m]=MG; img[m&lit]=L1; img[m&(e>0.55)&~lit&((yy-sy)>0)]=DG
            img[m&lit&(e<0.3)]=WH
        blocked|=ndi.binary_dilation(((xx-self.cx)/11)**2+((yy-self.cy)/6.5)**2<=1,iterations=2)
        return img
    def draw(self,img,t):
        t=t%self.L                                          # identical maths for t and t+LOOP
        H,W,_=img.shape; ph=2*np.pi*t/self.L; cx,cy=self.cx,self.cy
        yy,xx=np.mgrid[0:H,0:W]
        # flame: a round belly with several tongues of different height, each bending in an S
        H0=15.0
        tongues=[(-2.6,0.62,1.7,0.0),(-0.6,1.00,2.0,1.1),(1.5,0.80,1.8,2.3),(3.2,0.45,1.3,3.7)]
        hgt=np.zeros(W); xs=np.arange(W)
        for k,(ox,hs,wd,pk) in enumerate(tongues):
            h=H0*hs*(0.82+0.18*np.sin(ph*11+pk)+0.08*np.sin(ph*23+pk*2))
            hgt=np.maximum(hgt,h*np.exp(-((xs-(cx+ox+0.6*np.sin(ph*7+pk)))/wd)**2))
        belly=4.0*np.clip(1-((xs-cx-0.3)/5.2)**2,0,1)**0.5          # rounded base
        hgt=np.maximum(hgt,belly)
        for y in range(int(cy-H0-3),int(cy)+2):
            up=cy+1-y
            if up<0: continue
            # S-bend: the higher a slice, the more it is pushed sideways (wind + wobble)
            bend=0.07*up**1.5*0.6+0.9*np.sin(ph*9+up*0.45)*(up/H0)
            xi=np.round(xs-bend).astype(int).clip(0,W-1)
            hh=hgt[xi]
            inside=(up<hh)&(hh>1.0)                                   # ignore the far tails of the curves
            for x in np.where(inside)[0]:
                v=1-up/max(hh[x],0.1)                                 # 1 at the foot, 0 at the tip
                cen=np.exp(-((x-bend-cx)/3.0)**2)
                heat=0.55*v+0.45*cen*v**0.5
                heat+=0.12*(self.fnoise[(y*3+int(32*t/self.L))%32,(x*5)%32]-0.5)   # flicker detail
                ci=int(np.clip(round(heat*7),0,7))
                if up>hh[x]-1.2: ci=min(ci,2)                         # dark red rim at the tips
                img[y,x]=FL[ci]
        # a detached flicker above the tallest tongue, now and then
        if np.sin(ph*5)>0.55:
            fy=int(cy-H0-2-3*(np.sin(ph*5)-0.55)); fx=int(cx-0.6+0.08*H0**1.5)
            if 0<=fy<H and 0<=fx<W: img[fy,fx]=FL[3]; img[fy-1,fx]=FL[2]
        # now and then a spark climbs high through the smoke and dies out
        for k in range(2):
            age=((t/self.L)*2+k*0.5)%1.0
            if age>0.6: continue
            a2=age/0.6
            sx2=int(round(cx+1+30*a2**1.4+3*np.sin(a2*10+k))); sy2=int(round(cy-14-50*a2))
            if 0<=sx2<W and 0<=sy2<H: img[sy2,sx2]=FL[7 if a2<0.3 else 5 if a2<0.7 else 3]
        # a few sparks rising and drifting with the wind (no ring)
        for k in range(5):
            age=((t/self.L)*3+k/5)%1.0
            sx2=int(cx+2+age*14+2*np.sin(age*9+k)); sy2=int(cy-12-age*26)
            if 0<=sx2<W and 0<=sy2<H and age<0.8: img[sy2,sx2]=FL[6 if age<0.3 else 4]
        # embers inside the ring (over the flame foot, so it grows out of the glow)
        sh=int(64*t/self.L)%64
        em=(((xx-cx)/6)**2+((yy-cy)/3)**2<=1)&(self.tex[(yy+2*sh)%64,xx%64]<0.18)
        img[em]=np.where((self.tex[yy[em]%64,xx[em]%64]<0.09)[:,None],FL[4],FL[1])
        for sx,sy,rx,ry,_ in self.stones:
            if sy<=cy: continue
            e=((xx-sx)/rx)**2+((yy-sy)/ry)**2; img[(e<=1.9)&(e>1.0)&((yy-sy)>-0.5)]=K; m=e<=1.0; lit=(xx-sx)+(yy-sy)*1.3<-0.5
            img[m]=MG; img[m&lit]=L1; img[m&(e>0.55)&~lit&((yy-sy)>0)]=DG; img[m&lit&(e<0.3)]=WH
        return img
    def smoke(self,img,t):
        """Smoke on top of everything: puffs rise, swell and blow right, thinning to nothing."""
        t=t%self.L
        H,W,_=img.shape; yy,xx=np.mgrid[0:H,0:W]
        for (t0,jx,sz,wph),lk in zip(self.puffs,self.look):
            age=((t-t0)%self.L)/self.L                     # 0..1, wraps -> exact loop
            px=self.cx+jx+52*age**1.6+5*np.sin(age*5.0+wph)     # rises first, then the wind takes it          # carried by the wind
            py=self.cy-10-58*age+22*age*age+3*np.sin(age*6.0+wph*1.3)              # rises, then levels out
            r=(2.5+age*10)*sz
            dens=np.clip(1.25-age*1.2,0,1)*np.clip(age/0.08,0,1)       # fades in, then thins out
            if dens<=0: continue
            pad=r*1.8+4                                      # generous box: torn edges never get clipped
            x0,x1=int(max(0,px-pad)),int(min(W,px+pad)); y0,y1=int(max(0,py-pad)),int(min(H,py+pad))
            if x0>=x1 or y0>=y1: continue
            sy,sx=np.mgrid[y0:y1,x0:x1].astype(float)
            ly,lx=sy-py,sx-px                                # float offsets: the puff glides
            d=np.sqrt((lx/(r*lk['stretch']))**2+(ly/(r*lk['asp']))**2)
            n=bilin(self.pnoise,ly*0.8*lk['scale']+lk['oy'],lx*0.8*lk['scale']+lk['ox'])
            body=d+0.5*n<1
            keep=bilin(self.ctex,ly+lk['oy'],lx+lk['ox'])<dens*1.05
            m=body&keep
            la=wph+age*2.5
            grad=(lx*np.cos(la)+ly*np.sin(la))/r
            # form: light side vs shadow side, plus small billows (fine noise) that each catch light
            fine=bilin(self.fnoise2,ly*1.6*lk['scale']+lk['ox'],lx*1.6*lk['scale']+lk['oy'])
            core=np.clip(1-d,0,1)                            # denser, darker middle
            shade=0.5*grad+0.35*bilin(self.pnoise,ly+lk['ox']+17,lx+lk['oy']+29)+0.45*(fine-0.5)+0.35*core*(age>0.2)-lk['tone']
            ci=np.clip(np.round(2-shade*2.2),0,4).astype(int)
            rim=body&~ndi.binary_erosion(body)&(grad<0)      # thin lit edge on the light side
            ci[rim]=4
            sub=img[y0:y1,x0:x1]; sub[m]=np.array(SMOKE)[ci][m]
        return img
