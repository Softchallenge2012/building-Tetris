from PIL import Image, ImageDraw, ImageFont
from collections import Counter

# ---------- 1. Read the top-view plan and extract the 10x10 grid ----------
src = Image.open('outputs/top_view.png').convert('RGB')

GRID_N = 10  # 10x10 cells, each 50px in the 500x500 source image = 10ft in real life
CELL_PX = src.width // GRID_N

def dominant_color(img, x0, y0, x1, y1):
    cnt = Counter()
    for x in range(x0, x1, 2):
        for y in range(y0, y1, 2):
            cnt[img.getpixel((x, y))] += 1
    return cnt.most_common(1)[0][0]

grid = []
for r in range(GRID_N):
    row = []
    for c in range(GRID_N):
        x0, x1 = c * CELL_PX + 5, (c + 1) * CELL_PX - 5
        y0, y1 = r * CELL_PX + 5, (r + 1) * CELL_PX - 5
        row.append(dominant_color(src, x0, y0, x1, y1))
    grid.append(row)

BLACK = (0, 0, 0)

def label(color):
    return {(0, 0, 0): 'ground', (0, 255, 0): 'green',
            (255, 170, 0): 'orange', (0, 255, 255): 'lightblue'}.get(color, 'ground')

# ---------- 2. Project the footprint onto each of the four outer faces ----------
# TOP: scan each column from the top row (row 0) downward, first building hit is visible
top = []
for c in range(GRID_N):
    val = 'ground'
    for r in range(GRID_N):
        if grid[r][c] != BLACK:
            val = label(grid[r][c]); break
    top.append(val)

# BOTTOM: scan each column from the bottom row upward
bottom = []
for c in range(GRID_N):
    val = 'ground'
    for r in range(GRID_N - 1, -1, -1):
        if grid[r][c] != BLACK:
            val = label(grid[r][c]); break
    bottom.append(val)

# LEFT: scan each row from the left column rightward
left = []
for r in range(GRID_N):
    val = 'ground'
    for c in range(GRID_N):
        if grid[r][c] != BLACK:
            val = label(grid[r][c]); break
    left.append(val)

# RIGHT: scan each row from the right column leftward
right = []
for r in range(GRID_N):
    val = 'ground'
    for c in range(GRID_N - 1, -1, -1):
        if grid[r][c] != BLACK:
            val = label(grid[r][c]); break
    right.append(val)

elevations = {
    'Top elevation (north face)': top,
    'Bottom elevation (south face)': bottom,
    'Left elevation (west face)': left,
    'Right elevation (east face)': right,
}

# ---------- 3. Draw each elevation as a 10ft-tall wall strip ----------
FT_TO_PX = 12          # drawing scale: 12 px per foot
SEG_W = FT_TO_PX * 10  # each cell = 10 ft wide
WALL_H = FT_TO_PX * 10 # walls are 10 ft tall
MARGIN = 60
TITLE_H = 30
PANEL_H = TITLE_H + WALL_H + 30
IMG_W = MARGIN * 2 + SEG_W * GRID_N
IMG_H = MARGIN * 2 + PANEL_H * 4 + 40  # +legend space

COLOR_HEX = {
    'green': (0, 204, 0),
    'orange': (255, 170, 0),
    'lightblue': (51, 204, 255),
    'ground': None,  # no wall drawn, just ground line
}

try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
except Exception:
    font_title = ImageFont.load_default()
    font_small = ImageFont.load_default()

def draw_elevation(draw, title, seq, top_y):
    wall_top = top_y + TITLE_H
    baseline = wall_top + WALL_H
    for i, val in enumerate(seq):
        x0 = MARGIN + i * SEG_W
        x1 = x0 + SEG_W
        color = COLOR_HEX[val]
        if color:
            draw.rectangle([x0, wall_top, x1, baseline], fill=color)

def render_combined():
    img = Image.new('RGB', (IMG_W, IMG_H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = MARGIN
    for title, seq in elevations.items():
        draw_elevation(draw, title, seq, y)
        y += PANEL_H
    # legend
    ly = y + 10
    swatches = [('RC building', (255, 170, 0)), ('RBath building', (0, 204, 0)),
                ('Light blue deck', (51, 204, 255))]
    lx = MARGIN
    for text, color in swatches:
        draw.rectangle([lx, ly, lx + 16, ly + 16], fill=color, outline=(90, 90, 90))
        draw.text((lx + 22, ly), text, fill=(20, 20, 20), font=font_small)
        lx += 170
    draw.rectangle([lx, ly, lx + 16, ly + 16], fill=(255, 255, 255), outline=(90, 90, 90))
    draw.text((lx + 22, ly), 'Open ground (no wall)', fill=(20, 20, 20), font=font_small)
    return img

def render_single(title, seq):
    h = MARGIN * 2 + PANEL_H
    img = Image.new('RGB', (IMG_W, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw_elevation(draw, title, seq, MARGIN)
    return img

combined = render_combined()
combined.save('outputs/site_elevations_combined.png')

file_map = {
    'Top elevation (north face)': 'elevation_top_north.png',
    'Bottom elevation (south face)': 'elevation_bottom_south.png',
    'Left elevation (west face)': 'elevation_left_west.png',
    'Right elevation (east face)': 'elevation_right_east.png',
}
for title, seq in elevations.items():
    img = render_single(title, seq)
    
    # Extract the single floor wall strip (wall_top to baseline)
    wall_top = MARGIN + TITLE_H
    baseline = wall_top + WALL_H
    wall_crop = img.crop((0, wall_top, IMG_W, baseline))
    
    # Stack the floor image 17 times to simulate 17 floors
    stacked_h = WALL_H * 17
    stacked_img = Image.new('RGB', (IMG_W, stacked_h), (255, 255, 255))
    for f in range(17):
        stacked_img.paste(wall_crop, (0, f * WALL_H))
        
    stacked_img.save(f'outputs/{file_map[title]}')

print('Grid (row by row):')
for r in grid:
    print([label(c) for c in r])
print()
print('TOP   :', top)
print('BOTTOM:', bottom)
print('LEFT  :', left)
print('RIGHT :', right)
print('Done.')
