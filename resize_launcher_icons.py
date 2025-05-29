from PIL import Image
import os

# Define the sizes for each density
sizes = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

# Path to the source icon
src_icon = 'meankieli-android/app/src/main/assets/icon.png'

# Resize and save to each mipmap folder
for folder, size in sizes.items():
    out_dir = f'meankieli-android/app/src/main/res/{folder}'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'ic_launcher.png')
    with Image.open(src_icon) as img:
        img = img.convert('RGBA')
        img = img.resize((size, size), Image.LANCZOS)
        img.save(out_path, format='PNG')
    print(f'Saved {out_path}') 