"""
Fonctions de dessin (PIL) pour construire chaque visuel du combat, format
"empile" (haut vs bas) :
- fond en deux couleurs complementaires (haut / bas)
- cadre arrondi contenant la photo de l'animal : MEME dimension et MEME
  espacement depuis le centre pour les deux zones (vraie symetrie)
- legende (nom de l'animal) grande et rapprochee du cadre, du cote du bord
  exterieur de l'ecran
- barre de decompte horizontale au centre (derriere le badge VS), contour
  blanc uniquement en haut/bas de la barre (pas sur les cotes), qui se
  remplit de gauche a droite pendant 3 secondes (noire avant le decompte).
  Le badge VS (contour + "VS") clignote en jaune/blanc pendant le decompte,
  puis reste fige en jaune (contour + texte) jusqu'au round suivant.
- resultat : photos assombries a 70% (jamais le badge VS), gros pourcentage
  en contour blanc
- reveal : la moitie du perdant garde sa couleur de fond mais perd sa photo
  et son nom, remplaces par le texte d'explication ; ne deborde jamais sur
  le badge VS
Tout est rendu en PNG/numpy puis transforme en clip par video_builder.py
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageChops

DIVIDER_THICKNESS_RATIO = 0.0225  # epaisseur de la barre de decompte / du total height
VS_BADGE_RADIUS_RATIO = 0.095     # rayon du badge VS / largeur
OUTLINE_WIDTH_RATIO = 0.006       # epaisseur du contour blanc (barre + badge) / largeur

FRAME_GAP_FROM_DIVIDER_RATIO = 0.018  # espace entre l'animal et la barre centrale (identique haut/bas)
FRAME_H_RATIO = 0.92                  # hauteur dispo pour l'animal / hauteur de la zone (identique haut/bas)
CAPTION_GAP_RATIO = 0.014             # petit espace fixe entre la legende et le cadre
TEXT_STROKE_RATIO = 0.024             # epaisseur du contour de texte / taille de police (coherent partout)

WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
GOLD = (255, 214, 0, 255)


def _text_stroke_width(font_size: int) -> int:
    """Epaisseur de contour de texte, proportionnelle a la taille de police (coherente partout)."""
    return max(1, round(font_size * TEXT_STROKE_RATIO))


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        for fallback in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                          "C:/Windows/Fonts/arialbd.ttf",
                          "C:/Windows/Fonts/arial.ttf"):
            if os.path.exists(fallback):
                return ImageFont.truetype(fallback, size)
        return ImageFont.load_default()


def _text_w(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def draw_centered_text(draw, xy, text, font, fill, stroke_width=0, stroke_fill=None, anchor="mm"):
    x, y = xy
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor,
               stroke_width=stroke_width, stroke_fill=stroke_fill)


def _wrap_lines(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for w in words:
        trial = (current + " " + w).strip()
        if _text_w(draw, trial, font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_wrapped_text(draw, box, text, font, fill, line_spacing=14, align="center",
                       stroke_width=0, stroke_fill=None):
    """Dessine du texte multi-lignes centre verticalement dans un rectangle 'box'=(x0,y0,x1,y1)."""
    x0, y0, x1, y1 = box
    lines = _wrap_lines(draw, text, font, x1 - x0)

    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    total_h = sum(line_heights) + line_spacing * (len(lines) - 1)
    cy = y0 + (y1 - y0 - total_h) / 2

    for line, lh in zip(lines, line_heights):
        cx = (x0 + x1) / 2
        draw.text((cx, cy + lh / 2), line, font=font, fill=fill, anchor="mm",
                   stroke_width=stroke_width, stroke_fill=stroke_fill, align=align)
        cy += lh + line_spacing


def draw_wrapped_text_from_edge(draw, x0, x1, edge_y, text, font, fill, line_spacing=6,
                                 stroke_width=0, stroke_fill=None, grow="up"):
    """
    Comme draw_wrapped_text, mais ancre le bloc de texte a 'edge_y' au lieu
    de le centrer dans une box (permet de coller precisement le texte au
    cadre photo). grow='up' : edge_y est le BAS du bloc, le texte s'etend
    vers le haut. grow='down' : edge_y est le HAUT du bloc.
    """
    lines = _wrap_lines(draw, text, font, x1 - x0)
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    total_h = sum(line_heights) + line_spacing * (len(lines) - 1)

    cy = (edge_y - total_h) if grow == "up" else edge_y

    for line, lh in zip(lines, line_heights):
        cx = (x0 + x1) / 2
        draw.text((cx, cy + lh / 2), line, font=font, fill=fill, anchor="mm",
                   stroke_width=stroke_width, stroke_fill=stroke_fill, align="center")
        cy += lh + line_spacing


def cover_fit(image_path: str, box_w: int, box_h: int) -> Image.Image:
    img = Image.open(image_path).convert("RGB")
    return ImageOps.fit(img, (box_w, box_h), method=Image.LANCZOS, centering=(0.5, 0.35))


def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------------------
# Fond : deux couleurs complementaires, haut / bas
# ---------------------------------------------------------------------------

def build_stacked_base(width: int, height: int, top_color: str, bottom_color: str) -> Image.Image:
    canvas = Image.new("RGB", (width, height), (10, 10, 10))
    half_h = height // 2
    canvas.paste(Image.new("RGB", (width, half_h), _hex_to_rgb(top_color)), (0, 0))
    canvas.paste(Image.new("RGB", (width, height - half_h), _hex_to_rgb(bottom_color)), (0, half_h))
    return canvas


def divider_bounds(width: int, height: int):
    """y0, y1 de la barre centrale (epaisse, sert de piste de decompte)."""
    half_h = height // 2
    thickness = int(height * DIVIDER_THICKNESS_RATIO)
    return half_h - thickness // 2, half_h + thickness // 2


def draw_divider(canvas: Image.Image, progress: float, fill_color=(255, 214, 0)):
    """
    Dessine la piste de decompte + son remplissage gauche->droite (0..1),
    avec un contour blanc UNIQUEMENT en haut et en bas de la barre (pas sur
    les cotes gauche/droit). progress=0 -> piste entierement noire (avant le
    decompte), comme le badge VS.

    Le trait blanc est coupe exactement la ou le badge VS (dessine par-dessus
    ensuite) va le recouvrir, pour que le contour du badge soit la SEULE
    ligne visible a cet endroit (pas de "soudure"/double-trait).
    """
    width, height = canvas.size
    y0, y1 = divider_bounds(width, height)
    outline_w = max(2, int(width * OUTLINE_WIDTH_RATIO))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rectangle([0, y0, width, y1], fill=(0, 0, 0, 255))
    progress = max(0.0, min(1.0, progress))
    fill_w = int(width * progress)
    if fill_w > 0:
        draw.rectangle([0, y0, fill_w, y1], fill=fill_color + (255,))

    cx = width // 2
    r = int(width * VS_BADGE_RADIUS_RATIO)
    dy = (y1 - y0) / 2
    half_span = (r * r - dy * dy) ** 0.5 if r > dy else 0
    left_cut = int(cx - half_span)
    right_cut = int(cx + half_span)

    y_top = y0 + outline_w // 2
    y_bot = y1 - outline_w // 2
    if left_cut > 0:
        draw.line([(0, y_top), (left_cut, y_top)], fill=WHITE, width=outline_w)
        draw.line([(0, y_bot), (left_cut, y_bot)], fill=WHITE, width=outline_w)
    if right_cut < width:
        draw.line([(right_cut, y_top), (width, y_top)], fill=WHITE, width=outline_w)
        draw.line([(right_cut, y_bot), (width, y_bot)], fill=WHITE, width=outline_w)
    return canvas


def draw_free_vs_badge(canvas: Image.Image, font_path: str, cx: int, cy: int, r: int,
                        badge_text: str = "VS", outline_color=None, text_color=None,
                        outline_width_ratio: float = OUTLINE_WIDTH_RATIO):
    """
    Comme draw_vs_badge, mais a une position/taille libres (utilise pour le
    gros badge VS de l'ecran d'ouverture "carte de combat").
    """
    width, _ = canvas.size
    outline_w = max(2, int(width * outline_width_ratio))
    outline_color = outline_color or WHITE
    text_color = text_color or WHITE
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, 255),
                 outline=outline_color, width=outline_w)
    max_text_w = r * 1.4
    size = int(r * 1.0)
    font = load_font(font_path, size)
    while _text_w(draw, badge_text, font) > max_text_w and size > 10:
        size -= 2
        font = load_font(font_path, size)
    draw_centered_text(draw, (cx, cy + 2), badge_text, font, text_color)


def draw_vs_badge(canvas: Image.Image, font_path: str, badge_text: str = "VS",
                   outline_color=None, text_color=None):
    """
    Badge central : rond noir, contour + texte configurables (blanc par
    defaut ; jaune pendant/apres le decompte). Pose PAR-DESSUS la piste/le
    remplissage -> masque naturellement tout contour de la barre a cet
    endroit (pas de "soudure" visible, cf. draw_divider).
    """
    width, height = canvas.size
    half_h = height // 2
    r = int(width * VS_BADGE_RADIUS_RATIO)
    outline_w = max(2, int(width * OUTLINE_WIDTH_RATIO))
    cx, cy = width // 2, half_h
    outline_color = outline_color or WHITE
    text_color = text_color or WHITE
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, 255),
                 outline=outline_color, width=outline_w)

    # Texte "VS" (legerement plus petit que le rond, marge de securite)
    max_text_w = r * 1.4
    size = int(r * 1.0)
    font = load_font(font_path, size)
    while _text_w(draw, badge_text, font) > max_text_w and size > 10:
        size -= 2
        font = load_font(font_path, size)
    draw_centered_text(draw, (cx, cy + 2), badge_text, font, text_color)
    return canvas


def countdown_blink_color(t: float, on_color=GOLD, off_color=WHITE, hz: float = 3.0):
    """Couleur de contour du badge VS a l'instant t (clignotement pendant le decompte)."""
    return on_color if int(t * hz * 2) % 2 == 0 else off_color


