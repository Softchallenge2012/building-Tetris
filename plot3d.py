import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from PIL import Image

outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(outputs_dir, exist_ok=True)

def load_img(fname, fallback):
    p = os.path.join(outputs_dir, fname)
    if not os.path.exists(p):
        p = os.path.join(outputs_dir, fallback)
    if not os.path.exists(p):
        im = Image.new('RGB', (150, 150), (255, 255, 255))
    else:
        im = Image.open(p).convert('RGB')
        arr = np.array(im)

        # Mark non-background pixels (anything not near-white)
        bg = (arr[:, :, 0] >= 240) & (arr[:, :, 1] >= 240) & (arr[:, :, 2] >= 240)
        mask = ~bg

        # Remove single lines / thin artifacts with morphological opening
        from scipy import ndimage
        struct = np.ones((3, 3), dtype=bool)
        cleaned = ndimage.binary_opening(mask, structure=struct, iterations=2)

        # Keep only the largest connected component (the building block)
        labeled, n = ndimage.label(cleaned)
        if n > 0:
            sizes = ndimage.sum(cleaned, labeled, range(1, n + 1))
            main_label = int(np.argmax(sizes)) + 1
            building = labeled == main_label
            rows = np.any(building, axis=1)
            cols = np.any(building, axis=0)
            if rows.any() and cols.any():
                rmin, rmax = np.where(rows)[0][[0, -1]]
                cmin, cmax = np.where(cols)[0][[0, -1]]
                im = im.crop((cmin, rmin, cmax + 1, rmax + 1))

        # Save trimmed image before resizing
        trimmed_path = os.path.join(outputs_dir, "trimmed_" + os.path.basename(p))
        im.save(trimmed_path)
        im = im.resize((150, 150))
    return np.array(im) / 255.0

south_img = load_img("facade_elevation_south.png", "elevation_bottom_south.png")
north_img = load_img("facade_elevation_north.png", "elevation_top_north.png")
west_img = load_img("facade_elevation_west.png", "elevation_left_west.png")
east_img = load_img("facade_elevation_east.png", "elevation_right_east.png")

fig = plt.figure(figsize=(10, 10), dpi=150)
ax = fig.add_subplot(111, projection='3d')

# South face (y = 0)
X, Z = np.meshgrid(np.linspace(0, 10, south_img.shape[1]), np.linspace(17, 0, south_img.shape[0]))
Y = np.full_like(X, 0)
ax.plot_surface(X, Y, Z, facecolors=south_img, rstride=1, cstride=1, shade=False)

# North face (y = 10)
X, Z = np.meshgrid(np.linspace(10, 0, north_img.shape[1]), np.linspace(17, 0, north_img.shape[0]))
Y = np.full_like(X, 10)
ax.plot_surface(X, Y, Z, facecolors=north_img, rstride=1, cstride=1, shade=False)

# West face (x = 0)
Y, Z = np.meshgrid(np.linspace(0, 10, west_img.shape[1]), np.linspace(17, 0, west_img.shape[0]))
X = np.full_like(Y, 0)
ax.plot_surface(X, Y, Z, facecolors=west_img, rstride=1, cstride=1, shade=False)

# East face (x = 10)
Y, Z = np.meshgrid(np.linspace(10, 0, east_img.shape[1]), np.linspace(17, 0, east_img.shape[0]))
X = np.full_like(Y, 10)
ax.plot_surface(X, Y, Z, facecolors=east_img, rstride=1, cstride=1, shade=False)

ax.set_xlim(-2, 12)
ax.set_ylim(-2, 12)
ax.set_zlim(0, 20)
ax.set_box_aspect((1, 1, 1.7))
ax.view_init(elev=25, azim=-45)
ax.set_axis_off()

out_3d = os.path.join(outputs_dir, "building_3d_view.png")
fig.savefig(out_3d, bbox_inches='tight', pad_inches=0.1, facecolor='#0f172a')
plt.close(fig)