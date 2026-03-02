import json
from PIL import Image, ImageDraw, ImageFont
from PIL import Image, ImageDraw, ImageFont

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

# 3. Load image using PIL (for Hebrew text) or OpenCV
img_path = 'data/israel.png'
# Using PIL to write Hebrew text
img = Image.open(img_path).convert('RGB')
draw = ImageDraw.Draw(img)

# Try loading a readable font, fallback to default
try:
    font = ImageFont.truetype("data/fonts/Heebo-Regular.ttf", 20)
except IOError:
    font = ImageFont.load_default()

# 4. Draw points and labels
for name, x, y in points_to_draw:
    # Reverse text for PIL if it doesn't handle RTL natively
    text = name[::-1]
    
    # Draw red circle
    r = 5
    draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 0, 0), outline=(0, 0, 0))
    
    # Draw text
    draw.text((x + 8, y - 10), text, font=font, fill=(255, 0, 0))

# Save output
out_path = 'data/israel_with_new_settlements.png'
img.save(out_path)
print(f"Saved verification map with {len(points_to_draw)} new settlements to {out_path}")