# ---------------------------------------------------------------------------
# Cadre photo + legende. MEME dimension et MEME espacement depuis le centre
# pour les deux zones (symetrie stricte) ; seule la position de la legende
# change de cote (bord exterieur de l'ecran), rapprochee du cadre.
# ---------------------------------------------------------------------------

def _zone_span(width, height, zone):
    div_y0, div_y1 = divider_bounds(width, height)
    return (0, div_y0) if zone == "top" else (div_y1, height)


def frame_rect(width, height, zone):
    """(x0,y0,x1,y1) du cadre photo : meme taille/espacement pour top et bottom."""
    zy0, zy1 = _zone_span(width, height, zone)
    zone_h = zy1 - zy0
    frame_w = int(width * 0.94)
    frame_x0 = (width - frame_w) // 2
    gap = int(zone_h * FRAME_GAP_FROM_DIVIDER_RATIO)
    frame_h = int(zone_h * FRAME_H_RATIO)

    if zone == "top":
        frame_y1 = zy1 - gap          # cadre colle (a 'gap' pres) a la barre centrale
        frame_y0 = frame_y1 - frame_h
    else:
        frame_y0 = zy0 + gap          # meme 'gap' depuis la barre centrale
        frame_y1 = frame_y0 + frame_h

    return (frame_x0, frame_y0, frame_x0 + frame_w, frame_y1)


def _draw_frame_border(canvas: Image.Image, zone: str, border_color=WHITE):
    width, height = canvas.size
    x0, y0, x1, y1 = frame_rect(width, height, zone)
    fw = x1 - x0
    radius = int(fw * 0.06)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=border_color, width=5)


def add_photo_frame(canvas: Image.Image, photo_path: str, zone: str, border_color=WHITE):
    width, height = canvas.size
    x0, y0, x1, y1 = frame_rect(width, height, zone)
    fw, fh = x1 - x0, y1 - y0

    radius = int(fw * 0.06)
    photo = cover_fit(photo_path, fw, fh)

    mask = Image.new("L", (fw, fh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, fw, fh], radius=radius, fill=255)
    canvas.paste(photo, (x0, y0), mask)

    _draw_frame_border(canvas, zone, border_color)


