# Readable-size camp objects: polygon shapes with wobbly (hand-made) edges.
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from field6 import WH,L1,MG,DG,K
from tree import PK,BARK
from fire import FL
from objects import CANVAS,RED,MOSS,put,hx
def poly(H,W,pts,rng=None,wob=0.0):
    im=Image.new('L',(W,H),0); ImageDraw.Draw(im).polygon([tuple(p) for p in pts],fill=1)
    m=np.asarray(im).astype(bool)
    if rng is not None and wob>0:                       # roughen the outline a little
        n=ndi.gaussian_filter(rng.normal(0,1,(H,W)),1.0)
        edge=m^ndi.binary_erosion(m); out=ndi.binary_dilation(m)&~m
        m=(m&~(edge&(n<-wob)))|(out&(n>wob))
    return m
class Tent2:
    """A-frame tent, shaded per pixel like the tree: light field -> 5 cloth tones with fine grain."""
    def __init__(s,x,y,rng): s.x,s.y=x,y
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x-2)/14)**2+((yy-s.y+8)/13)**2<=1
    def draw(s,img,t,L):
        H,W,_=img.shape; x,y=s.x,s.y; ph=2*np.pi*t/L
        r=np.random.default_rng(7); yy,xx=np.mgrid[0:H,0:W]
        A=(x,y-13); Ab=(x+3,y-24); FL_=(x-10,y); FR=(x+10,y); BL=(x-7,y-12); BR=(x+13,y-11)
        # soft ragged ground shadow on the lee side
        shadow=poly(H,W,[FR,(x+17,y-2),(x+19,y-12),BR],r,0.9)
        sn=ndi.gaussian_filter(np.random.default_rng(21).normal(0,1,(H,W)),1.2)
        img[shadow&(sn>-0.6)]=DG; img[shadow&(sn>0.5)]=MG
        left=poly(H,W,[A,Ab,BL,FL_],r,0.7); right=poly(H,W,[A,Ab,BR,FR],r,0.7); gable=poly(H,W,[A,FL_,FR],r,0.5)
        # light field
        rid=np.abs((xx-A[0])*(Ab[1]-A[1])-(yy-A[1])*(Ab[0]-A[0]))/np.hypot(Ab[0]-A[0],Ab[1]-A[1])
        bn=ndi.gaussian_filter(np.random.default_rng(23).normal(0,1,(H,W)),0.9); bn/=bn.std()
        along=((xx-A[0])*(Ab[0]-A[0])+(yy-A[1])*(Ab[1]-A[1]))/np.hypot(Ab[0]-A[0],Ab[1]-A[1])**2
        folds=0.10*np.sin(along*np.pi*3)                         # cloth sags between poles -> bands
        pull=np.zeros((H,W))
        for (cx_,cy_) in (FL_,FR,BL,BR):                         # tension near the pegged corners
            d=np.hypot(xx-cx_,yy-cy_); pull+=0.06*np.cos(d*1.4)*np.exp(-d/4)
        Lt=np.zeros((H,W))
        Lt[left]=(0.88-0.03*rid+folds*0.7+pull+0.06*bn)[left]
        Lt[right]=(0.50-0.02*rid+folds*0.6+pull*0.7+0.06*bn)[right]
        g=gable
        Lt[g]=(0.66-0.022*(xx-x)-0.008*(yy-(y-13))+0.05*bn+pull*0.5)[g]
        # seams: thin slightly darker lines down each slope, sagging
        seam=np.zeros((H,W),bool)
        for k in (0.33,0.66):
            p0=(A[0]+(Ab[0]-A[0])*k,A[1]+(Ab[1]-A[1])*k)
            for (q0,q1) in ((FL_,BL),(FR,BR)):
                q=(q0[0]+(q1[0]-q0[0])*k,q0[1]+(q1[1]-q0[1])*k)
                for u in np.linspace(0,1,24):
                    sx=int(round(p0[0]+(q[0]-p0[0])*u)); sy=int(round(p0[1]+(q[1]-p0[1])*u+0.8*np.sin(np.pi*u)))
                    if 0<=sx<W and 0<=sy<H: seam[sy,sx]=True
        Lt[seam]-=0.14
        # ridge catches the light
        Lt[(left|right)&(rid<1.0)]+=0.12
        # front edges of the gable catch light (left) / fall into shade (right): keeps the form readable
        gedge=gable&~ndi.binary_erosion(gable)&(yy<y)
        Lt[gedge&(xx<=x)]=0.95; Lt[gedge&(xx>x)]=0.45
        cloth=left|right|gable
        grain=np.random.default_rng(24).random((H,W))
        v=np.clip(Lt,0,0.999)*5; i=np.floor(v).astype(int); f=v-i
        ci=np.clip(i+(grain<f*0.9),0,4)                          # irregular grain between tones
        img[cloth]=np.array(CANVAS)[ci][cloth]
        # door: graded darkness inside, folded-back flap with its own light and darker underside
        door=poly(H,W,[(x,y-10),(x-4,y),(x+4,y)])
        depth=(yy-(y-10))/10
        dv=np.clip(0.05+0.12*depth+0.04*bn,0,0.3)
        img[door]=np.where((dv>0.14)[...,None],DG,K)[door]
        flap_off=0.7*np.sin(ph*5)
        flap=poly(H,W,[(x,y-10),(x+4+flap_off,y),(x+7+flap_off,y-2)])
        fv=0.55+0.18*(xx-x)/7-0.15*((yy-(y-10))/10)+0.07*bn
        fi=np.clip(np.floor(np.clip(fv,0,0.999)*5+(grain-0.5)*0.8),0,4).astype(int)
        img[flap]=np.array(CANVAS)[fi][flap]
        under=flap&~ndi.binary_erosion(flap)&(xx<x+3)
        img[under]=CANVAS[0]                                    # underside edge of the fold
        # poles at the apexes, pegs and thin guy lines
        for (px,py) in (A,Ab): put(img,px,py-1,BARK[1]); put(img,px,py-2,BARK[2])
        for (gx,gy,dx,dy) in [(x-10,y,-5,2),(x+10,y,4,3),(x-7,y-12,-5,-2),(x+13,y-11,4,-1)]:
            for k in range(1,6):
                if k%2 or k==5: put(img,gx+int(round(dx*k/5)),gy+int(round(dy*k/5)),DG)
            put(img,gx+dx,gy+dy,BARK[2]); put(img,gx+dx,gy+dy-1,BARK[3])
