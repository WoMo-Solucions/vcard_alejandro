import qrcode
from PIL import Image, ImageDraw
import math

# ---------- CONFIG ----------
qr_data = "https://womo-solucions.github.io/Vcard/"
logo_text_path = "logo.png"   # imagen con las letras JR (se usará como molde)
qr_logo_path = "logo.png"     # logo que irá en el centro (puede ser el mismo archivo)
out_path = "QR_JR_Metalizado.png"

box_size = 10      # tamaño en px de cada módulo del QR (puedes ajustar)
border = 4         # borde en módulos del QR
# ----------------------------

# Metales/colores para degradado (ajusta si quieres otro tono)
color_top = (20, 50, 95)    # azul oscuro (arriba)
color_bottom = (70, 150, 160)  # azul-verdoso claro (abajo)

# Tamaño del logo central (en píxeles). Ajusta si necesitas logo más grande.
logo_size = 80
blank_margin = 6  # espacio extra (px) alrededor del logo dentro del área blanca

# 1) Generar QR base (alto nivel de corrección para permitir overlay)
qr = qrcode.QRCode(
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=box_size,
    border=border
)
qr.add_data(qr_data)
qr.make(fit=True)

qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
w, h = qr_img.size

# 2) Crear máscara a partir de tu logo (molde de las letras "JR")
logo_text = Image.open(logo_text_path).convert("RGBA")

# Si la imagen tiene canal alpha, usamos alpha como máscara; si no, binarizamos la luminancia
if "A" in logo_text.getbands():
    mask_src = logo_text.split()[3]  # canal alpha
else:
    mask_src = logo_text.convert("L").point(lambda p: 255 if p < 240 else 0)

# Queremos que la silueta ocupe casi todo el área del QR dejando una línea de módulos
margin_px = box_size * 3  # dos líneas de módulos alrededor
target_w = w - 2 * margin_px
target_h = h - 2 * margin_px

# Mantener proporciones: redimensionamos maximizando sin salirse
mask_src = mask_src.convert("L")
mask_src.thumbnail((target_w, target_h), Image.LANCZOS)
mask_w, mask_h = mask_src.size

# Binarizar después de escalar para evitar semitonos
mask_src = mask_src.point(lambda p: 255 if p > 128 else 0)

# Pegar la máscara centrada en una máscara del tamaño completo del QR
mask_full = Image.new("L", (w, h), 0)
pos_x = (w - mask_w) // 2
pos_y = (h - mask_h) // 2
mask_full.paste(mask_src, (pos_x, pos_y))

# 3) Reservar área blanca para el logo central (lo dejamos fuera de la máscara)
blank_size = logo_size + blank_margin * 2
blank_x = (w - blank_size) // 2
blank_y = (h - blank_size) // 2

# Limpiar la máscara en el rectángulo central (para que esa área no sea coloreada)
mask_pixels = mask_full.load()
for yy in range(blank_y, blank_y + blank_size):
    if yy < 0 or yy >= h:
        continue
    for xx in range(blank_x, blank_x + blank_size):
        if xx < 0 or xx >= w:
            continue
        mask_pixels[xx, yy] = 0

# 4) Recolorear SOLO los módulos negros que estén dentro de la máscara con degradado metalizado
colored = qr_img.copy()
px_col = colored.load()
px_mask = mask_full.load()

# Para cálculo de degradado usamos la franja vertical relativa dentro del molde
for y in range(h):
    for x in range(w):
        # Si este pixel está marcado por la máscara y el pixel QR es negro:
        cur = px_col[x, y]      # RGBA tupla
        # comparo por RGB (sin transparencia)
        if px_mask[x, y] > 128 and cur[0:3] == (0, 0, 0):
            # ratio vertical relativo dentro del área del molde
            # (clamp para estar seguros)
            local_y = min(max(y - pos_y, 0), max(mask_h - 1, 1))
            ratio = local_y / max(mask_h - 1, 1)

            # color base por interpolación linear
            r_base = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g_base = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b_base = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)

            # añadir un brillo sutil tipo "sheen" en la zona central para efecto metalizado
            sheen = (1 - abs(2 * ratio - 1)) ** 3  # pico en el centro
            add = int(40 * sheen)  # intensidad del brillo (ajusta 0..60)
            r = min(255, r_base + add)
            g = min(255, g_base + add)
            b = min(255, b_base + add)

            # aplicar color (manteniendo alpha = 255)
            px_col[x, y] = (r, g, b, 255)

# 5) Dibujar el área blanca central (para que el logo repose en blanco)
draw = ImageDraw.Draw(colored)
draw.rectangle([blank_x, blank_y, blank_x + blank_size - 1, blank_y + blank_size - 1], fill=(255, 255, 255, 255))

# 6) Pegar logo centrado (sin borde, tal como pediste)
logo_center = Image.open(qr_logo_path).convert("RGBA")
logo_center = logo_center.resize((logo_size, logo_size), Image.LANCZOS)
logo_pos = ((w - logo_size) // 2, (h - logo_size) // 2)
colored.paste(logo_center, logo_pos, logo_center)

# 7) Guardar
colored.save(out_path)
print("✅ QR generado:", out_path)

