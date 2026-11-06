"""Create recoloured variants of some downloaded maps + a procedural light-quartz worktop set.
usage: python -I make_derived.py
"""
import os
import numpy as np
from PIL import Image

T = "/tmp/claude-0/-home-user-isis-medical/29082e2e-5040-5750-9e57-b941bd9f147a/scratchpad/assets/textures"


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255.0


def save(a, p, q=93):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p, quality=q)
    print("wrote", p)


def lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def retint(src, dst, target_rgb, contrast=1.0):
    """Replace hue/sat by a target colour, keep the luminance pattern (relative to mean)."""
    a = load(src)
    L = lum(a)
    rel = 1.0 + contrast * (L / L.mean() - 1.0)
    t = np.array(target_rgb, np.float32) / 255.0
    save(rel[..., None] * t[None, None, :], dst)


def hsv_adjust(src, dst, hue_to=None, hue_mix=1.0, sat_mul=1.0, val_mul=1.0):
    im = Image.open(src).convert("HSV")
    h, s, v = [np.asarray(c).astype(np.float32) for c in im.split()]
    if hue_to is not None:
        # circular move of the hue toward hue_to (0..255 scale)
        mean_h = np.angle(np.exp(1j * h / 255 * 2 * np.pi).mean()) / (2 * np.pi) * 255 % 255
        shift = (hue_to - mean_h) * hue_mix
        h = (h + shift) % 255
    s = np.clip(s * sat_mul, 0, 255)
    v = np.clip(v * val_mul, 0, 255)
    out = Image.merge("HSV", [Image.fromarray(x.astype(np.uint8)) for x in (h, s, v)]).convert("RGB")
    out.save(dst, quality=93)
    print("wrote", dst)


# --- recolours -------------------------------------------------------------
retint(f"{T}/fabric_linen/rough_linen_diff_2k.jpg", f"{T}/fabric_linen/rough_linen_diff_2k_offwhite.jpg", (236, 232, 224), contrast=0.9)
retint(f"{T}/fabric_sofa/poly_wool_herringbone_diff_2k.jpg", f"{T}/fabric_sofa/poly_wool_herringbone_diff_2k_greige.jpg", (196, 188, 176), contrast=1.0)
hsv_adjust(f"{T}/grass/grass_ground_diff_2k.jpg", f"{T}/grass/grass_ground_diff_2k_green.jpg", hue_to=62, hue_mix=0.85, sat_mul=1.25, val_mul=0.95)
hsv_adjust(f"{T}/tile_floor_bath/marble_01_diff_2k.jpg", f"{T}/tile_floor_bath/marble_01_diff_2k_greige.jpg", sat_mul=0.5, val_mul=1.06)
retint(f"{T}/render_exterior/white_stucco_02_diff_2k.jpg", f"{T}/render_exterior/white_stucco_02_diff_2k_offwhite.jpg", (232, 228, 218), contrast=1.0)


# --- procedural light quartz ------------------------------------------------
def periodic_noise(n, rng, f_lo, f_hi, slope=1.0):
    """Tileable band-limited noise via FFT. Frequencies in cycles per tile."""
    fx = np.fft.fftfreq(n) * n
    fy = np.fft.fftfreq(n) * n
    FX, FY = np.meshgrid(fx, fy)
    f = np.sqrt(FX ** 2 + FY ** 2)
    amp = np.where((f >= f_lo) & (f <= f_hi), 1.0 / np.maximum(f, 1) ** slope, 0.0)
    ph = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    x = np.real(np.fft.ifft2(amp * ph))
    return (x - x.mean()) / (x.std() + 1e-9)


N = 2048
rng = np.random.default_rng(42)
qd = f"{T}/worktop_stone"
os.makedirs(qd, exist_ok=True)
base = np.array([238, 235, 229], np.float32) / 255.0
cloud = periodic_noise(N, rng, 1, 24, 1.5)  # soft clouding (tile = 1.2 m)
grain = periodic_noise(N, rng, 200, 700, 0.0)  # ~1-3 mm grains
grain2 = periodic_noise(N, rng, 120, 400, 0.0)
def aniso_noise(n, rng, f_lo, f_hi, stretch=3.0, slope=1.5):
    fx = np.fft.fftfreq(n) * n
    fy = np.fft.fftfreq(n) * n
    FX, FY = np.meshgrid(fx, fy)
    f = np.sqrt((FX * stretch) ** 2 + FY ** 2)
    amp = np.where((f >= f_lo) & (f <= f_hi), 1.0 / np.maximum(f, 1) ** slope, 0.0)
    ph = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    x = np.real(np.fft.ifft2(amp * ph))
    return (x - x.mean()) / (x.std() + 1e-9)


vn = aniso_noise(N, rng, 1.5, 14, 3.0, 2.0) + 0.035 * periodic_noise(N, rng, 14, 60, 1.0)
fade = np.clip(0.5 + 0.8 * periodic_noise(N, rng, 1, 5, 1.0), 0, 1)
veins = (np.exp(-(vn / 0.03) ** 2) * 0.9 + np.exp(-(vn / 0.2) ** 2) * 0.2) * fade
veins2 = np.exp(-((aniso_noise(N, rng, 3, 20, 2.0, 2.0)) / 0.025) ** 2) * 0.35 * np.clip(periodic_noise(N, rng, 1, 6, 1.0), 0, 1)
veins = np.clip(np.maximum(veins, veins2), 0, 1)
L = 1.0 + 0.010 * cloud
L -= 0.09 * veins
specks = (grain > 2.3).astype(np.float32)  # grey specks
dark = (grain2 > 3.4).astype(np.float32)  # sparse darker specks
L -= 0.07 * specks + 0.25 * dark
L += 0.035 * np.clip(grain, 0, None) * 0.3  # sparkle
col = L[..., None] * base[None, None, :]
col[..., 2] += 0.012 * veins  # veins slightly cooler/grey
save(col, f"{qd}/quartz_light_diff_2k.jpg")
rough = 0.14 + 0.025 * periodic_noise(N, rng, 4, 60, 1.0) + 0.05 * specks
save(np.repeat(np.clip(rough, 0.08, 0.3)[..., None], 3, 2), f"{qd}/quartz_light_rough_2k.jpg")
h = 0.3 * specks + 0.2 * dark + 0.05 * grain
gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
s = 0.6
nx, ny, nz = -gx * s, gy * s, np.ones_like(h)  # OpenGL: +Y up (image rows go down)
ln = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
nrm = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5
Image.fromarray((nrm * 255 + 0.5).astype(np.uint8)).save(f"{qd}/quartz_light_nor_gl_2k.png")
print("wrote", f"{qd}/quartz_light_nor_gl_2k.png")