def outline(img,mask,c=K,below_only=False):
    H,W,_=img.shape
    ring=ndi.binary_dilation(mask)&~mask
    if below_only:
        ring&=np.roll(mask,1,axis=0)|np.roll(mask,-1,axis=1)|np.roll(mask,1,axis=1)
    img[ring]=c
class Shrine2:
    """Small hokora: two stone steps, timber body with doors, big swept roof, moss, rope."""
    def __init__(s,x,y,rng): s.x,s.y=x,y
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x)/16)**2+((yy-s.y+10)/16)**2<=1
    def draw(s,img,t,L):
        H,W,_=img.shape; x,y=s.x,s.y; ph=2*np.pi*t/L; r=np.random.default_rng(11)
        yy,xx=np.mgrid[0:H,0:W]
        # stone steps / plinth
        st1=poly(H,W,[(x-12,y),(x+12,y),(x+11,y-3),(x-11,y-3)],r,0.8)
        st2=poly(H,W,[(x-9,y-3),(x+9,y-3),(x+8,y-5),(x-8,y-5)],r,0.8)
        for m in (st1,st2):
            img[m]=MG; img[m&(xx<x-3)]=L1; img[m&(xx>x+5)]=DG
            outline(img,m,DG,True)
        # timber body with two doors and a dark gap between them
        body=poly(H,W,[(x-7,y-5),(x+7,y-5),(x+7,y-15),(x-7,y-15)],r,0.4)
        img[body]=BARK[2]; img[body&(xx>x+3)]=BARK[1]
        img[body&((xx-x)%4==0)]=BARK[1]                     # planks
        door=(np.abs(xx-x)<=3)&(yy<=y-6)&(yy>=y-13)
        img[door]=BARK[3]; img[door&(xx==x)]=K; img[door&(yy==y-13)]=BARK[1]
        img[door&(xx==x-2)&(yy==y-9)]=FL[3]; img[door&(xx==x+2)&(yy==y-9)]=FL[3]   # little brass rings
        # roof: wide, sagging middle, eaves sweep up at the ends, ridge on top
        pts=[(x-16,y-14),(x-12,y-16),(x,y-15),(x+12,y-16),(x+16,y-14),(x+13,y-20),(x+4,y-26),(x-4,y-26),(x-13,y-20)]
        roof=poly(H,W,pts,r,0.5)
        img[roof]=DG; img[roof&(xx<x+1)]=MG
        img[roof&((yy-(y-26))%3==0)]=np.where((xx[roof&((yy-(y-26))%3==0)]<x+1)[:,None],DG,K)   # tile rows
        img[roof&(yy>=y-16)&(xx<x)]=L1                       # lit eave edge
        outline(img,roof,K)
        for k in range(-5,6): put(img,x+k,y-27,MG if k<0 else DG)   # ridge
        put(img,x-6,y-28,DG); put(img,x+6,y-28,K)
        for (dx,dy) in [(-11,18),(-8,21),(-3,24),(5,23),(9,19),(-14,15),(12,17)]:
            put(img,x+dx,y-dy,MOSS[(dx+dy)%2])
        # shimenawa rope + paper streamers fluttering
        for k in range(-7,8): put(img,x+k,y-15+int(round(0.6*np.cos(k*0.45))),L1)
        for j,dx in enumerate((-5,0,5)):
            sw=np.sin(ph*5+j*1.9)
            for d in range(1,5): put(img,x+dx+int(round(sw*(d/4)*1.5)),y-15+d,WH if d%2 else L1)
class Banner2:
    """Nobori next to the shrine: bamboo pole, red cloth with a white disc, ripples in the wind."""
    def __init__(s,x,y,h,rng): s.x,s.y,s.h=x,y,h
    def draw(s,img,t,L):
        x,y,h=s.x,s.y,s.h; ph=2*np.pi*t/L; top=y-h
        for yy in range(top,y+1):
            k=(y-yy)
            px=int(round(x+0.5*np.sin(k/18)))
            put(img,px,yy,hx('#c2b183') if k%6 else hx('#7d6f4c')); put(img,px+1,yy,hx('#8c7d55'))
        for i in range(0,10): put(img,x+1+i,top+1,hx('#8c7d55'))
        bw,bh=8,int(h*0.62)
        for j in range(bh):
            wave=1.4*np.sin(ph*4-j*0.32)*(j/bh)
            lean=0.12*j
            for i in range(bw):
                xi=int(round(x+2+i+wave+lean))
                sh=np.sin(ph*4-j*0.32+i*0.3)
                c=RED[3] if sh>0.6 else RED[2] if sh>-0.25 else RED[1]
                if i in (0,bw-1): c=RED[1]
                if 4<=j<=10 and (i-3.5)**2+(j-7)**2<=6: c=WH if sh>-0.25 else L1
                put(img,xi,top+2+j,c)
            if j==bh-1:
                for i in range(0,bw,2): put(img,int(round(x+2+i+wave+lean)),top+3+j,RED[0])
        # small stone base
        for i in range(-2,4): put(img,x+i,y+1,MG if i<1 else DG)
class Lantern2:
    """Stone tōrō: wide base, post, shelf, light box, curved cap and jewel finial."""
    def __init__(s,x,y,rng): s.x,s.y=x,y
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x)/7)**2+((yy-s.y+9)/12)**2<=1
    def draw(s,img,t,L):
        H,W,_=img.shape; x,y=s.x,s.y; ph=2*np.pi*t/L; r=np.random.default_rng(13)
        yy,xx=np.mgrid[0:H,0:W]
        parts=[poly(H,W,[(x-5,y),(x+5,y),(x+4,y-2),(x-4,y-2)],r,0.6),          # base
               poly(H,W,[(x-2,y-2),(x+2,y-2),(x+2,y-8),(x-2,y-8)],r,0.4),       # post
               poly(H,W,[(x-5,y-8),(x+5,y-8),(x+4,y-10),(x-4,y-10)],r,0.5),     # shelf
               poly(H,W,[(x-3,y-10),(x+3,y-10),(x+3,y-15),(x-3,y-15)]),         # light box
               poly(H,W,[(x-7,y-15),(x+7,y-15),(x+3,y-19),(x-3,y-19)],r,0.5)]   # cap
        for k,m in enumerate(parts):
            img[m]=MG; img[m&(xx<x)]=L1; img[m&(xx>x+1)]=DG
            outline(img,m,K,True)
        box=parts[3]
        fl=0.5+0.5*np.sin(ph*13+np.sin(ph*7))
        win=box&(np.abs(xx-x)<=1)&(yy>=y-14)&(yy<=y-11)
        img[win]=FL[5]; img[win&(xx==x)]=FL[7] if fl>0.4 else FL[6]
        put(img,x-7,y-16,MG); put(img,x+7,y-16,DG)                               # upturned corners
        put(img,x,y-20,MG); put(img,x,y-21,L1)                                   # finial
        put(img,x+3,y-1,MOSS[0]); put(img,x+4,y-9,MOSS[1]); put(img,x+5,y-16,MOSS[0])
        for (dx,dy) in [(-3,2),(2,2),(4,3),(-5,3),(0,4),(6,4)]:                  # warm light on the ground
            if (dx+int(fl*3))%2==0: put(img,x+dx,y+dy,FL[5])
