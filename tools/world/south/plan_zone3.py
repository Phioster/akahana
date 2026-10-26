import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy.interpolate import splprep, splev
W,H,S=900,600,2
img=Image.new('RGB',(W*S,H*S),(92,112,78)); d=ImageDraw.Draw(img)
f=ImageFont.truetype('/system/fonts/Roboto-Regular.ttf',26)
def curve(pts,n=300):
    tck,_=splprep(np.array(pts,float).T,s=0,k=min(3,len(pts)-1)); return np.array(splev(np.linspace(0,1,n),tck)).T
def P(c,w,col): d.line([(x*S,y*S) for x,y in c],fill=col,width=int(w*S),joint='curve')
def meander(pts, amp, seed, n=300):
    """A stream that wanders: the base curve plus a slow sideways swing that grows and shrinks."""
    c = curve(pts, n)
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, n)
    sw = sum(rng.uniform(0.4, 1) * np.sin(t * f * 2 * np.pi + rng.uniform(0, 6)) for f in (2.3, 4.1, 7.7))
    sw *= amp * (0.4 + 0.6 * np.abs(np.sin(t * 3.1 + seed)))
    d = np.gradient(c, axis=0)
    d /= np.hypot(d[:, :1], d[:, 1:]) + 1e-9
    return c + np.stack([-d[:, 1], d[:, 0]], 1) * sw[:, None] * np.minimum(1, np.minimum(t, 1 - t) * 8)[:, None]
CA = meander([(14,40),(90,95),(150,190),(140,300),(220,380),(330,470),(410,610)], 16, 3)
CQ = meander([(566,128),(540,200),(500,290),(440,380),tuple(CA[205])], 10, 5)     # from the spring
CB = meander([(886,300),(800,350),(720,420),(640,500),(560,560),(520,612)], 12, 8)
CC = meander([(14,360),(70,390),tuple(CA[150])], 2.5, 9, 120)                         # a short side brook
C = {'A': CA, 'Q': CQ, 'B': CB, 'C': CC}
widths = {'A': 9, 'Q': 6, 'B': 8, 'C': 5}
streams = {k: (None, w) for k, w in widths.items()}
for k,(p,w) in streams.items(): P(C[k],w+6,(70,96,62))
for k,(p,w) in streams.items(): P(C[k],w,(96,128,150))
d.ellipse([554*S,116*S,580*S,136*S],fill=(96,128,150),outline=(70,96,62),width=8)   # the spring: a small pool
for (x,y) in [(552,122),(580,126),(560,138),(575,114)]: d.ellipse([(x-4)*S,(y-3)*S,(x+4)*S,(y+3)*S],fill=(150,150,145))
d.text((586*S,100*S),'Quelle',fill=(235,235,225),font=f)
for k,c in C.items():
    for i in range(40,len(c)-20,65):
        dx,dy=c[i+3]-c[i-3]; n=np.hypot(dx,dy); dx,dy=dx/n,dy/n; x,y=c[i]
        d.polygon([((x+9*dx)*S,(y+9*dy)*S),((x-5*dx-5*dy)*S,(y-5*dy+5*dx)*S),((x-5*dx+5*dy)*S,(y-5*dy-5*dx)*S)],fill=(225,235,242))
d.ellipse([330*S,575*S,640*S,700*S],fill=(96,128,150))
d.text((440*S,580*S),'zum See',fill=(230,235,240),font=f)
trails={'west':[(300,0),(270,90),(240,200),(270,300),(230,420),(260,520),(330,610)],
        'ost':[(650,0),(690,110),(720,220),(770,320),(800,420),(770,520),(730,610)],
        'mitte':[(520,0),(560,60),(612,120),(616,200),(570,320),(505,420),(472,520),(468,575)],
        'q1':[(255,250),(330,262),(420,250),(520,236),(592,214)],
        'weide':[(268,150),(200,156),(130,168),(62,160)],
        'q3':[(250,490),(330,505),(400,515),(478,512)]}
T={k:curve(p) for k,p in trails.items()}
for k,c in T.items(): P(c,4 if k in ('west','ost') else 3,(205,190,160))
def M(x,y,r,c,n):
    d.ellipse([(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S],fill=c,outline=(30,30,30),width=2)
    if n: d.text((x*S-8,y*S-15),n,fill=(20,20,20),font=f)
kinds=iter('BBRTT')
for tk,t in T.items():
    for sk,s in C.items():
        dd=np.hypot(t[:,None,0]-s[None,:,0],t[:,None,1]-s[None,:,1]); i,j=np.unravel_index(dd.argmin(),dd.shape)
        if dd[i,j]<4:
            x,y=t[i]; k=next(kinds); M(x,y,11,(230,200,140) if k=='B' else (200,170,120) if k=='R' else (170,170,165),k); print(tk,sk,k,int(x),int(y))
M(592,110,8,(255,210,120),'L')
for (x,y) in [(110,200),(470,140),(330,420),(820,230),(620,400),(150,520)]: M(x,y,7,(255,240,140),'G')
def on(k,i,off):
    c = C[k]; i = min(i, len(c) - 3); x, y = c[i]; dx, dy = c[i+2] - c[i-2]; n = np.hypot(dx, dy); return x - dy/n*off, y + dx/n*off
for k,idx in {'A':(30,90,170,250),'Q':(60,170,250),'B':(50,140,230),'C':(40,90)}.items():
    for i in idx: M(*on(k,i,12),6,(150,170,90),'')
for k,i in [('A',120),('Q',120),('B',90)]: M(*on(k,i,-14),7,(120,150,90),'F')
for (x,y) in [(400,90),(80,460),(860,470),(700,580)]: M(x,y,7,(130,130,125),'S')
for k,i in [('A',60),('B',200)]: M(*on(k,i,-19),13,(110,140,100),'W')
for x0 in (0,W-14): d.rectangle([x0*S,0,(x0+14)*S,H*S],fill=(40,60,50))
img.save(sys.argv[1])
