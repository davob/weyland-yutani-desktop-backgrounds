# Step 1: track the character grid's local phase across the photo (camera lens makes pitch drift).
from PIL import Image, ImageFilter
import numpy as np
from scipy.ndimage import gaussian_filter1d as g1
im=Image.open('images/1.webp').convert('RGB').filter(ImageFilter.MedianFilter(3))
lum=np.asarray(im).astype(np.float32).max(2)
rows=[119,157,195,233,270,308,346,384,421,459,497,540]
prof=np.zeros(2000)
for y in rows: prof+=lum[y-12:y+12].mean(0)
x=np.arange(2000); p0=19.9
z=(prof-g1(prof,30))*np.exp(-2j*np.pi*x/p0)
ph=np.unwrap(np.angle(g1(z.real,60)+1j*g1(z.imag,60)))
np.save('work/phase.npy',ph); print('phase saved')
