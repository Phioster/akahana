# Cherry tree seen from high up at an angle, built from organic curves and blobs.
import numpy as np
from scipy import ndimage as ndi
from field6 import WH,L1,MG,DG,K
hx=lambda h:np.array([int(h[i:i+2],16) for i in (1,3,5)],np.uint8)
PK=[hx(c) for c in ['#6e2f42','#9c4a62','#c87a90','#e6aab8','#f6d8de']]   # dark .. light blossom
BARK=[hx(c) for c in ['#241e1f','#3a3133','#57494b','#7a6a6a']]
B4=(np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])+0.5)/16
def bezier(p0,p1,p2,n):
    t=np.linspace(0,1,n)[:,None]
    return (1-t)**2*p0+2*(1-t)*t*p1+t**2*p2
def grow(rng,base,ang,length,width,depth,out):
    """Recursive curved branches; every segment bends a little (no straight lines)."""
    if depth==0 or length<4: out['tips'].append(base); return
    bend=rng.normal(0,0.35)
    mid=base+length*0.5*np.array([np.cos(ang+bend),np.sin(ang+bend)])
    end=base+length*np.array([np.cos(ang+bend*0.3),np.sin(ang+bend*0.3)])
    pts=bezier(base,mid,end,int(length*2))
    for k,p in enumerate(pts):
        w=width*(1-0.45*k/len(pts))
        out['strokes'].append((p[0],p[1],w,depth))
    n=2 if rng.random()<0.7 else 3
    for i in range(n):
        # spread wide and sideways: a cherry crown is broader than tall
        a=ang+(i-(n-1)/2)*1.0+rng.uniform(-0.35,0.35)
        a=a+0.25*np.sign(np.cos(a))*(depth<5)
        grow(rng,end,a,length*rng.uniform(0.72,0.9),width*0.66,depth-1,out)
def build(W,H,cx,by,rng):
    """Returns colour image layer (H,W,3), mask, shadow mask and tip list."""
    out={'strokes':[],'tips':[]}
    yy,xx=np.mgrid[0:H,0:W]
    # trunk rises "up" the screen (towards the camera), leaning slightly, then splits
    grow(rng,np.array([cx,by],float),-np.pi/2+0.1,20,6.5,6,out)
    wood=np.zeros((H,W)); shade=np.zeros((H,W))
    for x,y,w,_ in out['strokes']:
        r=max(0.8,w)
        m=(xx-x)**2+(yy-y)**2<=r*r
        wood[m]=1
        # light from the upper left across each limb
        shade[m]=np.maximum(shade[m],np.clip(0.5-((xx[m]-x)*0.7+(yy[m]-y)*0.4)/(r+0.5)*0.5,0,1))
    # roots flare into the ground
    for a in np.linspace(-0.4,np.pi+0.4,6)+rng.normal(0,0.15,6):
        L=rng.uniform(6,11); p0=np.array([cx,by]); p2=p0+L*np.array([np.cos(a),0.45*np.sin(a)+0.25])
        p1=(p0+p2)/2+rng.normal(0,1.5,2)
        for k,p in enumerate(bezier(p0,p1,p2,20)):
            r=2.6*(1-k/20)+0.6; m=(xx-p[0])**2+(yy-p[1])**2<=r*r; wood[m]=1; shade[m]=np.maximum(shade[m],0.35)
    # canopy: blossom clouds around the branch tips, lumpy edges from noise
    inner=[(x,y) for x,y,w,d in out['strokes'] if d<=4 and rng.random()<0.06]
    tips=np.array(out['tips']+inner)
    noise=ndi.gaussian_filter(rng.normal(0,1,(H,W)),2.2); noise/=noise.std()
    fine=rng.random((H,W))
    canopy=np.zeros((H,W)); light=np.zeros((H,W))
    for tx,ty in tips:
        R=rng.uniform(9,15)
        d=np.sqrt((xx-tx)**2+((yy-ty)*1.15)**2)
        c=np.clip(1-d/R+0.18*noise,0,1)
        canopy=np.maximum(canopy,c)
        # each cloud lit on its upper-left side
        l=np.clip(0.55-((xx-tx)*0.6+(yy-ty)*0.8)/R*0.55,0,1)*(c>0)
        light=np.where(c>canopy-1e-6,np.maximum(light,l),light)
    cmask=(canopy>0.08)|((canopy>0.02)&(fine<0.35))          # ragged blossom edge
    # thick limbs: needed to show branches on the underside of the crown
    limbs=np.zeros((H,W),bool)
    for x,y,w,d in out['strokes']:
        if d>=4: limbs|=(xx-x)**2+(yy-y)**2<=max(0.8,w)**2
    out['limbs']=limbs
    return out,wood>0,shade,cmask,canopy,light
