# qr_generator.py
# Requisitos: pip install qrcode[pil] pillow

import qrcode
from PIL import Image, ImageOps
import os

# ================== CONFIG ==================
qr_data = "https://womo-solucions.github.io/vcard_alejandro/"  # <-- Tu URL
qr_logo_path = "logo.png"      # <-- Logo que irá en el centro (PNG recomendado con fondo transp.)
out_path = "QR.png"            # <-- Salida del QR
box_size = 12                  # Tamaño del módulo del QR (px)
border = 4                     # Borde del QR (módulos)
logo_scale = 0.22              # Proporción del lado del logo vs. lado del QR (0.15 - 0.30 funciona bien)
white_pad = 18                 # Padding blanco alrededor del logo (px)
rounded_white_box = True       # Caja blanca con bordes redondeados
white_box_radius = 18          # Radio de la caja blanca
recolor_qr = False             # Si True, recolorea módulos negros con un degradado
color_top = (20, 50, 95)       # Arriba (si recolor_qr=True)
color_bottom = (70, 150, 160)  # Abajo (si recolor_qr=True)
# ============================================


def make_qr_image(data: str, box_size: int = 10, border: int = 4):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGBA")


def recolor_qr_vertical(img: Image.Image, top_rgb, bottom_rgb) -> Image.Image:
    """Recolorea (solo donde es negro) con un degradado vertical."""
    img = img.copy()
    px = img.load()
    w, h = img.size
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top_rgb[0] * (1 - t) + bottom_rgb[0] * t)
        g = int(top_rgb[1] * (1 - t) + bottom_rgb[1] * t)
        b = int(top_rgb[2] * (1 - t) + bottom_rgb[2] * t)
        for x in range(w):
            r0, g0, b0, a0 = px[x, y]
            # Recolorear solo módulos negros puros
            if (r0, g0, b0) == (0, 0, 0):
                px[x, y] = (r, g, b, a0)
    return img


def paste_logo_center(base: Image.Image, logo_path: str, scale: float, pad: int,
                      rounded_box: bool, radius: int) -> Image.Image:
    """Pega el logo centrado sobre una caja blanca opcional."""
    if not os.path.exists(logo_path):
        raise FileNotFoundError(f"No se encontró el logo: {logo_path}")

    base = base.copy()
    bw, bh = base.size

    # Escalar logo según el lado del QR
    target_logo_side = int(min(bw, bh) * scale)
    logo = Image.open(logo_path).convert("RGBA")
    logo = ImageOps.contain(logo, (target_logo_side, target_logo_side), method=Image.LANCZOS)
    lw, lh = logo.size

    # Caja blanca
    box_w = lw + pad * 2
    box_h = lh + pad * 2

    white_box = Image.new("RGBA", (box_w, box_h), (255, 255, 255, 255))
    if rounded_box and radius > 0:
        # Crear máscara redondeada
        mask = Image.new("L", (box_w, box_h), 0)
        rr = Image.new("L", (box_w, box_h), 0)
        rr_draw = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        # Truco con ImageOps para redondear
        white_box = ImageOps.expand(ImageOps.fit(white_box, (box_w, box_h)), border=0, fill=(255, 255, 255, 255))
        white_box = ImageOps.rounded_rectangle(white_box, radius=radius, fill=(255, 255, 255, 255))

    # Posiciones
    cx = (bw - box_w) // 2
    cy = (bh - box_h) // 2
    base.alpha_composite(white_box, (cx, cy))

    # Pegar logo centrado dentro de la caja
    lx = cx + (box_w - lw) // 2
    ly = cy + (box_h - lh) // 2
    base.alpha_composite(logo, (lx, ly))
    return base


def main():
    qr_img = make_qr_image(qr_data, box_size=box_size, border=border)
    if recolor_qr:
        qr_img = recolor_qr_vertical(qr_img, color_top, color_bottom)
    qr_img = paste_logo_center(qr_img, qr_logo_path, logo_scale, white_pad, rounded_white_box, white_box_radius)
    qr_img.save(out_path)
    print(f"✅ QR generado: {out_path}")


if __name__ == "__main__":
    main()
