import os
from pathlib import Path
from PIL import Image

icon_dir = Path('static/img/icons')
for png_path in icon_dir.glob('*.png'):
    webp_path = png_path.with_suffix('.webp')
    if webp_path.exists():
        continue
    im = Image.open(png_path)
    # No resizing specified for icons, keep original size
    im.save(webp_path, format='WEBP', quality=85, method=6)
    print(f'Converted {png_path.name} to {webp_path.name}')