BAMBOO=[hx(c) for c in ['#5f5236','#7d6f4c','#a2915f','#c4b27d','#ddd0a0']]
RED5=[hx(c) for c in ['#4e1215','#7e1b20','#ad2329','#cc2e2e','#da4238']]
WHITE5=[hx(c) for c in ['#8f8986','#b3ada8','#d1ccc4','#e6e1d7','#f5f1e8']]
class Banner3:
    """Nobori with per-pixel cloth light: folds travel down the cloth in the wind."""
    def __init__(s,x,y,h,rng): s.x,s.y,s.h=x,y,h
    def draw(s,img,t,L):
        t=t%L                                                   # exact loop
        H,W,_=img.shape; x,y,h=s.x,s.y,s.h; ph=2*np.pi*t/L; top=y-h
        grain=np.random.default_rng(31).random((H,W))
        # blotchy cloth texture in cloth coordinates, so it travels with the fabric
        cn=ndi.gaussian_filter(np.random.default_rng(32).normal(0,1,(64,16)),1.1,mode='wrap'); cn/=cn.std()
        def q(pal,v,xx_,yy_):                                   # value -> palette with fine grain
            v=np.clip(v,0,0.999)*len(pal); i=int(v); f=v-i
            return pal[min(len(pal)-1,i+(grain[yy_%H,xx_%W]<f*0.9))]
        # bamboo pole: rounded (lit left), nodes every 6 px with a darker ring and light lip
        for yy in range(top,y+1):
            k=y-yy; px=int(round(x+0.5*np.sin(k/18)))
            node=k%6==0
            for dx,base in ((0,0.78),(1,0.42)):
                v=base-(0.35 if node else 0)+(0.12 if (k%6==1 and dx==0) else 0)
                if 0<=px+dx<W and 0<=yy<H: img[yy,px+dx]=q(BAMBOO,v,px+dx,yy)
        # cross bar
        for i in range(0,10):
            if 0<=x+1+i<W: img[top+1,x+1+i]=q(BAMBOO,0.6-0.03*i,x+1+i,top+1); img[top+2,x+1+i]=BAMBOO[1] if i%3 else BAMBOO[0]
        # cloth hangs from the bar (top edge) and the pole (left edge, via loops)
        bw,bh=8,int(h*0.62)
        for j in range(bh):
            amp=(j/bh)**1.2
            wave=1.5*np.sin(ph*4-j*0.32)*amp
            lean=0.12*j
            for i in range(bw):
                xi=int(round(x+2+i+wave+lean)); yi=top+3+j
                if not(0<=xi<W and 0<=yi<H): continue
                slope=np.cos(ph*4-j*0.32+i*0.28)                # fold facing the light (+) or away (-)
                v=0.55+0.30*slope*(0.4+amp)-0.05*(i/bw)+0.16*cn[j%64,i%16]+0.14*(grain[yi,xi]-0.5)
                disc=(i-3.5)**2+((j-7)*1.1)**2<=6.5 and 3<=j<=11
                c=q(WHITE5,v+0.1,xi,yi) if disc else q(RED5,v,xi,yi)
                if i==0 and not disc: c=RED5[1]                 # hem along the pole
                img[yi,xi]=c
            # loops tying the cloth to the pole every few rows
            if j%5==1:
                lx=int(round(x+1+wave*0.2)); 
                if 0<=lx<W: img[top+3+j,lx]=RED5[2]
        # frayed bottom edge: uneven threads
        for i in range(bw):
            j=bh-1; wave=1.5*np.sin(ph*4-j*0.32); lean=0.12*j
            xi=int(round(x+2+i+wave+lean)); ln=int(1+2*grain[(top+i)%H,(x+i*7)%W])
            for d in range(1,ln+1):
                if 0<=xi<W and top+3+j+d<H and (i+d)%2==0: img[top+3+j+d,xi]=RED5[1]
        # a few stones packed around the foot of the pole, like the fire ring
        yy_,xx_=np.mgrid[0:H,0:W]
        sr=np.random.default_rng(34)
        # five small stones at the foot of the pole (first variant, as chosen)
        for (ox,oy,rx,ry) in [(-3,0.5,2.2,1.5),(3,0.8,2.0,1.4),(0,2.0,2.4,1.5),(-1,-1.2,1.6,1.1),(2,-1.0,1.5,1.0)]:
            sx,sy=x+0.5+ox+sr.normal(0,0.3),y+0.5+oy+sr.normal(0,0.2)
            e=((xx_-sx)/rx)**2+((yy_-sy)/ry)**2
            img[(e<=1.9)&(e>1.0)&((yy_-sy)>-0.5)]=K
            m=e<=1.0; lit=(xx_-sx)+(yy_-sy)*1.3<-0.5
            img[m]=MG; img[m&lit]=L1; img[m&(e>0.55)&~lit&((yy_-sy)>0)]=DG; img[m&lit&(e<0.3)]=WH
        put(img,x,y-1,BAMBOO[2]); put(img,x+1,y-1,BAMBOO[1])            # pole stands between the stones
