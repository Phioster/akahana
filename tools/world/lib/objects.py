# Camp + Japanese details, drawn pixel by pixel with a slight hand-made wobble.
# Light from the upper left like the rest of the scene. All motion closes after LOOP.
import numpy as np
from scipy import ndimage as ndi
from field6 import WH,L1,MG,DG,K
from tree import PK,BARK
from fire import FL
hx=lambda h:np.array([int(h[i:i+2],16) for i in (1,3,5)],np.uint8)
CANVAS=[hx(c) for c in ['#544a40','#857766','#b1a089','#d5c6ac','#eee4cf']]   # tent cloth, dark..lit
RED=[hx(c) for c in ['#5e1418','#9a1f24','#cf2a2e','#e8504a']]               # banner
MOSS=[hx('#5b6148'),hx('#7c8160')]
def put(img,x,y,c,mask=None):
    H,W,_=img.shape
    if 0<=x<W and 0<=y<H and (mask is None or not mask[y,x]): img[y,x]=c
class Tent:
    """Small A-frame tent seen from above at an angle; ridge runs left-right."""
    def __init__(s,x,y,rng): s.x,s.y=x,y; s.r=rng; s.n=rng.normal(0,0.6,40)
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x)/13)**2+((yy-s.y-2)/7.5)**2<=1
    def draw(s,img,t,L):
        x0,y0=s.x,s.y; ph=2*np.pi*t/L
        # ground shadow on the lee side
        for j in range(-2,9):
            for i in range(-11,15):
                if ((i-2)/13)**2+((j-4)/6)**2<=1 and (i+j)%2==0: put(img,x0+i,y0+j+2,DG)
        ridge=y0-7
        for i in range(-11,12):
            sag=0.9*np.sin(np.pi*(i+11)/22)                      # cloth sags between the poles
            flap=0.6*np.sin(ph*6+i*0.5)*(abs(i)>6)              # loose ends move in the wind
            top=int(round(ridge+sag+0.3*s.n[i+11]))
            bot=int(round(y0+0.4*s.n[i+20]+flap))
            for y in range(top,bot+1):
                f=(y-top)/max(1,bot-top)
                near=y>top+(bot-top)*0.45                       # front slope faces the camera
                c=CANVAS[3] if not near else CANVAS[2]
                if i>4 and near: c=CANVAS[1]                     # right end in shade
                if i<-6 and not near: c=CANVAS[4]
                if f>0.92: c=CANVAS[1]                           # hem
                put(img,x0+i,y,c)
            put(img,x0+i,top,CANVAS[4] if i<3 else CANVAS[2])   # lit ridge line
        # door: a dark, slightly open slit with a folded-back flap
        for y in range(ridge+3,y0+1):
            w=int((y-ridge-2)*0.35)
            for i in range(-w,w+1): put(img,x0+1+i,y,K if i<1 else DG)
            put(img,x0+2+w,y,CANVAS[4])
        # poles + guy lines (thin, curved a bit)
        for px in (-11,11):
            for y in range(ridge-2,ridge+1): put(img,x0+px,y,BARK[1])
        for k in range(6): put(img,x0-12-k,ridge+1+int(k*0.9),DG); put(img,x0+12+k,ridge+1+int(k*0.9),DG)
class Lantern:
    """Small stone tōrō: base, post, fire box with warm light, curved roof cap."""
    def __init__(s,x,y,rng): s.x,s.y=x,y; s.n=rng.normal(0,1,30)
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x)/5)**2+((yy-s.y+5)/8)**2<=1
    def draw(s,img,t,L):
        x,y=s.x,s.y; ph=2*np.pi*t/L
        rows=[ # (dy, half-width, kind)
            (0,3,'base'),(-1,3,'base'),(-2,2,'base'),(-3,1,'post'),(-4,1,'post'),(-5,1,'post'),
            (-6,3,'shelf'),(-7,2,'box'),(-8,2,'box'),(-9,2,'box'),(-10,4,'roof'),(-11,3,'roof'),(-12,1,'top'),(-13,0,'top')]
        for k,(dy,hw,kind) in enumerate(rows):
            wob=int(round(0.4*s.n[k]))
            for i in range(-hw,hw+1):
                c=L1 if i<0 else MG if i<hw else DG
                if kind=='roof': c=MG if i<0 else DG; c=L1 if (dy==-11 and i<0) else c
                if kind=='box' and abs(i)<=1 and dy in (-8,-9):
                    fl=0.5+0.5*np.sin(ph*13+np.sin(ph*7))      # candle flicker
                    c=FL[6] if (i==0 and fl>0.3) else FL[4] if i==0 else FL[3]
                put(img,x+i+wob*(kind=='roof'),y+dy,c)
        # roof tips curl up slightly
        put(img,x-5,y-11,MG); put(img,x+5,y-11,DG)
        # moss on the shaded side + soft glow on the ground in front
        put(img,x+2,y-1,MOSS[0]); put(img,x+3,y,MOSS[1]); put(img,x+2,y-6,MOSS[0])
        g=0.5+0.5*np.sin(ph*9)
        for (dx,dy) in [(-2,2),(1,2),(3,3),(-4,3),(0,4)]:
            if (dx+int(g*3))%2==0: put(img,x+dx,y+dy,FL[5])
