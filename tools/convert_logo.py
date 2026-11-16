import os
from PIL import Image

src = os.path.join('static','img','logo','logo.png')
dst = os.path.join('static','img','logo','logo.webp')

if not os.path.exists(src):
    raise FileNotFoundError(f"Source image not found: {src}")

im = Image.open(src)
# Resize preserving aspect ratio, max 512x512
im.thumbnail((512, 512), Image.LANCZOS)
# Save as WebP with quality and method
im.save(dst, format='WEBP', quality=85, method=6)
print('Converted', src, 'to', dst)
