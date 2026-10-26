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
A=[(14,70),(120,110),(230,190),(330,300),(420,420),(450,530),(460,610)]
B=[(886,50),(780,120),(700,230),(610,330),(540,450),(500,540),(480,610)]
CA,CB=curve(A),curve(B)
def at(c,y): i=np.abs(c[:,1]-y).argmin(); return tuple(c[i])
streams={'A':(A,9),'B':(B,10),
         'C':([(14,360),(110,380),(220,420),(330,455),at(CA,480)],6),
         'D':([(886,330),(820,380),(740,430),(620,470),at(CB,495)],6)}
C={k:curve(p) for k,(p,w) in streams.items()}
for k,(p,w) in streams.items(): P(C[k],w+6,(70,96,62))
for k,(p,w) in streams.items(): P(C[k],w,(96,128,150))
for k,c in C.items():
    for i in range(40,len(c)-20,65):
        dx,dy=c[i+3]-c[i-3]; n=np.hypot(dx,dy); dx,dy=dx/n,dy/n; x,y=c[i]
        d.polygon([((x+9*dx)*S,(y+9*dy)*S),((x-5*dx-5*dy)*S,(y-5*dy+5*dx)*S),((x-5*dx+5*dy)*S,(y-5*dy-5*dx)*S)],fill=(225,235,242))
d.ellipse([340*S,570*S,600*S,690*S],fill=(96,128,150))
d.text((428*S,576*S),'zum See',fill=(230,235,240),font=f)
trails={'west':[(300,0),(250,120),(170,250),(150,380),(200,500),(260,600)],
        'ost':[(650,0),(720,140),(780,280),(770,420),(700,520),(640,600)],
        'mitte':[(470,0),(480,100),(470,220),(478,380),(470,500),(468,566)],
        'q1':[(474,320),(400,326),(300,336),(160,338)],
        'q2':[(474,250),(560,256),(660,268),(778,270)]}
T={k:curve(p) for k,p in trails.items()}
for k,c in T.items(): P(c,4 if k in ('west','ost') else 3,(205,190,160))
def M(x,y,r,c,n):
    d.ellipse([(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S],fill=c,outline=(30,30,30),width=2)
    if n: d.text((x*S-8,y*S-15),n,fill=(20,20,20),font=f)
kinds=iter('BTRBTRBTR')
for tk,t in T.items():
    for sk,s in C.items():
        dd=np.hypot(t[:,None,0]-s[None,:,0],t[:,None,1]-s[None,:,1]); i,j=np.unravel_index(dd.argmin(),dd.shape)
        if dd[i,j]<4:
            x,y=t[i]; k=next(kinds); M(x,y,11,(230,200,140) if k=='B' else (200,170,120) if k=='R' else (170,170,165),k); print(tk,sk,k,int(x),int(y))
M(195,230,8,(255,210,120),'L')
for (x,y) in [(110,200),(560,170),(330,400),(820,250),(600,420),(140,520)]: M(x,y,7,(255,240,140),'G')
def on(k,i,off): x,y=C[k][i]; dx,dy=C[k][i+2]-C[k][i-2]; n=np.hypot(dx,dy); return x-dy/n*off, y+dx/n*off
for k,idx in {'A':(30,100,200,260),'B':(40,120,190,250),'C':(50,180),'D':(60,200)}.items():
    for i in idx: M(*on(k,i,12),6,(150,170,90),'')
for k,i in [('A',150),('B',80),('D',120)]: M(*on(k,i,-14),7,(120,150,90),'F')
for (x,y) in [(380,90),(90,450),(860,470),(600,560)]: M(x,y,7,(130,130,125),'S')
for k,i in [('A',60),('B',220)]: M(*on(k,i,-18),13,(110,140,100),'W')
for x0 in (0,W-14): d.rectangle([x0*S,0,(x0+14)*S,H*S],fill=(40,60,50))
img.save(sys.argv[1])