STONE=[hx(c) for c in ['#2b2927','#45423d','#625e56','#837e74','#a8a295']]
MOSS3=[hx(c) for c in ['#3f4632','#5b6447','#7d8660']]
class Lantern3:
    """Stone tōrō shaded per pixel: profile rows -> rounded light, ledges, cracks, moss, glowing chamber."""
    # (row from the ground up, half-width, part)
    PROFILE=[(0,7,'base'),(1,7,'base'),(2,6,'base'),(3,5,'base'),
             (4,2,'shaft'),(5,2,'shaft'),(6,2,'shaft'),(7,2,'shaft'),(8,2,'shaft'),(9,2,'shaft'),
             (10,6,'shelf'),(11,6,'shelf'),(12,5,'shelf'),
             (13,4,'box'),(14,4,'box'),(15,4,'box'),(16,4,'box'),(17,4,'box'),(18,4,'box'),
             (19,8,'roof'),(20,7,'roof'),(21,6,'roof'),(22,4,'roof'),(23,3,'roof'),(24,2,'roof'),
             (25,1,'jewel'),(26,2,'jewel'),(27,2,'jewel'),(28,1,'jewel')]
    # the game's size (Philip 2026-11-04: lanterns were twice the monk's height): about 18 rows, a little taller than him
    PROFILE_SMALL=[(0,5,'base'),(1,4,'base'),(2,3,'base'),
             (3,1,'shaft'),(4,1,'shaft'),(5,1,'shaft'),
             (6,4,'shelf'),(7,3,'shelf'),
             (8,3,'box'),(9,3,'box'),(10,3,'box'),(11,3,'box'),
             (12,5,'roof'),(13,4,'roof'),(14,3,'roof'),(15,2,'roof'),
             (16,1,'jewel'),(17,1,'jewel')]
    def __init__(s,x,y,rng,small=True):
        s.x,s.y,s.small=x,y,small
        # window rows, the row under the roof, glow height and radius, how far the roof corners reach
        s.win,s.under,s.gy,s.R,s.curl,s.k=((9,10),11,9.5,9,6,0.7) if small else ((14,17),17,15.5,13,9,1.0)
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]
        if s.small: return ((xx-s.x)/6)**2+((yy-s.y+8)/10)**2<=1
        return ((xx-s.x)/9)**2+((yy-s.y+13)/16)**2<=1
    def draw(s,img,t,L):
        t=t%L; H,W,_=img.shape; x,y=s.x,s.y; ph=2*np.pi*t/L
        g=np.random.default_rng(41).random((40,20)); bn=ndi.gaussian_filter(np.random.default_rng(42).normal(0,1,(40,20)),0.9); bn/=bn.std()
        mossn=ndi.gaussian_filter(np.random.default_rng(43).normal(0,1,(40,20)),1.3)
        fl=0.5+0.12*np.sin(ph*13+np.sin(ph*7))+0.05*np.sin(ph*29)       # calm candle flicker
        prof={r:(hw,part) for r,hw,part in (s.PROFILE_SMALL if s.small else s.PROFILE)}
        k_=s.k; w0,w1=s.win
        def q(pal,v,gx,gy):
            v=np.clip(v,0,0.999)*len(pal); i=int(v); return pal[min(len(pal)-1,i+(g[gy%40,gx%20]<(v-i)*0.9))]
        # cast shadow to the lower right (light comes from the upper left)
        sh=np.random.default_rng(44).normal(0,1,(12,24))
        for dy in range(-6,3):
            for dx in range(0,14):
                e=((dx-6*k_)/(8*k_))**2+((dy+1.5*k_)/(3.5*k_))**2+0.2*sh[(dy+6)%12,dx%24]
                if e<1: put(img,x+dx,y+dy,DG if e<0.7 else MG)
        # light falling onto the ground: a flat, diffuse gold-red pool around the foot
        yy_,xx_=np.mgrid[0:H,0:W]
        pd=np.hypot((xx_-x)/(15*k_),(yy_-y-1)/(6.5*k_))
        pa=np.clip(1-pd,0,1)**1.4*(0.40+0.08*fl)
        pool=np.array([250,150,64],float)
        sel=pa>0.01
        img[sel]=np.clip(img[sel]*(1-pa[sel,None])+pool*pa[sel,None],0,255).astype(np.uint8)
        for r,(hw,part) in prof.items():
            yy=y-r
            above=prof.get(r+1,(0,''))[0]; below=prof.get(r-1,(0,''))[0]
            for i in range(-hw,hw+1):
                xx=x+i; u=i/max(hw,1)
                gx,gy=i+10,r
                v=0.62-0.32*u-0.10*u*u+0.07*bn[gy%40,gx%20]             # rounded, lit from the left
                if abs(i)>above: v+=0.16                                 # top surface of a ledge
                if abs(i)>below: v-=0.22                                 # underside of a ledge
                if part=='roof':
                    v-=0.05
                    if r==s.under: v-=0.25                               # roof underside in shade...
                c=q(STONE,v,gx,gy)
                if part=='box' and abs(i)<=1 and w0<=r<=w1:              # window into the chamber
                    core=fl+0.25*(1-abs(i))-0.1*abs(r-(w0+w1)/2)
                    c=FL[7] if core>0.95 else FL[6] if core>0.7 else FL[5] if core>0.45 else FL[4]
                if part=='box' and abs(i)==2 and w0<=r<=w1: c=STONE[0]   # window reveal
                # cracks and weathering
                if (part in('base','shaft','roof')) and g[(gy*3)%40,(gx*7)%20]<0.06: c=STONE[0]
                # moss on the shaded side and on ledge tops
                if (u>0.25 or abs(i)>above) and mossn[gy%40,gx%20]>0.55 and part!='box':
                    c=MOSS3[2] if v>0.55 else MOSS3[1] if v>0.35 else MOSS3[0]
                put(img,xx,yy,c)
        # roof corners curl upward (warabite)
        cr=s.curl; ry=(12 if s.small else 19)
        put(img,x-cr,y-ry-1,STONE[3]); put(img,x-cr,y-ry-2,STONE[4]); put(img,x+cr,y-ry-1,STONE[1]); put(img,x+cr,y-ry-2,STONE[2])
        # glow: warm light from the chamber tints everything around it, fading out, breathing with the flame
        cx,cy=x,y-s.gy; R=s.R
        yy_,xx_=np.mgrid[0:H,0:W]
        d=np.hypot(xx_-cx,(yy_-cy)*1.1)/R
        a=np.clip(1-d,0,1)**2*(0.30+0.08*fl)
        warm=np.array([246,176,82],float)
        sel=a>0.01
        img[sel]=np.clip(img[sel]*(1-a[sel,None])+warm*a[sel,None],0,255).astype(np.uint8)
        # a little moss tuft at the foot
        for (dx,dy) in ([(3,1),(4,0),(-4,1)] if s.small else [(5,1),(6,0),(-6,1)]): put(img,x+dx,y+dy,MOSS3[1])
