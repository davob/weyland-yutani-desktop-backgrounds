from PIL import Image, ImageFilter
import numpy as np
rng=np.random.default_rng(7)
W,H=3840,2160
# --- clean logo layer (light-on-dark, to be screen-blended) ---
logo=Image.open('work/logo_layer.png').convert('RGB')
L=np.zeros((H,W,3),np.float32); ox,oy=(W-logo.width)//2,(H-logo.height)//2
L[oy:oy+logo.height,ox:ox+logo.width]=np.asarray(logo)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
cx,cy=W/2,H/2
r=np.sqrt(((xx-cx)/(W/2))**2+((yy-cy)/(H/2))**2)  # 0 centre ~1.41 corners
def mix(c0,c1,t): t=np.clip(t,0,1)[...,None]; return np.array(c0,np.float32)*(1-t)+np.array(c1,np.float32)*t
def grain(img,amt): return img+rng.normal(0,amt,img.shape[:2])[...,None]
def glow(strength,color,blur=60):
    g=Image.fromarray(np.clip(L,0,255).astype(np.uint8)).resize((W//8,H//8),Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur/8)).resize((W,H),Image.BILINEAR)
    g=np.asarray(g).astype(np.float32).max(2,keepdims=True)/255
    return g*np.array(color,np.float32)*strength
def finish(bg,name,glowc=None,gs=0):
    if glowc is not None: bg=bg+glow(gs,glowc)
    bg=np.clip(bg,0,255)
    out=255-(255-bg)*(255-L)/255   # screen blend keeps the glyph look
    Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save(f'wallpapers/wy-{name}.png',optimize=True)
    Image.fromarray(np.clip(out,0,255).astype(np.uint8)).resize((960,540),Image.LANCZOS).save(f'work/p-{name}.png')

# 1 Deep space navy: radial gradient + faint stars away from logo
bg=mix((22,34,58),(3,5,10),r/1.2)
st=rng.random((H,W))>0.99955; br=rng.random((H,W))**3*150+30
mask=np.clip((np.abs(yy-cy)/(logo.height*0.75)-0.6),0,1)
stars=np.zeros((H,W),np.float32); stars[st]=br[st]
stars=np.asarray(Image.fromarray(stars.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32)*4.5*mask
bg=bg+stars[...,None]*np.array([0.85,0.9,1.0]); finish(grain(bg,1.5),'1-deep-space',(60,70,40),0.35)

# 2 CRT terminal: dark teal-green phosphor, scanlines, vignette
bg=mix((14,40,38),(2,8,8),(r/1.25)**1.3)
scan=(np.sin(yy*np.pi/3)**2)[...,None]*0.18+0.82
finish(grain(bg*scan,1.8),'2-crt-terminal',(50,60,30),0.4)

# 3 Warm amber haze: dark brown/charcoal, warm centre
bg=mix((48,34,20),(8,6,5),(r/1.2)**1.1)
finish(grain(bg,2.2),'3-amber-haze',(70,55,20),0.45)

# 4 Blueprint grid: slate blue with faint engineering grid
bg=mix((30,40,54),(9,12,18),(r/1.25)**1.2)
g1=((xx%60<1.5)|(yy%60<1.5)).astype(np.float32)*0.5+((xx%300<2)|(yy%300<2)).astype(np.float32)*0.7
g1=np.asarray(Image.fromarray((np.clip(g1,0,1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32)/255
fade=np.clip(1-r/1.5,0,1)*0.6+0.4
bg=bg+(g1*fade*14)[...,None]*np.array([0.7,0.9,1.0]); finish(grain(bg,1.2),'4-blueprint-grid',(55,65,45),0.3)

# 5 Graphite horizon: charcoal with soft horizontal light band behind logo
band=np.exp(-((yy-cy)/(H*0.22))**2)*np.exp(-((xx-cx)/(W*0.55))**2)
bg=mix((10,11,13),(46,48,52),band)+0
finish(grain(bg,2.0),'5-graphite-horizon',(50,55,40),0.3)