def add_zone_caption(canvas: Image.Image, text: str, zone: str, font_path: str):
    """
    Nom de l'animal : place pres du centre (juste a l'exterieur du badge
    VS), donc pres de l'animal lui-meme -- plutot que pres du bord ecran,
    qui n'a presque plus de marge depuis que l'animal occupe la quasi
    totalite de la zone.
    """
    width, height = canvas.size
    div_y0, div_y1 = divider_bounds(width, height)
    cy = (div_y0 + div_y1) // 2
    vs_r = int(width * VS_BADGE_RADIUS_RATIO)
    clearance = vs_r + int(height * 0.018)

    draw = ImageDraw.Draw(canvas, "RGBA")
    font_size = int(width * 0.105)
    font = load_font(font_path, font_size)
    x0, x1 = int(width * 0.05), int(width * 0.95)

    if zone == "top":
        draw_wrapped_text_from_edge(draw, x0, x1, cy - clearance, text.upper(), font, WHITE,
                                     line_spacing=4, stroke_width=0, grow="up")
    else:
        draw_wrapped_text_from_edge(draw, x0, x1, cy + clearance, text.upper(), font, WHITE,
                                     line_spacing=4, stroke_width=0, grow="down")


# ---------------------------------------------------------------------------
# Resultat : gros pourcentage (contour blanc) tamponne dans la couleur de sa
# zone. Le perdant est assombri et le vainqueur clignote en jaune, mais ces
# deux effets s'appliquent directement sur la silhouette de l'animal (cf.
# tint_silhouette dans video_builder.py) -- plus de cadre a assombrir ici.
# ---------------------------------------------------------------------------

def draw_percentage_text(canvas: Image.Image, zone: str, pct: int, font_path: str, zone_color_hex: str):
    """Juste le gros pourcentage, en blanc plein, sans aucun contour."""
    width, height = canvas.size
    x0, y0, x1, y1 = frame_rect(width, height, zone)
    fw, fh = x1 - x0, y1 - y0
    draw = ImageDraw.Draw(canvas, "RGBA")
    font_size = int(fw * 0.40)
    font = load_font(font_path, font_size)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    draw_centered_text(draw, (cx, cy), f"{pct}%", font, WHITE, stroke_width=0)


def render_result_frame(duel_frame: Image.Image, pct_a: int, pct_b: int, font_bold_path: str,
                         top_color: str, bottom_color: str) -> Image.Image:
    canvas = duel_frame.copy()
    draw_percentage_text(canvas, "top", pct_a, font_bold_path, top_color)
    draw_percentage_text(canvas, "bottom", pct_b, font_bold_path, bottom_color)
    # Redessine le VS par-dessus (fige en jaune jusqu'au round suivant).
    draw_vs_badge(canvas, font_bold_path, outline_color=WHITE, text_color=GOLD)
    return canvas


# ---------------------------------------------------------------------------
# Reveal : la moitie du PERDANT garde sa couleur de fond mais perd sa photo
# et son nom, remplaces par le texte d'explication (MAJUSCULES, blanc/contour
# noir). Le badge VS est redessine par-dessus (toujours fige en jaune ici).
# ---------------------------------------------------------------------------

def build_explanation_base(result_img: Image.Image, loser_zone: str, loser_color_hex: str,
                            font_path: str) -> Image.Image:
    """Fond de la phase explication (zone du perdant en couleur unie, VS redessine), SANS texte."""
    canvas = result_img.copy()
    width, height = canvas.size
    zy0, zy1 = _zone_span(width, height, loser_zone)

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rectangle([0, zy0, width, zy1], fill=_hex_to_rgb(loser_color_hex) + (255,))

    # Le rectangle ci-dessus peut recouvrir le haut/bas du badge VS (qui
    # deborde legerement de la barre centrale) : on le redessine par-dessus.
    draw_vs_badge(canvas, font_path, outline_color=WHITE, text_color=GOLD)
    return canvas