WOOD=[hx(c) for c in ['#2e2420','#4a3a31','#6a5545','#8c735c','#ab9277']]
TILE=[hx(c) for c in ['#24262a','#383b40','#52565c','#71767b','#959a9d']]
ROPE=[hx(c) for c in ['#7d6a46','#a68f5d','#c9b37c']]
class Shrine3:
    """Hokora shaded per pixel: stone steps, plank body with lattice doors, curved tiled roof,
    shimenawa with fluttering shide, moss and fallen cherry petals."""
    def __init__(s,x,y,rng): s.x,s.y=x,y
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x)/18)**2+((yy-s.y+13)/19)**2<=1
    def draw(s,img,t,L):
        t=t%L; H,W,_=img.shape; x,y=s.x,s.y; ph=2*np.pi*t/L
        G=np.random.default_rng(51).random((64,64))
        BN=ndi.gaussian_filter(np.random.default_rng(52).normal(0,1,(64,64)),0.9,mode='wrap'); BN/=BN.std()
        MN=ndi.gaussian_filter(np.random.default_rng(53).normal(0,1,(64,64)),1.4,mode='wrap')
        def q(pal,v,i,j):
            v=np.clip(v,0,0.999)*len(pal); k=int(v); return pal[min(len(pal)-1,k+(G[j%64,i%64]<(v-k)*0.9))]
        # cast shadow to the lower right
        for j in range(-14,3):
            for i in range(0,22):
                e=((i-9)/12)**2+((j+5)/7)**2+0.2*BN[(j+20)%64,i%64]
                if e<1: put(img,x+i,y+j,DG if e<0.7 else MG)
        # --- stone steps (two), wobbly outline, top faces light, fronts darker
        for (top,bot,hw) in [(-2,0,13),(-4,-2,10)]:
            for j in range(top,bot+1):
                w=hw+int(round(0.6*BN[(j+30)%64,5]))
                for i in range(-w,w+1):
                    u=i/w; v=0.58-0.25*u+0.06*BN[(j+40)%64,(i+32)%64]
                    v+=0.2 if j==top else -0.08
                    c=q(STONE,v,i+32,j+40)
                    if G[(j*5)%64,(i*3+7)%64]<0.05: c=STONE[0]
                    if MN[(j+40)%64,(i+32)%64]>0.6 and u>-0.2: c=MOSS3[1] if j==top else MOSS3[0]
                    put(img,x+i,y+j,c)
        # --- body: planks with grain, lit left, roof shadow on the top rows
        bx0,bx1,by0,by1=-8,8,-15,-5
        for j in range(by0,by1+1):
            for i in range(bx0,bx1+1):
                u=i/8; v=0.66-0.30*u+0.05*BN[(j+50)%64,(i*2+20)%64]
                v+=0.06*np.sin((j+i*0.15)*1.7+ (i//3)*2.1)              # wood grain along each plank
                if (i-bx0)%3==0: v-=0.16                                   # plank joints
                if j<=by0+2: v-=0.22                                       # shadow under the eaves
                c=q(WOOD,v,i+20,j+50)
                put(img,x+i,y+j,c)
        # lattice doors with darkness behind, frame and two little metal fittings
        for j in range(-13,-5):
            for i in range(-5,6):
                frame=(abs(i)==5) or j==-13 or i==0
                lat=((i+5)%2==0) or ((j+13)%3==0)
                if frame: c=q(WOOD,0.30-0.1*(i>0),i+30,j+30)
                elif lat: c=q(WOOD,0.55-0.25*(i/5)+0.05*BN[j%64,i%64],i+40,j+40)
                else: c=K if (i+j)%3 else WOOD[0]
                put(img,x+i,y+j,c)
        for (i,j) in [(-2,-9),(2,-9)]: put(img,x+i,y+j,hx('#c2a35a')); put(img,x+i,y+j+1,hx('#8a7340'))
        # --- roof: curved (sags in the middle, eaves sweep up), tile rows, ridge with end caps
        rows=list(range(-16,-27,-1))
        for k,j in enumerate(rows):
            f=k/len(rows)
            hw=int(round(17*(1-f**1.35)**0.8+1))                            # smooth, steepening toward the ridge
            for i in range(-hw,hw+1):
                lift=int(round(0.012*i*i*(k<3)))                            # upswept eave ends
                yy=y+j-lift
                u=i/max(hw,1)
                v=0.50-0.30*u+0.18*f+0.05*BN[(j+60)%64,(i+32)%64]        # upper courses face the sky -> lighter
                if k%2==0: v+=0.14                                         # tile course catches light
                if (i+k)%3==0 and k%2==1: v-=0.12                          # tile joints
                if k==0: v-=0.18                                            # eave underside edge
                c=q(TILE,v,i+32,j+60)
                if MN[(j+60)%64,(i+20)%64]>0.65: c=MOSS3[2] if v>0.5 else MOSS3[1]
                put(img,x+i,yy,c)
        for i in range(-6,7):                                               # ridge
            put(img,x+i,y-27,q(TILE,0.75-0.25*(i/6),i+32,5)); put(img,x+i,y-28,q(TILE,0.55-0.25*(i/6),i+32,6))
        for (i,v) in [(-7,0.7),(7,0.35)]:                                   # ridge end caps
            put(img,x+i,y-28,q(TILE,v,i+32,7)); put(img,x+i,y-29,q(TILE,v+0.1,i+32,8))
        # cherry petals that have fallen on the roof
        for k in range(9):
            i=int(G[k,3]*24-12); j=-17-int(G[k,9]*9)
            put(img,x+i,y+j,PK[3] if G[k,11]<0.5 else PK[4])
        # --- shimenawa: twisted rope sagging across the front, shide paper zigzags fluttering
        for i in range(-9,10):
            j=-15+int(round(1.2*np.cos(i*np.pi/19)))
            put(img,x+i,y+j,ROPE[(i%3)]); put(img,x+i,y+j+1,ROPE[0] if i%3 else ROPE[1])
        for k,i0 in enumerate((-6,0,6)):
            sw=np.sin(ph*5+k*2.1)
            for d in range(4):
                zx=x+i0+(1 if d%2 else 0)+int(round(sw*d*0.5)); zy=y-13+d
                put(img,zx,zy,WH if d%2==0 else L1); put(img,zx+1,zy,L1 if d%2==0 else MG)
class ShrineVariant:
    """Same detail language as Shrine3, four basic forms: 'hip','gable','nagare','stone'."""
    def __init__(s,x,y,kind): s.x,s.y,s.kind=x,y,kind
    def draw(s,img,t,L):
        t=t%L; H,W,_=img.shape; x,y=s.x,s.y; ph=2*np.pi*t/L; kind=s.kind
        G=np.random.default_rng(61).random((64,64))
        BN=ndi.gaussian_filter(np.random.default_rng(62).normal(0,1,(64,64)),0.9,mode='wrap'); BN/=BN.std()
        MN=ndi.gaussian_filter(np.random.default_rng(63).normal(0,1,(64,64)),1.4,mode='wrap')
        yy,xx=np.mgrid[0:H,0:W]
        def q(pal,v,i,j):
            v=np.clip(v,0,0.999)*len(pal); k=int(v); return pal[min(len(pal)-1,k+(G[j%64,i%64]<(v-k)*0.9))]
        def shade_fill(mask,pal,base,grad,cx,extra=None,moss=True):
            for (j,i) in zip(*np.where(mask)):
                u=(i-cx)/8.0; v=base-grad*u+0.05*BN[j%64,i%64]
                if extra is not None: v+=extra(i,j)
                c=q(pal,v,i,j)
                if moss and MN[j%64,i%64]>0.7: c=MOSS3[1] if v>0.45 else MOSS3[0]
                img[j,i]=c
        # shadow
        for j in range(-16,3):
            for i in range(0,20):
                e=((i-8)/11)**2+((j+5)/7)**2+0.2*BN[(j+20)%64,i%64]
                if e<1: put(img,x+i,y+j,DG if e<0.7 else MG)
        # steps (shared)
        steps=poly(H,W,[(x-11,y),(x+11,y),(x+10,y-2),(x-10,y-2)])|poly(H,W,[(x-8,y-2),(x+8,y-2),(x+7,y-4),(x-7,y-4)])
        shade_fill(steps,STONE,0.6,0.25,x,lambda i,j:0.15 if j in (y-2,y-4) else 0)
        def doors(x0,y0,y1,hw):
            for j in range(y0,y1):
                for i in range(-hw,hw+1):
                    frame=abs(i)==hw or j==y0 or i==0
                    lat=((i+hw)%2==0) or ((j-y0)%3==0)
                    c=q(WOOD,0.30-0.1*(i>0),i+30,j) if frame else q(WOOD,0.55-0.25*(i/hw),i+40,j) if lat else (K if (i+j)%3 else WOOD[0])
                    put(img,x0+i,j,c)
        def rope(y0,hw):
            for i in range(-hw,hw+1):
                j=y0+int(round(1.0*np.cos(i*np.pi/(2*hw+1))))
                put(img,x+i,j,ROPE[i%3]); put(img,x+i,j+1,ROPE[0] if i%3 else ROPE[1])
            for k,i0 in enumerate((-hw+3,0,hw-3)):
                sw=np.sin(ph*5+k*2.1)
                for d in range(4):
                    zx=x+i0+(1 if d%2 else 0)+int(round(sw*d*0.5)); zy=y0+2+d
                    put(img,zx,zy,WH if d%2==0 else L1); put(img,zx+1,zy,L1 if d%2==0 else MG)
        def petals(cx,cy,w,h,n=7):
            for k in range(n): put(img,cx+int(G[k,3]*w-w/2),cy-int(G[k,9]*h),PK[3] if G[k,11]<0.5 else PK[4])
        if kind=='stone':
            body=poly(H,W,[(x-6,y-4),(x+6,y-4),(x+6,y-14),(x-6,y-14)])
            shade_fill(body,STONE,0.62,0.3,x)
            niche=poly(H,W,[(x-3,y-5),(x+3,y-5),(x+3,y-11),(x,y-13),(x-3,y-11)])
            img[niche]=K
            for (i,j,c) in [(0,-8,STONE[3]),(0,-7,STONE[2]),(-1,-6,STONE[2]),(0,-6,STONE[3]),(1,-6,STONE[1]),(0,-9,STONE[4])]:
                put(img,x+i,y+j,c)                                           # tiny jizō figure
            put(img,x-1,y-5,hx('#9a1f24')); put(img,x+1,y-5,hx('#9a1f24'))  # red bib
            slab=poly(H,W,[(x-11,y-14),(x+11,y-14),(x+9,y-18),(x-9,y-18)])
            shade_fill(slab,STONE,0.55,0.28,x,lambda i,j:0.2 if j<=y-17 else (-0.2 if j==y-14 else 0))
            cap=poly(H,W,[(x-4,y-18),(x+4,y-18),(x+2,y-21),(x-2,y-21)])
            shade_fill(cap,STONE,0.6,0.3,x)
            put(img,x,y-22,STONE[3]); put(img,x,y-23,STONE[4])
            petals(x,y-15,18,3,5)
            return
        # timber body (hip / gable / nagare)
        body=poly(H,W,[(x-7,y-4),(x+7,y-4),(x+7,y-14),(x-7,y-14)])
        shade_fill(body,WOOD,0.66,0.3,x,lambda i,j:(-0.16 if (i-x+7)%3==0 else 0)-(0.22 if j<=y-12 else 0)+0.06*np.sin((j+i*0.15)*1.7),moss=False)
        doors(x,y-12,y-4,4)
        for i in (-2,2): put(img,x+i,y-8,hx('#c2a35a'))
        if kind=='hip':
            for k,j in enumerate(range(y-15,y-26,-1)):
                f=k/11; hw=int(round(16*(1-f**1.35)**0.8+1))
                for i in range(-hw,hw+1):
                    lift=int(round(0.012*i*i*(k<3)))
                    v=0.5-0.3*i/max(hw,1)+0.18*f+(0.14 if k%2==0 else 0)-(0.18 if k==0 else 0)+0.05*BN[j%64,(i+32)%64]
                    put(img,x+i,j-lift,q(TILE,v,i+32,j))
            for i in range(-5,6): put(img,x+i,y-26,q(TILE,0.75-0.25*i/5,i+32,5))
            petals(x,y-17,22,8)
            rope(y-14,8)
        elif kind=='gable':
            A=(x,y-29); FLp=(x-12,y-14); FRp=(x+12,y-14); Ab=(x+3,y-33)
            BLp=(x-9,y-26); BRp=(x+15,y-25)
            left=poly(H,W,[A,Ab,BLp,FLp]); right=poly(H,W,[A,Ab,BRp,FRp]); gable=poly(H,W,[A,FLp,FRp])
            shade_fill(left,TILE,0.78,0.0,x,lambda i,j:(0.12 if (j-y)%2==0 else 0),moss=True)
            shade_fill(right,TILE,0.35,0.0,x,lambda i,j:(0.10 if (j-y)%2==0 else 0),moss=True)
            shade_fill(gable,WOOD,0.55,0.25,x,lambda i,j:-0.12 if (j-y)%3==0 else 0,moss=False)
            # bargeboards: light wooden boards along both gable edges, with the tips flaring out
            for k in range(16):
                for (p1,lit) in ((FLp,True),(FRp,False)):
                    px=int(round(A[0]+(p1[0]-A[0])*k/15)); py=int(round(A[1]+(p1[1]-A[1])*k/15))
                    put(img,px,py,WOOD[4] if lit else WOOD[2]); put(img,px,py+1,WOOD[3] if lit else WOOD[1])
            put(img,x-13,y-13,WOOD[4]); put(img,x+13,y-13,WOOD[2])
            for k in range(3): put(img,x,y-28+k,WOOD[3])                    # hanging ornament under the apex
            petals(x-3,y-18,10,8,6)
            rope(y-14,8)
        elif kind=='nagare':
            # ridge high at the back, the front slope runs long and low over the steps
            back=poly(H,W,[(x-12,y-26),(x+12,y-26),(x+13,y-23),(x-13,y-23)])
            front=poly(H,W,[(x-13,y-23),(x+13,y-23),(x+15,y-6),(x-15,y-6)])
            shade_fill(back,TILE,0.45,0.3,x)
            def fr(i,j):
                f=(j-(y-23))/17
                return 0.25-0.25*f+(0.12 if (j-y)%2==0 else 0)+(-0.25 if j>=y-7 else 0)
            shade_fill(front,TILE,0.5,0.3,x,fr)
            # eave edge sweeps up at both ends
            for i in range(-15,16):
                lift=int(round(0.02*i*i)); put(img,x+i,y-6-lift,q(TILE,0.25-0.2*i/15,i+32,3))
            for i in range(-12,13): put(img,x+i,y-27,q(TILE,0.8-0.3*i/12,i+32,4))
            for (i,v) in ((-13,0.8),(13,0.4)): put(img,x+i,y-28,q(TILE,v,i+32,6))
            petals(x,y-10,24,12,9)
            # doors peek out under the long eave
            rope(y-6,8)
FLc=[hx(c) for c in ['#5a2a14','#9a4a1c','#d9822e','#f2b44a','#fde7a0']]
class ShrineB:
    """Gable-front hokora as a real volume: every part shares one depth direction (back = up-right)."""
    D=np.array([0,-4])                                     # depth runs straight up the screen, like the rest of the scene
    def __init__(s,x,y): s.x,s.y=x,y
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x-2)/18)**2+((yy-s.y+15)/21)**2<=1
    def draw(s,img,t,L):
        t=t%L; H,W,_=img.shape; x,y=s.x,s.y; ph=2*np.pi*t/L; D=s.D
        G=np.random.default_rng(71).random((64,64))
        BN=ndi.gaussian_filter(np.random.default_rng(72).normal(0,1,(64,64)),0.9,mode='wrap'); BN/=BN.std()
        MN=ndi.gaussian_filter(np.random.default_rng(73).normal(0,1,(64,64)),1.4,mode='wrap')
        def q(pal,v,i,j):
            v=np.clip(v,0,0.999)*len(pal); k=int(v); return pal[min(len(pal)-1,k+(G[j%64,i%64]<(v-k)*0.9))]
        def fill(mask,pal,vfun,moss=0.0):
            for (j,i) in zip(*np.where(mask)):
                v=vfun(i,j)+0.05*BN[j%64,i%64]; c=q(pal,v,i,j)
                if moss and MN[j%64,i%64]>moss: c=MOSS3[2] if v>0.55 else MOSS3[1] if v>0.35 else MOSS3[0]
                img[j,i]=c
        P=lambda *pts:poly(H,W,[tuple(np.array(p,float)) for p in pts])
        def box(x0,x1,ytop,ybot,dep,pal,front_v,top_v,side_v,moss=0.0):
            """front face + top face + right side face of a block (dep = how deep, in D steps)"""
            d=D*dep
            top=P((x0,ytop),(x1,ytop),(x1+d[0],ytop+d[1]),(x0+d[0],ytop+d[1]))
            side=P((x1,ytop),(x1+d[0],ytop+d[1]),(x1+d[0],ybot+d[1]),(x1,ybot))
            front=P((x0,ytop),(x1,ytop),(x1,ybot),(x0,ybot))
            fill(side,pal,lambda i,j:side_v,moss); fill(top,pal,lambda i,j:top_v-0.1*(i-x0)/(x1-x0),moss)
            fill(front,pal,lambda i,j:front_v-0.18*(i-x0)/(x1-x0),moss)
        # cast shadow to the lower right
        for j in range(-20,3):
            for i in range(0,24):
                e=((i-10)/13)**2+((j+7)/8)**2+0.2*BN[(j+20)%64,i%64]
                if e<1: put(img,x+i,y+j,DG if e<0.7 else MG)
        # paved stone platform the building stands on: reaches back under and behind the shrine
        slab=P((x-15,y-24),(x+15,y-24),(x+16,y-1),(x-16,y-1))
        disk=np.hypot(*np.mgrid[-3:4,-3:4])<=3.0
        slab=ndi.binary_opening(slab,structure=disk)            # rounded corners
        face=slab&(np.indices((H,W))[0]>=y-3)                     # bottom rows = front edge face
        slab&=~face
        def pav(i,j):
            n=BN[(j*2)%64,(i*2+11)%64]
            return 0.70-0.2*(i-x)/16+(-0.30 if abs(n)<0.18 else 0)+0.06*((j-y+24)/21)
        fill(slab,STONE,pav,moss=0.78)
        fill(face,STONE,lambda i,j:0.30-0.15*(i-x)/16,moss=0.85)
        # a single step up onto the platform, in front of the doors
        box(x-5,x+5,y-1,y+1,0.3,STONE,0.42,0.80,0.25,moss=0.85)
        # timber body: front wall, right side wall going back, top hidden by the roof
        bx0,bx1,bt,bb=-7,7,-19,-7
        d=D*1.3
        front=P((x+bx0,y+bt),(x+bx1,y+bt),(x+bx1,y+bb),(x+bx0,y+bb))
        fill(front,WOOD,lambda i,j:0.52-0.26*(i-x)/7-(0.16 if (i-x-bx0)%3==0 else 0)-(0.25 if j<=y+bt+2 else 0)+0.06*np.sin((j+i*0.15)*1.7)-0.14*max(0,(j-(y+bb-4)))/4-0.10*(G[j%64,(i*5)%64]<0.25))
        # corner posts (light, rounded) and a sill beam
        for (px,lit) in ((x+bx0,True),(x+bx1,False)):
            for j in range(y+bt,y+bb+1):
                put(img,px,j,q(WOOD,0.62 if lit else 0.30,px,j)); put(img,px+(1 if lit else -1),j,q(WOOD,0.48 if lit else 0.22,px+1,j))
        for i in range(bx0,bx1+1): put(img,x+i,y+bb,q(WOOD,0.4-0.2*i/7,i,bb))
        # lattice doors
        for j in range(y-16,y-7):
            for i in range(-4,5):
                frame=abs(i)==4 or j==y-16 or i==0
                lat=((i+4)%2==0) or ((j-y+16)%3==0)
                c=q(WOOD,0.26-0.1*(i>0),i+30,j) if frame else q(WOOD,0.46-0.22*(i/4)-0.08*(G[j%64,(i*7)%64]<0.3),i+40,j) if lat else (K if (i+j)%3 else WOOD[0])
                if c is K or c is WOOD[0]:                       # warm light inside, strongest low in the middle
                    w=np.exp(-((i/3.0)**2+((j-(y-9))/3.0)**2))*(0.75+0.25*np.sin(ph*13+i+np.sin(ph*7)))
                    c=FLc[2] if w>0.6 else FLc[1] if w>0.35 else FLc[0] if w>0.15 else c
                put(img,x+i,j,c)
        put(img,x-2,y-11,hx('#c2a35a')); put(img,x+2,y-11,hx('#c2a35a'))
        # small wooden veranda in front of the doors
        ver=P((x-8,y-7),(x+8,y-7),(x+9,y-6),(x-9,y-6))
        fill(ver,WOOD,lambda i,j:0.55-0.28*(i-x)/9-(0.15 if (i-x)%3==0 else 0)-0.08*(G[j%64,(i*3)%64]<0.3))
        for k,cxo in enumerate((-6,6)):                        # two candles on the veranda
            put(img,x+cxo,y-7,hx('#d9d0bd')); put(img,x+cxo,y-8,hx('#efe8d8'))
            f=np.sin(ph*17+k*2.3)+0.5*np.sin(ph*29+k)
            put(img,x+cxo,y-9,FLc[4] if f>-0.4 else FLc[3])
            if f>0.3: put(img,x+cxo,y-10,FLc[2])
        # roof: front gable, two slopes running back along D, overhanging eaves with fascia
        A=np.array([x,y-29]); FLp=np.array([x-12,y-17]); FRp=np.array([x+12,y-17]); dd=D*2.0
        Ab,BLp,BRp=A+dd,FLp+dd,FRp+dd
        # dark underside visible under the right eave (between eave and side wall)
        for i in range(-12,13): put(img,x+i,y-16,WOOD[0] if abs(i)>7 else WOOD[1])   # shadow under the eave line
        right=P(A,Ab,BRp,FRp); left=P(A,Ab,BLp,FLp)
        fill(right,TILE,lambda i,j:0.40+(0.12 if (j-y)%2==0 else 0)-0.015*(i-x)+0.10*((x+12-i)/12),moss=0.72)
        fill(left,TILE,lambda i,j:0.72+(0.10 if (j-y)%2==0 else 0)+0.10*((i-x+12)/12),moss=0.72)
        gable=P(A,FLp,FRp)
        fill(gable,WOOD,lambda i,j:0.55-0.25*(i-x)/12-(0.12 if (j-y)%3==0 else 0)-(0.2 if j>y-18 else 0))
        # fascia: thickness along the bottom of the right slope's front and the eave line
        for k in range(13):                                # eave edges along both outer sides, seen from above
            for (p0,p1,c) in ((FLp,BLp,TILE[2]),(FRp,BRp,TILE[0])):
                p=p0+(p1-p0)*k/12; put(img,int(round(p[0]))+(-1 if c is TILE[2] else 1),int(round(p[1])),c)
        # bargeboards with flared tips
        for k in range(18):
            for (p1,lit) in ((FLp,True),(FRp,False)):
                p=A+(p1-A)*k/17; px,py=int(round(p[0])),int(round(p[1]))
                put(img,px,py,WOOD[4] if lit else WOOD[2]); put(img,px,py+1,WOOD[3] if lit else WOOD[1])
        put(img,x-13,y-16,WOOD[4]); put(img,x-14,y-16,WOOD[3]); put(img,x+13,y-16,WOOD[2]); put(img,x+14,y-16,WOOD[1])
        for k in range(3): put(img,x,y-28+k,WOOD[3]); put(img,x,y-25,hx('#c2a35a'))   # gegyo ornament
        # ridge running back from the apex
        for k in range(11):
            p=A+(Ab-A)*k/10; put(img,int(round(p[0])),int(round(p[1]))-1,TILE[4] if k<6 else TILE[3])
        # fallen cherry petals on the lit slope
        for k in range(8):
            u,v=G[k,3],G[k,9]; p=FLp+(A-FLp)*u*0.9+dd*v*0.9
            put(img,int(round(p[0])),int(round(p[1])),PK[3] if G[k,11]<0.5 else PK[4])
        # shimenawa across the front with fluttering shide
        for i in range(-8,9):
            j=y-18+int(round(1.0*np.cos(i*np.pi/17)))
            put(img,x+i,j,ROPE[i%3]); put(img,x+i,j+1,ROPE[0] if i%3 else ROPE[1])
        for k,i0 in enumerate((-5,0,5)):
            sw=np.sin(ph*5+k*2.1)
            for dlt in range(4):
                zx=x+i0+(1 if dlt%2 else 0)+int(round(sw*dlt*0.5)); zy=y-16+dlt
                put(img,zx,zy,WH if dlt%2==0 else L1); put(img,zx+1,zy,L1 if dlt%2==0 else MG)
