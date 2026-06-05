import sys, os
from PIL import Image

src = 'frontend/icon.png'
if not os.path.exists(src):
    print('No icon.png found, skipping')
    sys.exit(0)

try:
    img = Image.open(src).convert('RGBA')
    targets = [
        (192, 'frontend/public/icon-192.png'),
        (512, 'frontend/public/icon-512.png'),
        (180, 'frontend/public/apple-touch-icon.png'),
    ]
    for size, path in targets:
        img.resize((size, size), Image.LANCZOS).save(path, 'PNG')
        print(f'Icon {size}x{size} -> {path}')
except Exception as e:
    print(f'Icon generation failed (non-fatal): {e}')
