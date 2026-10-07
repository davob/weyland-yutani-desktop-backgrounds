# Plain near-black 4K wallpaper with the crisp logo centred.
from PIL import Image; import numpy as np
W,H=3840,2160; bg=np.array([2,4,6],np.float32)
logo=np.asarray(Image.open('work/logo_layer.png').convert('RGB')).astype(np.float32)
L=np.zeros((H,W,3),np.float32); ox,oy=(W-logo.shape[1])//2,(H-logo.shape[0])//2
L[oy:oy+logo.shape[0],ox:ox+logo.shape[1]]=logo
out=255-(255-bg)*(255-L)/255
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save('wallpapers/weyland-yutani-wallpaper-4k.png',optimize=True)
print('ok plain')