def paint(img,W,H,wood,shade,cmask,canopy,light,rng,show_wood_through=True):
    yy,xx=np.mgrid[0:H,0:W]; bay=B4[yy%4,xx%4]
    # bark: 4 tones dithered by the light
    lv=np.clip(shade*3.2,0,3); i=np.floor(lv).astype(int); f=lv-i
    bi=np.clip(i+(bay<f),0,3); bark=np.array(BARK)[bi]
    img[wood]=bark[wood]
    # blossoms: light value -> 5 pinks with ordered dither, plus white sparkles on the lit side
    # blossom clusters: small bumps of light/dark inside every cloud
    bn=ndi.gaussian_filter(rng.normal(0,1,(H,W)),0.9); bn/=bn.std()
    v=np.clip(light*1.0+0.15*(canopy-0.5)+0.16*bn,0,1)*4
    i=np.floor(v).astype(int); f=v-i; pi=np.clip(i+(bay<f),0,4)
    pink=np.array(PK)[pi]
    spark=(light>0.62)&(rng.random((H,W))<0.12)
    pink[spark]=WH
    # tiny dark gaps between blossom clusters keep it from reading as a flat blob
    gaps=(bn<-1.3)&(light<0.5)
    pink[gaps]=PK[0]
    img[cmask]=pink[cmask]
    # loose blossoms just outside the crown edge
    ring=ndi.binary_dilation(cmask,iterations=3)&~cmask
    loose=ring&(rng.random((H,W))<0.12)
    img[loose]=np.where((rng.random((H,W))<0.5)[loose,None],PK[3],PK[2])
    return img
def underside(img,W,H,out,shade,cmask,canopy,by,rng):
    # from high up we look under the lower rim of the crown: thick limbs show there
    yy,xx=np.mgrid[0:H,0:W]; bay=B4[yy%4,xx%4]
    rows=np.where(cmask.any(1))[0]; ctop,cbot=rows.min(),rows.max()
    lower=yy>ctop+(cbot-ctop)*0.5
    # dark hollow under the crown so the limbs have something to sit in
    hollow=cmask&lower&(canopy<0.55)&ndi.binary_dilation(out['limbs'],iterations=3)
    img[hollow]=np.where((bay[hollow]<0.5)[:,None],PK[0],BARK[1])
    show=out['limbs']&cmask&lower&(canopy<0.92)
    lv=np.clip(shade*3.2,0,3); i=np.floor(lv).astype(int); f=lv-i
    bark=np.array(BARK)[np.clip(i+(bay<f),0,3)]
    img[show]=bark[show]
    # a few blossoms hang in front of the limbs again so they sit inside the crown
    front=show&(rng.random((H,W))<0.18)
    img[front]=PK[2]
    return img
def extra_branch(img,shade_ref,p0,p1,p2,w0,w1,rng):
    """Hand-placed curved limb drawn on the crown's underside (user-requested)."""
    H,W,_=img.shape; yy,xx=np.mgrid[0:H,0:W]; bay=B4[yy%4,xx%4]
    pts=bezier(np.array(p0,float),np.array(p1,float),np.array(p2,float),40)
    m=np.zeros((H,W),bool); sh=np.zeros((H,W))
    for k,p in enumerate(pts):
        r=w0+(w1-w0)*k/len(pts)
        d=(xx-p[0])**2+(yy-p[1])**2<=r*r
        m|=d
        sh[d]=np.maximum(sh[d],np.clip(0.55-((xx[d]-p[0])*0.7+(yy[d]-p[1])*0.4)/(r+0.5)*0.5,0,1))
    lv=np.clip(sh*3.2,0,3); i=np.floor(lv).astype(int); f=lv-i
    bark=np.array(BARK)[np.clip(i+(bay<f),0,3)]
    img[m]=bark[m]
    # blossoms hanging over the far half of the limb so it disappears into the crown
    far=m&(xx<(p0[0]+p2[0])/2)&(rng.random((H,W))<0.25)
    img[far]=np.where((rng.random((H,W))<0.5)[far,None],PK[2],PK[3])
    return img