def draw_caption_chunk(canvas: Image.Image, zone: str, text: str, font_path: str):
    """
    Sous-titre "auto-genere" : quelques mots a la fois, TRES gros, centres
    dans la zone du perdant (remplace l'ancien paragraphe fixe).
    """
    if not text:
        return
    width, height = canvas.size
    zy0, zy1 = _zone_span(width, height, zone)
    cy = (zy0 + zy1) // 2

    draw = ImageDraw.Draw(canvas, "RGBA")
    max_w = width * 0.86
    font_size = int(width * 0.16)
    font = load_font(font_path, font_size)
    while _text_w(draw, text, font) > max_w and font_size > 24:
        font_size -= 4
        font = load_font(font_path, font_size)

    draw_centered_text(draw, (width // 2, cy), text, font, WHITE, stroke_width=0)



# ---------------------------------------------------------------------------
# Petite transition d'entree entre chaque round : la scene (fond + VS) fait
# un leger zoom-in en fondu depuis le noir, plutot qu'un cut sec.
# ---------------------------------------------------------------------------

def build_round_transition_frame(stage_img: Image.Image, progress: float) -> Image.Image:
    width, height = stage_img.size
    progress = max(0.0, min(1.0, progress))
    eased = 1 - (1 - progress) ** 3  # ease-out : demarre vite, ralentit en fin

    scale = 0.90 + 0.10 * eased
    scaled_w, scaled_h = max(1, int(width * scale)), max(1, int(height * scale))
    scaled = stage_img.resize((scaled_w, scaled_h), Image.LANCZOS)

    canvas = Image.new("RGB", (width, height), (0, 0, 0))
    x0 = (width - scaled_w) // 2
    y0 = (height - scaled_h) // 2
    canvas.paste(scaled, (x0, y0))

    if eased < 1.0:
        black = Image.new("RGB", (width, height), (0, 0, 0))
        canvas = Image.blend(black, canvas, eased)
    return canvas


# ---------------------------------------------------------------------------
# Sequence d'ouverture de la video (une seule fois, au tout debut) : titre
# en haut + miniatures de tous les animaux qui apparaissent une a une,
# empilees en vrac en bas de l'ecran.
# ---------------------------------------------------------------------------

def build_opening_base(width: int, height: int, bg_color_hex: str = None,
                        bg_image_path: str = None) -> Image.Image:
    if bg_image_path and os.path.exists(bg_image_path):
        canvas = cover_fit(bg_image_path, width, height).convert("RGBA")
        # Leger voile sombre en haut (sous le titre) pour garder le texte lisible
        # quelle que soit l'image fournie par l'utilisateur.
        scrim_h = int(height * 0.30)
        alpha_col = np.linspace(150, 0, scrim_h).astype("uint8")
        overlay_arr = np.zeros((height, width, 4), dtype="uint8")
        overlay_arr[:scrim_h, :, 3] = alpha_col[:, None]
        overlay = Image.fromarray(overlay_arr, "RGBA")
        canvas.alpha_composite(overlay)
        return canvas.convert("RGB")
    return Image.new("RGB", (width, height), _hex_to_rgb(bg_color_hex or "#202020"))


def add_opening_title(canvas: Image.Image, font_path: str, logo_path: str = None):
    """
    Titre de l'ecran d'ouverture : le logo utilisateur (PNG 16:9), agrandi
    et place plus bas (a l'endroit ou etait l'ancien sous-titre texte, qui
    a ete supprime) ; ou a defaut le texte "DUELS D'ANIMAUX" en haut.
    """
    width, height = canvas.size
    draw = ImageDraw.Draw(canvas, "RGBA")

    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        # ~x1.3 plus grand qu'avant (plafonne pour ne jamais deborder du cadre).
        logo_w = min(int(width * 0.95), int(width * 0.82 * 1.3))
        logo_h = int(logo_w * 9 / 16)
        logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)
        x0 = (width - logo_w) // 2
        y0 = int(height * 0.16)  # plus bas : a la place de l'ancien sous-titre
        canvas.paste(logo_resized, (x0, y0), logo_resized)
    else:
        title_size = int(width * 0.105)
        font_title = load_font(font_path, title_size)
        draw_wrapped_text(draw, (int(width * 0.05), int(height * 0.10), int(width * 0.95), int(height * 0.22)),
                           "DUELS D'ANIMAUX", font_title, WHITE, line_spacing=6,
                           stroke_width=_text_stroke_width(title_size), stroke_fill=BLACK)


# ---------------------------------------------------------------------------
# Animation d'entree des photos (pendant l'intro) : le cadre grossit et
# apparait en fondu depuis son centre final, plutot qu'un "pop" instantane.
# ---------------------------------------------------------------------------

def add_photo_frame_animated(canvas: Image.Image, photo_path: str, zone: str, progress: float):
    """progress 0..1 : 0 = invisible, 1 = cadre final (taille/opacite pleines)."""
    progress = max(0.0, min(1.0, progress))
    eased = 1 - (1 - progress) ** 3  # ease-out
    width, height = canvas.size
    x0, y0, x1, y1 = frame_rect(width, height, zone)
    fw, fh = x1 - x0, y1 - y0

    scale = 0.55 + 0.45 * eased
    alpha = int(255 * eased)
    cur_w, cur_h = max(1, int(fw * scale)), max(1, int(fh * scale))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    cur_x0, cur_y0 = cx - cur_w // 2, cy - cur_h // 2

    radius = int(cur_w * 0.06)
    photo = cover_fit(photo_path, cur_w, cur_h)
    mask = Image.new("L", (cur_w, cur_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, cur_w, cur_h], radius=radius, fill=alpha)
    canvas.paste(photo, (cur_x0, cur_y0), mask)

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle([cur_x0, cur_y0, cur_x0 + cur_w, cur_y0 + cur_h], radius=radius,
                            outline=(255, 255, 255, alpha), width=5)


# ---------------------------------------------------------------------------
# Animation de sortie (fin de manche) : une zone (photo+legende ou texte
# d'explication) se fond progressivement dans la couleur unie de son fond,
# pour preparer une transition propre vers le round suivant.
# ---------------------------------------------------------------------------

def add_zone_exit_fade(canvas: Image.Image, zone: str, zone_color_hex: str, alpha: float):
    """alpha 0..1 : 0 = zone inchangee, 1 = entierement fondue en couleur unie."""
    if alpha <= 0:
        return
    alpha = min(1.0, alpha)
    width, height = canvas.size
    zy0, zy1 = _zone_span(width, height, zone)
    region = canvas.crop((0, zy0, width, zy1)).convert("RGB")
    flat = Image.new("RGB", region.size, _hex_to_rgb(zone_color_hex))
    blended = Image.blend(region, flat, alpha)
    canvas.paste(blended, (0, zy0))


# ---------------------------------------------------------------------------
# Transition de fin de manche : le VS et la barre centrale tournent sur eux-
# memes (360°) pour "balayer" les couleurs de la manche qui se termine et
# devoiler celles de la manche suivante.
# ---------------------------------------------------------------------------

def build_sweep_transition_frame(old_top_hex: str, old_bottom_hex: str,
                                  new_top_hex: str, new_bottom_hex: str,
                                  width: int, height: int, progress: float,
                                  font_path: str) -> Image.Image:
    progress = max(0.0, min(1.0, progress))
    angle_deg = progress * 360.0
    cx, cy = width // 2, height // 2

    old_img = Image.new("RGB", (width, height))
    old_img.paste(Image.new("RGB", (width, height // 2), _hex_to_rgb(old_top_hex)), (0, 0))
    old_img.paste(Image.new("RGB", (width, height - height // 2), _hex_to_rgb(old_bottom_hex)), (0, height // 2))

    new_img = Image.new("RGB", (width, height))
    new_img.paste(Image.new("RGB", (width, height // 2), _hex_to_rgb(new_top_hex)), (0, 0))
    new_img.paste(Image.new("RGB", (width, height - height // 2), _hex_to_rgb(new_bottom_hex)), (0, height // 2))

    yy, xx = np.mgrid[0:height, 0:width]
    angles = np.degrees(np.arctan2(yy - cy, xx - cx)) % 360.0  # 0° = horizontale (a droite), sens horaire
    mask = angles < angle_deg

    old_arr = np.array(old_img)
    new_arr = np.array(new_img)
    result_arr = np.where(mask[..., None], new_arr, old_arr).astype("uint8")
    canvas = Image.fromarray(result_arr)

    # Le VS et toute la barre horizontale (meme sprite que l'etat de repos)
    # tournent ensemble, comme un seul bloc, au meme rythme que le balayage
    # des couleurs -> l'ensemble donne l'impression d'un seul objet qui
    # pivote et "essuie" l'ancienne couleur pour reveler la suivante.
    # Le sprite (barre + VS) est dessine sur un canevas PLUS GRAND que
    # l'ecran final (au moins la diagonale), sinon la barre est tronquee
    # aux bords AVANT meme la rotation (un canevas de la taille de l'ecran
    # ne peut pas contenir une barre plus longue que sa propre largeur). On
    # recadre ensuite la zone centrale correspondant a l'ecran final.
    diag = int((width ** 2 + height ** 2) ** 0.5)
    big = diag + 60
    scx, scy = big // 2, big // 2

    sprite = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    y0, y1 = divider_bounds(width, height)
    thickness = y1 - y0
    outline_w = max(2, int(width * OUTLINE_WIDTH_RATIO))
    sdraw = ImageDraw.Draw(sprite, "RGBA")
    bar_x0, bar_x1 = scx - diag // 2, scx + diag // 2
    bar_y0, bar_y1 = scy - thickness // 2, scy + thickness // 2
    sdraw.rectangle([bar_x0, bar_y0, bar_x1, bar_y1], fill=(0, 0, 0, 255))
    sdraw.line([(bar_x0, bar_y0 + outline_w // 2), (bar_x1, bar_y0 + outline_w // 2)], fill=WHITE, width=outline_w)
    sdraw.line([(bar_x0, bar_y1 - outline_w // 2), (bar_x1, bar_y1 - outline_w // 2)], fill=WHITE, width=outline_w)

    # Le badge VS doit garder sa taille normale (basee sur la largeur de
    # l'ecran final, pas sur le grand canevas du sprite) : on le dessine a
    # part sur un calque aux dimensions d'origine, puis on le colle au
    # centre du sprite.
    vs_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_vs_badge(vs_layer, font_path)
    sprite.alpha_composite(vs_layer, (scx - width // 2, scy - height // 2))

    # PIL Image.rotate() est anti-horaire pour un angle positif : on inverse
    # le signe pour tourner dans le meme sens horaire que le balayage.
    rotated = sprite.rotate(-angle_deg, resample=Image.BICUBIC, center=(scx, scy))
    left, top = scx - width // 2, scy - height // 2
    cropped = rotated.crop((left, top, left + width, top + height))

    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(cropped)
    canvas = canvas.convert("RGB")
    return canvas


def paste_thumbnail(canvas: Image.Image, photo_path: str, cx: int, cy: int, size: int,
                     border_color=WHITE):
    if size < 6:
        return
    thumb = cover_fit(photo_path, size, size)
    radius = int(size * 0.14)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    x0, y0 = int(cx - size / 2), int(cy - size / 2)
    canvas.paste(thumb, (x0, y0), mask)
    if border_color is not None:
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rounded_rectangle([x0, y0, x0 + size, y0 + size], radius=radius,
                                outline=border_color, width=max(3, int(size * 0.035)))


def tint_silhouette(cutout_img, color_rgb, amount: float):
    """
    Teinte un animal deja detoure (PIL RGBA) vers 'color_rgb' (0 = couleurs
    d'origine, 1 = entierement 'color_rgb'), en conservant sa silhouette
    (canal alpha) intacte. Utilise pour assombrir le perdant ou faire
    clignoter le vainqueur en jaune au moment du resultat.
    """
    if cutout_img is None or amount <= 0:
        return cutout_img
    amount = min(1.0, amount)
    r, g, b, a = cutout_img.split()
    rgb = Image.merge("RGB", (r, g, b))
    tint_layer = Image.new("RGB", cutout_img.size, color_rgb)
    blended = Image.blend(rgb, tint_layer, amount)
    br, bgc, bb = blended.split()
    return Image.merge("RGBA", (br, bgc, bb, a))


def add_cutout_outline(cutout_img, thickness: int = 3, color=(255, 255, 255, 255)):
    """
    Ajoute un leger contour uni (blanc par defaut) qui suit la silhouette
    d'un animal deja detoure (PIL RGBA), en dilatant son canal alpha.
    Rajoute d'abord une marge transparente (sinon le contour serait tronque
    si le sujet touche deja le bord de son image d'origine). Renvoie une
    NOUVELLE image, legerement plus grande que l'original.
    """
    if cutout_img is None:
        return None
    pad = thickness + 2
    padded = ImageOps.expand(cutout_img, border=pad, fill=(0, 0, 0, 0))
    r, g, b, a = padded.split()
    kernel = max(3, thickness * 2 + 1)
    if kernel % 2 == 0:
        kernel += 1
    dilated = a.filter(ImageFilter.MaxFilter(kernel))
    ring_alpha = ImageChops.subtract(dilated, a)

    outline_layer = Image.new("RGBA", padded.size, color[:3] + (0,))
    outline_layer.putalpha(ring_alpha)

    return Image.alpha_composite(outline_layer, padded)


def _ease_out_back(t: float, overshoot: float = 1.6) -> float:
    """Easing avec leger rebond : depasse 1.0 juste avant de s'y stabiliser."""
    t = max(0.0, min(1.0, t))
    c1 = overshoot
    c3 = c1 + 1
    tm1 = t - 1
    return 1 + c3 * (tm1 ** 3) + c1 * (tm1 ** 2)


def paste_cutout_in_box(canvas: Image.Image, cutout_img, box, progress: float = 1.0):
    """
    Colle un animal deja detoure (PIL RGBA, avec ou sans contour) dans une
    boite (x0, y0, x1, y1), a l'echelle MAXIMALE qui y tient sans deborder
    (ni trop gros, ni trop petit, quel que soit le format d'origine de
    l'image), centre. progress 0..1 anime une apparition avec un leger
    effet de rebond ("il arrive un peu trop grand puis se stabilise").
    """
    if cutout_img is None:
        return
    progress = max(0.0, min(1.0, progress))
    if progress <= 0:
        return
    alpha_eased = 1 - (1 - progress) ** 3
    scale_eased = _ease_out_back(progress)

    x0, y0, x1, y1 = box
    box_w, box_h = x1 - x0, y1 - y0
    box_cx, box_cy = (x0 + x1) // 2, (y0 + y1) // 2

    cw, ch = cutout_img.size
    scale = min(box_w / cw, box_h / ch)
    tw, th = max(1, int(cw * scale)), max(1, int(ch * scale))

    cur_scale = max(0.05, 0.55 + 0.45 * scale_eased)
    cur_w, cur_h = max(1, int(tw * cur_scale)), max(1, int(th * cur_scale))
    resized = cutout_img.resize((cur_w, cur_h), Image.LANCZOS)

    if alpha_eased < 1.0:
        r, g, b, a = resized.split()
        a = a.point(lambda v: int(v * alpha_eased))
        resized = Image.merge("RGBA", (r, g, b, a))

    x = box_cx - cur_w // 2
    y = box_cy - cur_h // 2
    canvas.paste(resized, (x, y), resized)


def add_animal_silhouette(canvas: Image.Image, cutout_img, zone: str, progress: float = 1.0):
    """Comme paste_cutout_in_box, mais utilise directement la boite standard d'une zone (haut/bas)."""
    width, height = canvas.size
    box = frame_rect(width, height, zone)
    paste_cutout_in_box(canvas, cutout_img, box, progress=progress)


def paste_cutout_thumbnail(canvas: Image.Image, cutout_img, cx: int, cy: int, max_size: int,
                            progress: float = 1.0):
    """
    Comme paste_thumbnail, mais pour un animal deja detoure (PIL RGBA, fond
    transparent) : mis a l'echelle pour tenir dans un carre max_size x
    max_size (silhouette entiere, sans recadrage ni bordure), centre sur
    (cx, cy). progress 0..1 anime une apparition (grossit + fondu).
    """
    if cutout_img is None or max_size < 6:
        return
    progress = max(0.0, min(1.0, progress))
    if progress <= 0:
        return
    eased = 1 - (1 - progress) ** 3

    cw, ch = cutout_img.size
    scale = min(max_size / cw, max_size / ch)
    tw, th = max(1, int(cw * scale)), max(1, int(ch * scale))
    resized = cutout_img.resize((tw, th), Image.LANCZOS)

    cur_scale = 0.6 + 0.4 * eased
    cur_w, cur_h = max(1, int(tw * cur_scale)), max(1, int(th * cur_scale))
    if cur_scale != 1.0:
        resized = resized.resize((cur_w, cur_h), Image.LANCZOS)

    if eased < 1.0:
        r, g, b, a = resized.split()
        a = a.point(lambda v: int(v * eased))
        resized = Image.merge("RGBA", (r, g, b, a))

    x0, y0 = cx - cur_w // 2, cy - cur_h // 2
    canvas.paste(resized, (x0, y0), resized)


# ---------------------------------------------------------------------------
# Petit flash dore sur le cadre du VAINQUEUR au moment exact du reveal, pour
# marquer le climax (intensity : 1.0 = flash maximal, 0.0 = invisible).
# ---------------------------------------------------------------------------

def add_winner_flash(canvas: Image.Image, winner_zone: str, intensity: float):
    if intensity <= 0:
        return
    intensity = max(0.0, min(1.0, intensity))
    width, height = canvas.size
    x0, y0, x1, y1 = frame_rect(width, height, winner_zone)
    fw, fh = x1 - x0, y1 - y0
    radius = int(fw * 0.06)

    overlay_alpha = int(130 * intensity)
    if overlay_alpha > 0:
        mask = Image.new("L", (fw, fh), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, fw, fh], radius=radius, fill=overlay_alpha)
        gold_fill = Image.new("RGB", (fw, fh), (255, 214, 0))
        canvas.paste(gold_fill, (x0, y0), mask)

    draw = ImageDraw.Draw(canvas, "RGBA")
    border_w = int(4 + 8 * intensity)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=GOLD, width=border_w)


# ---------------------------------------------------------------------------
# Ecran de fin (CTA) : fond de couleur aleatoire, texte centre, grand et bien
# visible.
# ---------------------------------------------------------------------------

def build_ending_base(width: int, height: int, bg_color_hex: str, text: str, font_path: str) -> Image.Image:
    canvas = Image.new("RGB", (width, height), _hex_to_rgb(bg_color_hex))
    draw = ImageDraw.Draw(canvas, "RGBA")
    font_size = int(width * 0.078)
    font = load_font(font_path, font_size)
    draw_wrapped_text(draw, (int(width * 0.08), int(height * 0.22), int(width * 0.92), int(height * 0.78)),
                       text.upper(), font, WHITE, line_spacing=10,
                       stroke_width=_text_stroke_width(font_size), stroke_fill=BLACK)
    return canvas


# ---------------------------------------------------------------------------
# Barre de progression discrete (fine ligne en haut de l'ecran), pour
# rassurer inconsciemment le spectateur qu'il reste du contenu.
# ---------------------------------------------------------------------------

def draw_progress_bar(canvas: Image.Image, progress: float, color=GOLD):
    progress = max(0.0, min(1.0, progress))
    width, height = canvas.size
    bar_h = max(3, int(height * 0.0026))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rectangle([0, 0, width, bar_h], fill=(255, 255, 255, 60))
    fill_w = int(width * progress)
    if fill_w > 0:
        draw.rectangle([0, 0, fill_w, bar_h], fill=color)


# ---------------------------------------------------------------------------
# Ecran d'ouverture "carte de combat" (hook) : les deux animaux du duel
# phare en portraits circulaires, gros badge VS, tampon "DUEL N°X", fond
# sombre et dramatique.
# ---------------------------------------------------------------------------

def build_hook_base(width: int, height: int, bg_color_hex: str) -> Image.Image:
    return Image.new("RGB", (width, height), _hex_to_rgb(bg_color_hex))


def add_impact_lines(canvas: Image.Image, cx: int, cy: int, radius: int, color=(255, 214, 0, 90), count: int = 16):
    """Fines lignes qui rayonnent depuis le centre, pour donner de l'energie au badge VS."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    for i in range(count):
        angle = (2 * math.pi / count) * i
        inner = radius * 1.15
        outer = radius * 1.85
        x1, y1 = cx + math.cos(angle) * inner, cy + math.sin(angle) * inner
        x2, y2 = cx + math.cos(angle) * outer, cy + math.sin(angle) * outer
        draw.line([(x1, y1), (x2, y2)], fill=color, width=max(2, int(radius * 0.035)))


def add_circular_portrait(canvas: Image.Image, photo_path: str, cx: int, cy: int, radius: int,
                           progress: float = 1.0, border_color=WHITE):
    """progress 0..1 : le portrait grossit et apparait en fondu (meme logique que les cadres de round)."""
    progress = max(0.0, min(1.0, progress))
    if progress <= 0:
        return
    eased = 1 - (1 - progress) ** 3
    cur_r = max(1, int(radius * (0.55 + 0.45 * eased)))
    alpha = int(255 * eased)

    size = cur_r * 2
    photo = cover_fit(photo_path, size, size)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=alpha)
    canvas.paste(photo, (cx - cur_r, cy - cur_r), mask)

    draw = ImageDraw.Draw(canvas, "RGBA")
    outline_w = max(4, int(radius * 0.05))
    border = border_color[:3] + (alpha,) if len(border_color) == 4 else border_color
    draw.ellipse([cx - cur_r, cy - cur_r, cx + cur_r, cy + cur_r], outline=border, width=outline_w)


def add_duel_stamp(canvas: Image.Image, duel_number: int, font_path: str):
    """Tampon "DUEL N°X" legerement incline, en haut de l'ecran (comme un carton de ring)."""
    width, height = canvas.size
    stamp_w, stamp_h = int(width * 0.62), int(height * 0.075)
    stamp = Image.new("RGBA", (stamp_w, stamp_h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(stamp, "RGBA")
    sdraw.rounded_rectangle([0, 0, stamp_w, stamp_h], radius=int(stamp_h * 0.28),
                             fill=GOLD, outline=BLACK, width=max(3, int(stamp_h * 0.06)))
    font = load_font(font_path, int(stamp_h * 0.6))
    draw_centered_text(sdraw, (stamp_w // 2, stamp_h // 2 + 2), f"DUEL N°{duel_number}", font, BLACK)

    rotated = stamp.rotate(-6, resample=Image.BICUBIC, expand=True)
    x0 = (width - rotated.width) // 2
    y0 = int(height * 0.045)
    canvas.paste(rotated, (x0, y0), rotated)


# ---------------------------------------------------------------------------
# Fond "carte de combat" façon affiche boxe/MMA : degrade feu radial +
# rayons de lumiere, pour l'ecran d'ouverture avec animaux detoures.
# ---------------------------------------------------------------------------

def build_fire_gradient_base(width: int, height: int) -> Image.Image:
    """Degrade radial dramatique (centre clair orange/jaune -> bords sombres rouge/noir)."""
    cx, cy = width // 2, height // 2
    max_dist = (cx ** 2 + cy ** 2) ** 0.5

    yy, xx = np.mgrid[0:height, 0:width]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max_dist  # 0 au centre, 1 aux coins

    # Points de degrade : centre (clair, chaud) -> milieu (orange/rouge) -> bord (sombre)
    stops = [
        (0.00, (255, 214, 120)),
        (0.35, (235, 110, 40)),
        (0.70, (120, 30, 20)),
        (1.00, (18, 8, 10)),
    ]
    r = np.zeros((height, width), dtype=np.float32)
    g = np.zeros((height, width), dtype=np.float32)
    b = np.zeros((height, width), dtype=np.float32)
    for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
        mask = (dist >= p0) & (dist <= p1)
        local = np.clip((dist - p0) / max(1e-6, (p1 - p0)), 0, 1)
        r[mask] = c0[0] + (c1[0] - c0[0]) * local[mask]
        g[mask] = c0[1] + (c1[1] - c0[1]) * local[mask]
        b[mask] = c0[2] + (c1[2] - c0[2]) * local[mask]

    arr = np.stack([r, g, b], axis=-1).astype("uint8")
    return Image.fromarray(arr, mode="RGB")


def add_light_rays(canvas: Image.Image, cx: int, cy: int, count: int = 24,
                    color=(255, 200, 90, 45)):
    """Rayons de lumiere larges partant du centre (effet "sunburst" façon carte de combat)."""
    width, height = canvas.size
    max_len = int((width ** 2 + height ** 2) ** 0.5)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    for i in range(count):
        angle = (2 * math.pi / count) * i
        half_spread = math.pi / count * 0.35
        pts = [
            (cx, cy),
            (cx + math.cos(angle - half_spread) * max_len, cy + math.sin(angle - half_spread) * max_len),
            (cx + math.cos(angle + half_spread) * max_len, cy + math.sin(angle + half_spread) * max_len),
        ]
        odraw.polygon(pts, fill=color)
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.alpha_composite(overlay)
    canvas.paste(canvas_rgba.convert("RGB"), (0, 0))


def add_cutout_figure(canvas: Image.Image, cutout_img, cx: int, bottom_y: int, max_height: int,
                       progress: float = 1.0, flip: bool = False):
    """
    Colle un animal deja detoure (PIL RGBA), mis a l'echelle pour tenir dans
    'max_height', centre horizontalement sur cx, aligne par le bas sur
    bottom_y. progress 0..1 anime une apparition (grossit + fondu).
    """
    if cutout_img is None or max_height <= 0:
        return
    progress = max(0.0, min(1.0, progress))
    if progress <= 0:
        return
    eased = 1 - (1 - progress) ** 3

    cw, ch = cutout_img.size
    scale = max_height / ch
    tw, th = max(1, int(cw * scale)), max(1, int(ch * scale))
    resized = cutout_img.resize((tw, th), Image.LANCZOS)
    if flip:
        resized = resized.transpose(Image.FLIP_LEFT_RIGHT)

    # Anime en fondu (alpha globale) + leger scale-in depuis le bas
    cur_scale = 0.85 + 0.15 * eased
    cur_w, cur_h = max(1, int(tw * cur_scale)), max(1, int(th * cur_scale))
    if cur_scale != 1.0:
        resized = resized.resize((cur_w, cur_h), Image.LANCZOS)

    if eased < 1.0:
        r, g, b, a = resized.split()
        a = a.point(lambda v: int(v * eased))
        resized = Image.merge("RGBA", (r, g, b, a))

    x0 = cx - cur_w // 2
    y0 = bottom_y - cur_h
    canvas.paste(resized, (x0, y0), resized)


# ---------------------------------------------------------------------------
# Ecran d'ouverture v2 : fond "coin de ring" bleu vs rouge, texte en degrade
# de couleur (façon affiches de boxe pro), tampon plus travaille.
# ---------------------------------------------------------------------------

def build_corner_gradient_base(width: int, height: int,
                                top_color=(20, 70, 200), bottom_color=(190, 25, 20)) -> Image.Image:
    """
    Fond "coin bleu vs coin rouge" : degrade vertical (bleu en haut, rouge en
    bas, transition resserree pres du centre) + vignette radiale sombre vers
    les bords pour la profondeur.
    """
    yy, xx = np.mgrid[0:height, 0:width]
    vert = yy / height
    blend = np.clip((vert - 0.32) / 0.36, 0, 1)

    top_c = np.array(top_color, dtype=np.float32)
    bot_c = np.array(bottom_color, dtype=np.float32)
    base = top_c[None, None, :] * (1 - blend[..., None]) + bot_c[None, None, :] * blend[..., None]

    cx, cy = width / 2, height / 2
    dist = np.sqrt(((xx - cx) / width) ** 2 + ((yy - cy) / height) ** 2)
    vignette = np.clip(1.0 - dist * 0.9, 0.35, 1.0)

    arr = np.clip(base * vignette[..., None], 0, 255).astype("uint8")
    return Image.fromarray(arr, mode="RGB")


def draw_gradient_text(canvas: Image.Image, center, text: str, font,
                        color_top, color_bottom, stroke_width: int = 8, stroke_fill=BLACK):
    """
    Texte dont le remplissage degrade verticalement de color_top a
    color_bottom (ex. bleu clair -> bleu fonce), avec un contour uni epais
    (façon lettrage d'affiche de boxe).
    """
    draw = ImageDraw.Draw(canvas, "RGBA")
    cx, cy = center

    # 1) silhouette uniforme (contour + remplissage) dans la couleur du
    #    contour -> sert de base/contour epais net, sans trous.
    draw.text((cx, cy), text, font=font, fill=stroke_fill, anchor="mm",
              stroke_width=stroke_width, stroke_fill=stroke_fill)

    # 2) masque = juste la forme des lettres (sans le contour), pour reveler
    #    un degrade colore par-dessus la silhouette.
    bbox = draw.textbbox((cx, cy), text, font=font, anchor="mm")
    x0, y0, x1, y1 = bbox
    pad = 2
    tw, th = max(1, (x1 - x0) + pad * 2), max(1, (y1 - y0) + pad * 2)

    mask = Image.new("L", (tw, th), 0)
    mdraw = ImageDraw.Draw(mask)
    # Meme ancrage ("mm", centre) que pour le bbox ci-dessus, afin que le
    # texte du masque tombe EXACTEMENT a la meme position que la silhouette
    # (sinon les deux calques se decalent legerement -> effet fantome).
    mdraw.text((tw // 2, th // 2), text, font=font, fill=255, anchor="mm")

    grad_col = np.linspace(np.array(color_top, dtype=np.float32),
                            np.array(color_bottom, dtype=np.float32), th)
    grad_arr = np.tile(grad_col[:, None, :], (1, tw, 1)).astype("uint8")
    grad_img = Image.fromarray(grad_arr, mode="RGB")

    canvas.paste(grad_img, (x0 - pad, y0 - pad), mask)


def add_duel_stamp_v2(canvas: Image.Image, duel_number: int, font_path: str):
    """
    Tampon "DUEL N°X" plus travaille : ruban bicolore (moitie bleue, moitie
    rouge) avec liseres blancs, legerement incline (comme un carton de
    ring pro).
    """
    width, height = canvas.size
    stamp_w, stamp_h = int(width * 0.68), int(height * 0.068)
    stamp = Image.new("RGBA", (stamp_w, stamp_h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(stamp, "RGBA")
    radius = int(stamp_h * 0.22)

    sdraw.rounded_rectangle([0, 0, stamp_w, stamp_h], radius=radius, fill=(15, 15, 20, 255))
    half = stamp_w // 2
    sdraw.rectangle([0, 0, half, stamp_h], fill=(20, 70, 200, 255))
    sdraw.rectangle([half, 0, stamp_w, stamp_h], fill=(190, 25, 20, 255))
    border_w = max(3, int(stamp_h * 0.07))
    sdraw.rounded_rectangle([0, 0, stamp_w, stamp_h], radius=radius, outline=WHITE, width=border_w)

    font = load_font(font_path, int(stamp_h * 0.62))
    draw_centered_text(sdraw, (stamp_w // 2, stamp_h // 2 + 2), f"DUEL N°{duel_number}", font, WHITE,
                        stroke_width=max(2, int(stamp_h * 0.05)), stroke_fill=BLACK)

    rotated = stamp.rotate(-5, resample=Image.BICUBIC, expand=True)
    x0 = (width - rotated.width) // 2
    y0 = int(height * 0.035)
    canvas.paste(rotated, (x0, y0), rotated)


def apply_punch_zoom(frame_img: Image.Image, intensity: float) -> Image.Image:
    """
    Leger "punch-in" (zoom bref centre) pour marquer le choc au moment ou
    les deux animaux se retrouvent enfin ensemble a l'ecran.
    intensity 0..1 : 0 = image inchangee, 1 = zoom maximal.
    """
    intensity = max(0.0, min(1.0, intensity))
    if intensity <= 0:
        return frame_img
    w, h = frame_img.size
    scale = 1 + 0.06 * intensity
    zw, zh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = frame_img.resize((zw, zh), Image.LANCZOS)
    x0 = (zw - w) // 2
    y0 = (zh - h) // 2
    return resized.crop((x0, y0, x0 + w, y0 + h))
