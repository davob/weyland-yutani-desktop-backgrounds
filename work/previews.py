# Writes small JPEG previews of every wallpaper to previews/ for the README gallery.
import glob, os
from PIL import Image
os.makedirs('previews', exist_ok=True)
for src in sorted(glob.glob('wallpapers/*.png')):
    name = os.path.splitext(os.path.basename(src))[0]
    im = Image.open(src).convert('RGB').resize((800, 450), Image.LANCZOS)
    im.save(f'previews/{name}.jpg', quality=88, optimize=True, progressive=True)
    print('ok', name)