class Shrine:
    """Tiny weathered wooden hokora with a swept roof, rope and paper streamers."""
    def __init__(s,x,y,rng): s.x,s.y=x,y; s.n=rng.normal(0,1,60)
    def footprint(s,H,W):
        yy,xx=np.mgrid[0:H,0:W]; return ((xx-s.x)/10)**2+((yy-s.y+6)/10)**2<=1
    def draw(s,img,t,L):
        x,y=s.x,s.y; ph=2*np.pi*t/L
        # stone plinth
        for j in range(0,3):
            for i in range(-8+j//2,9-j//2):
                put(img,x+i,y-j,L1 if i<-2 else MG if i<5 else DG)
        # body: dark timber, plank seams, doors with a light slit
        for j in range(3,11):
            for i in range(-5,6):
                c=BARK[2] if i<-1 else BARK[1] if i<4 else BARK[0]
                if i in (-3,2) and j%3!=0: c=BARK[0]            # plank seams (broken lines)
                put(img,x+i,y-j,c)
        for j in range(4,9): put(img,x,y-j,FL[3] if j in (6,7) else K)
        # roof: wide, sagging middle, upswept ends, mossy
        for j in range(11,16):
            hw=10-(j-11)*2
            for i in range(-hw,hw+1):
                curve=int(round(0.06*i*i*(j==11)))              # eaves sweep upward at the ends
                c=DG if i>2 else MG
                if j>=14: c=MG if i<0 else DG
                if i<-hw+3 and j==11: c=L1
                put(img,x+i,y-j-curve,c)
        for (dx,dy) in [(-6,13),(-3,14),(1,15),(4,13),(7,12)]: put(img,x+dx,y-dy,MOSS[int((dx+dy)%2)])
        # shimenawa rope with paper streamers that flutter
        for i in range(-6,7): put(img,x+i,y-10+int(0.5*np.cos(i*0.6)),L1)
        for k,dx in enumerate((-4,0,4)):
            sw=int(round(np.sin(ph*5+k*1.7)))
            for d in range(1,4): put(img,x+dx+(sw if d>1 else 0),y-10+d,WH)
class Banner:
    """Nobori: tall bamboo pole with a long red banner rippling in the wind."""
    def __init__(s,x,y,top,rng): s.x,s.y,s.top=x,y,top; s.n=rng.normal(0,1,80)
    def draw(s,img,t,L,occl=None):
        x,y,top=s.x,s.y,s.top; ph=2*np.pi*t/L
        # bamboo pole, slight bend, nodes every few px
        for yy in range(top-2,y+1):
            fx=x+0.04*(y-yy)*np.sin((y-yy)/30)               # gentle bow
            c=hx('#b8a77a') if (y-yy)%7 else hx('#7d6f4c')
            put(img,int(round(fx)),yy,c,occl); put(img,int(round(fx))+1,yy,hx('#8c7d55'),occl)
        # cross bar at the top and the banner hanging from it, flying to the right
        bw,bh=7,26
        for i in range(0,bw+2): put(img,x+1+i,top+int(0.3*np.sin(i)),hx('#8c7d55'),occl)
        for j in range(bh):
            wave=1.6*np.sin(ph*4-j*0.35)*(j/bh)                 # ripple travels down the cloth
            lean=0.10*j                                         # wind pushes the free end right
            for i in range(bw):
                xi=int(round(x+2+i+wave+lean))
                shade=np.sin(ph*4-j*0.35+i*0.25)                # folds catch the light
                c=RED[3] if shade>0.55 else RED[2] if shade>-0.2 else RED[1]
                if i==0 or i==bw-1: c=RED[1]
                # white circle motif near the top
                if 4<=j<=8 and (i-3)**2+(j-6)**2<=4: c=L1 if shade>-0.2 else MG
                put(img,xi,top+1+j,c,occl)
            if j==bh-1:                                         # ragged bottom edge
                for i in range(0,bw,2): put(img,int(round(x+2+i+wave+lean)),top+2+j,RED[0],occl)
