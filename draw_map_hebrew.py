import json
from PIL import Image, ImageDraw, ImageFont
import re

def reverse_hebrew(text):
    # Only reverse consecutive Hebrew characters or whole string if mostly Hebrew
    return text[::-1]

# 1. Load the new locations we just added
targets = ["שערי תקוה", "עץ אפרים", "עשהאל", "לשם", "מגרון", "אש קודש", "קידה", "סוסיא", "אביגיל"]
with open('data/game_data.json', encoding='utf-8') as f:
    game_data = json.load(f)

# 2. Get coords from data
points_to_draw = []
for name in targets:
    for k, v in game_data.items():
        if v["name"] == name:
            points_to_draw.append((name, v["x"], v["y"]))
            break

# 3. Load image using PIL
img_path = 'data/israel.png'
img = Image.open(img_path).convert('RGB')
draw = ImageDraw.Draw(img)

# Try loading the downloaded Heebo font
try:
    font = ImageFont.truetype("data/fonts/Heebo-Regular.ttf", 20)
except IOError:
    print("Failed to load Heebo font, using default")
    font = ImageFont.load_default()

# 4. Draw points and labels
for name, x, y in points_to_draw:
    # Reverse text for PIL native drawing of RTL languages
    text = name[::-1]
    
    # Draw red circle
    r = 5
    draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 0, 0), outline=(0, 0, 0))
    
    # Draw text shadow for better visibility
    draw.text((x + 9, y - 9), text, font=font, fill=(255, 255, 255))
    draw.text((x + 7, y - 11), text, font=font, fill=(255, 255, 255))
    # Draw text
    draw.text((x + 8, y - 10), text, font=font, fill=(255, 0, 0))

# Save output
out_path = 'data/israel_with_new_settlements.png'
img.save(out_path)
print(f"Saved verification map with {len(points_to_draw)} new settlements to {out_path}")
