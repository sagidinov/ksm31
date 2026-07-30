#!/usr/bin/env python3
"""Generate Ozon product cards for Kubik — hero dog seeking a home."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = Path("/workspace")
SRC = ROOT / "source-photos"
OUT = ROOT / "cards"
FONT = ROOT / "fonts" / "Onest-Variable.ttf"

W, H = 1200, 1600  # Ozon 3:4

# Visual system — forest teal + warm coral (not purple, not cream/terracotta)
C = {
    "deep": (15, 42, 46),
    "deep2": (22, 58, 62),
    "sage": (216, 232, 224),
    "mint": (95, 191, 176),
    "coral": (255, 107, 90),
    "coral_d": (220, 78, 64),
    "sand": (245, 247, 244),
    "ink": (18, 32, 36),
    "muted": (90, 110, 112),
    "white": (255, 255, 255),
    "panel": (255, 255, 255),
}


def font(size: int, weight: int = 700) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_axes([weight])
    return f


def round_rect(draw, xy, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


# Relative subject centers in source photos (dog body), after letterbox trim
FOCUS = {
    "01-outdoor-portrait.jpg": (0.45, 0.62),
    "02-outdoor-yard.jpg": (0.45, 0.60),
    "03-recovered-brace.jpg": (0.52, 0.50),
    "04-soft-portrait.jpg": (0.50, 0.62),
    "05-recovery-bandages.jpg": (0.50, 0.52),
    "06-recovery-crate.jpg": (0.48, 0.52),
    "07-emergency.jpg": (0.50, 0.55),
}

# Keep zoom near 1.0 so the whole dog stays in frame
ZOOM = {
    "01-outdoor-portrait.jpg": 1.02,
    "02-outdoor-yard.jpg": 1.02,
    "03-recovered-brace.jpg": 1.0,
    "04-soft-portrait.jpg": 1.02,
    "05-recovery-bandages.jpg": 1.05,
    "06-recovery-crate.jpg": 1.05,
    "07-emergency.jpg": 1.0,
}


def trim_letterbox(img: Image.Image, threshold: int = 14) -> Image.Image:
    """Remove near-black letterbox bars common in phone exports."""
    arr = img.convert("RGB")
    px = arr.load()
    w, h = arr.size
    def row_bright(y):
        return sum(sum(px[x, y]) for x in range(0, w, max(1, w // 40))) / (3 * (w // max(1, w // 40) + 1))
    def col_bright(x):
        return sum(sum(px[x, y]) for y in range(0, h, max(1, h // 40))) / (3 * (h // max(1, h // 40) + 1))
    top = 0
    while top < h - 1 and row_bright(top) < threshold:
        top += 1
    bottom = h - 1
    while bottom > top and row_bright(bottom) < threshold:
        bottom -= 1
    left = 0
    while left < w - 1 and col_bright(left) < threshold:
        left += 1
    right = w - 1
    while right > left and col_bright(right) < threshold:
        right -= 1
    if bottom - top < h * 0.5 or right - left < w * 0.5:
        return img  # safety
    return img.crop((left, top, right + 1, bottom + 1))


def fit_cover(
    img: Image.Image,
    size: tuple[int, int],
    focus=(0.5, 0.5),
    zoom: float = 1.0,
) -> Image.Image:
    """Crop/scale so `focus` (x,y in source 0..1) lands at the center of the output."""
    tw, th = size
    img = trim_letterbox(img.convert("RGB"))
    sw, sh = img.size
    scale = max(tw / sw, th / sh) * max(zoom, 1.0)
    nw, nh = max(tw, int(sw * scale + 0.5)), max(th, int(sh * scale + 0.5))
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    cx, cy = focus[0] * nw, focus[1] * nh
    left = int(round(cx - tw / 2))
    top = int(round(cy - th / 2))
    left = max(0, min(left, nw - tw))
    top = max(0, min(top, nh - th))
    return img.crop((left, top, left + tw, top + th))


def fit_contain(
    img: Image.Image,
    size: tuple[int, int],
    focus=(0.5, 0.5),
    pad: float = 0.06,
    bg_mode: str = "blur",
    valign: str = "center",
) -> Image.Image:
    """Fit the whole photo inside the box (dog fully visible), fill margins with blur/solid."""
    tw, th = size
    img = trim_letterbox(img.convert("RGB"))
    sw, sh = img.size
    scale = min(tw / sw, th / sh) * (1.0 - pad)
    nw, nh = max(1, int(sw * scale + 0.5)), max(1, int(sh * scale + 0.5))
    subject = img.resize((nw, nh), Image.Resampling.LANCZOS)

    if bg_mode == "blur":
        bg = fit_cover(img, size, focus=focus, zoom=1.12)
        bg = bg.filter(ImageFilter.GaussianBlur(28))
        bg = ImageEnhance.Brightness(bg).enhance(0.72)
        bg = ImageEnhance.Color(bg).enhance(0.85)
    elif bg_mode == "sand":
        bg = Image.new("RGB", size, C["sand"])
    else:
        bg = Image.new("RGB", size, C["deep"])

    out = bg.copy()
    ox = int((tw - nw) * focus[0])
    if valign == "top":
        oy = int(th * 0.04)
    elif valign == "bottom":
        oy = th - nh - int(th * 0.04)
    else:
        oy = int((th - nh) * focus[1])
    ox = max(0, min(ox, tw - nw))
    oy = max(0, min(oy, th - nh))
    out.paste(subject, (ox, oy))
    return out


def photo(
    name: str,
    size: tuple[int, int],
    zoom: float | None = None,
    mode: str = "contain",
    valign: str = "center",
    bg_mode: str = "blur",
) -> Image.Image:
    """Default: contain — whole dog visible."""
    if mode == "cover":
        z = ZOOM[name] if zoom is None else zoom
        return fit_cover(load(name), size, focus=FOCUS[name], zoom=z)
    return fit_contain(
        load(name), size, focus=FOCUS[name], valign=valign, bg_mode=bg_mode
    )


def darken(img: Image.Image, factor=0.55) -> Image.Image:
    return ImageEnhance.Brightness(img).enhance(factor)


def gradient_overlay(size, top_alpha=0, bottom_alpha=210, color=(15, 42, 46)):
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    px = overlay.load()
    for y in range(h):
        t = y / (h - 1)
        # ease in toward bottom
        a = int(top_alpha + (bottom_alpha - top_alpha) * (t ** 1.4))
        for x in range(w):
            px[x, y] = (*color, a)
    return overlay


def text_wrap(draw, text, font_obj, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font_obj) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_multiline(draw, lines, xy, font_obj, fill, line_gap=10, align="left", box_w=None):
    x, y = xy
    for line in lines:
        w = draw.textlength(line, font=font_obj)
        lx = x
        if align == "center" and box_w:
            lx = x + (box_w - w) / 2
        draw.text((lx, y), line, font=font_obj, fill=fill)
        bbox = font_obj.getbbox(line)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def badge(draw, text, xy, bg=C["coral"], fg=C["white"], pad_x=22, pad_y=12, radius=999):
    f = font(28, 800)
    tw = draw.textlength(text, font=f)
    x, y = xy
    box = (x, y, x + tw + pad_x * 2, y + 28 + pad_y * 2)
    round_rect(draw, box, radius, fill=bg)
    draw.text((x + pad_x, y + pad_y - 2), text, font=f, fill=fg)
    return box


def panel(draw, xy, radius=28, fill=C["panel"], shadow=False, base=None):
    if shadow and base is not None:
        # soft shadow via separate layer handled by caller usually
        pass
    round_rect(draw, xy, radius, fill=fill)


def load(name: str) -> Image.Image:
    return Image.open(SRC / name)


def card_cover():
    # Dog fully visible in the upper zone; text lives below
    canvas = Image.new("RGB", (W, H), C["deep"])
    shot = photo("01-outdoor-portrait.jpg", (W, 1080), valign="center")
    canvas.paste(shot, (0, 0))
    base = canvas.convert("RGBA")
    # soft bottom fade into text area
    fade = gradient_overlay((W, H), 0, 0)
    # manual fade only near text band
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = overlay.load()
    for y in range(980, H):
        t = (y - 980) / (H - 980)
        a = int(230 * (t ** 0.9))
        for x in range(W):
            px[x, y] = (15, 42, 46, a)
    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)
    badge(draw, "ПЁС-ГЕРОЙ", (48, 56), bg=C["coral"])

    title = font(78, 800)
    lines = ["Помочь", "Кубику", "найти дом"]
    y = 1120
    for line in lines:
        draw.text((48, y), line, font=title, fill=C["sand"])
        y += 82

    sub = font(30, 500)
    draw.text((48, 1400), "Спас человека во время обстрела.", font=sub, fill=(220, 230, 226))
    draw.text((48, 1445), "Восстановился. Ждёт свою семью.", font=sub, fill=(220, 230, 226))
    draw.rectangle((48, 1510, 220, 1520), fill=C["mint"])
    base.convert("RGB").save(OUT / "01-cover.jpg", quality=92, optimize=True)


def card_hero():
    canvas = Image.new("RGB", (W, H), C["deep"])
    # Photo zone ends before text panel — dog fully visible
    photo_h = 760
    shot = photo("03-recovered-brace.jpg", (W, photo_h), valign="center")
    canvas.paste(shot, (0, 0))

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((36, photo_h - 20, W - 36, H - 40), radius=36, fill=(0, 0, 0, 45))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    round_rect(draw, (48, photo_h - 8, W - 48, H - 56), 32, fill=C["white"])

    badge(draw, "ИСТОРИЯ", (80, photo_h + 28), bg=C["deep"], fg=C["mint"])

    title = font(52, 800)
    y = draw_multiline(
        draw,
        text_wrap(draw, "Рискуя жизнью, спас человека", title, W - 200),
        (80, photo_h + 100),
        title,
        C["ink"],
        line_gap=8,
    )
    body = font(30, 500)
    text = (
        "Когда начался обстрел, Кубик не убежал. "
        "Он побежал к домику охраны — предупредить друга."
    )
    draw_multiline(draw, text_wrap(draw, text, body, W - 200), (80, y + 28), body, C["muted"], line_gap=10)

    chips = [("Шебекино", C["sage"]), ("Служебный пёс", C["sage"])]
    x = 80
    for label, bg in chips:
        f = font(24, 700)
        tw = draw.textlength(label, font=f)
        round_rect(draw, (x, 1400, x + tw + 36, 1460), 999, fill=bg)
        draw.text((x + 18, 1412), label, font=f, fill=C["deep"])
        x += tw + 52

    canvas.save(OUT / "02-hero.jpg", quality=92, optimize=True)


def card_story():
    canvas = Image.new("RGB", (W, H), C["sand"])
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, 18, H), fill=C["coral"])
    badge(draw, "КТО ТАКОЙ КУБИК", (48, 48), bg=C["coral"])

    title = font(58, 800)
    draw_multiline(
        draw,
        text_wrap(draw, "Охранник, который стал героем", title, W - 120),
        (48, 130),
        title,
        C["ink"],
        line_gap=6,
    )

    # Full-body outdoor shot (soft portrait crops the body in the source)
    shot = photo("01-outdoor-portrait.jpg", (W - 96, 780), valign="center", bg_mode="sand")
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, shot.size[0], shot.size[1]), 28, fill=255)
    canvas.paste(shot, (48, 250), mask)

    draw = ImageDraw.Draw(canvas)
    body = font(28, 500)
    paragraphs = [
        "Кубик жил и нёс службу на предприятии в Шебекино.",
        "В тот день, услышав взрывы, вместо бегства он побежал предупредить человека, которого считал другом.",
        "Снаряд разорвался рядом…",
    ]
    y = 1060
    for p in paragraphs:
        lines = text_wrap(draw, p, body, W - 120)
        y = draw_multiline(draw, lines, (48, y), body, C["ink"], line_gap=6)
        y += 16

    canvas.save(OUT / "03-story.jpg", quality=92, optimize=True)


def card_injury():
    canvas = Image.new("RGB", (W, H), C["deep"])
    photo_h = 900
    shot = photo("05-recovery-bandages.jpg", (W, photo_h), valign="center")
    canvas.paste(shot, (0, 0))
    draw = ImageDraw.Draw(canvas)

    badge(draw, "СПАСЕНИЕ", (48, 48), bg=C["coral"])

    round_rect(draw, (48, photo_h - 20, W - 48, H - 56), 32, fill=C["white"])

    title = font(46, 800)
    y = draw_multiline(
        draw,
        text_wrap(draw, "Истекающего кровью привезли в приют", title, W - 160),
        (80, photo_h + 20),
        title,
        C["ink"],
        line_gap=6,
    )
    body = font(28, 500)
    facts = [
        "• Часть одной передней лапы оторвало",
        "• Вторая — иссечена осколками и переломана",
        "• Врачи чудом сохранили вторую лапку",
    ]
    y += 24
    for fact in facts:
        draw.text((80, y), fact, font=body, fill=C["muted"])
        y += 48

    canvas.save(OUT / "04-injury.jpg", quality=92, optimize=True)


def card_rehab():
    canvas = Image.new("RGB", (W, H), C["deep"])
    shot = photo("06-recovery-crate.jpg", (W - 96, 700), valign="center")
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *shot.size), 28, fill=255)
    canvas.paste(shot, (48, 48), mask)

    draw = ImageDraw.Draw(canvas)
    badge(draw, "РЕАБИЛИТАЦИЯ", (48, 780), bg=C["mint"], fg=C["deep"])

    title = font(52, 800)
    y = draw_multiline(
        draw,
        text_wrap(draw, "2 месяца — на руках у врачей", title, W - 120),
        (48, 860),
        title,
        C["sand"],
        line_gap=8,
    )

    body = font(30, 500)
    text = (
        "Одной передней лапы нет, на вторую со штифтами опираться нельзя было. "
        "Даже сходить в туалет Кубик не мог сам. Наши девочки-врачи таскали его на руках — а он 30 кг."
    )
    draw_multiline(draw, text_wrap(draw, text, body, W - 120), (48, y + 28), body, (200, 214, 210), line_gap=10)

    stats = [("30 кг", "вес"), ("2 мес.", "реабилитация"), ("3 лапы", "сейчас")]
    x = 48
    for val, label in stats:
        round_rect(draw, (x, 1360, x + 340, 1520), 24, fill=C["deep2"])
        draw.text((x + 28, 1390), val, font=font(44, 800), fill=C["mint"])
        draw.text((x + 28, 1455), label, font=font(26, 500), fill=(180, 198, 194))
        x += 360

    canvas.save(OUT / "05-rehab.jpg", quality=92, optimize=True)


def card_now():
    canvas = Image.new("RGB", (W, H), C["deep"])
    shot = photo("01-outdoor-portrait.jpg", (W, 1080), valign="center")
    canvas.paste(shot, (0, 0))
    base = canvas.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = overlay.load()
    for y in range(980, H):
        t = (y - 980) / (H - 980)
        a = int(230 * (t ** 0.9))
        for x in range(W):
            px[x, y] = (15, 42, 46, a)
    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)

    badge(draw, "СЕЙЧАС", (48, 48), bg=C["mint"], fg=C["deep"])

    title = font(64, 800)
    y = 1120
    for line in ["Полностью", "восстановился"]:
        draw.text((48, y), line, font=title, fill=C["sand"])
        y += 72

    body = font(30, 500)
    text = "Научился ходить на трёх лапках. Чудесный пёс: умный, добрый, хороший охранник."
    draw_multiline(draw, text_wrap(draw, text, body, W - 120), (48, y + 20), body, (220, 230, 226), line_gap=10)

    base.convert("RGB").save(OUT / "06-now.jpg", quality=92, optimize=True)


def card_character():
    canvas = Image.new("RGB", (W, H), C["sand"])
    draw = ImageDraw.Draw(canvas)

    shot = photo("03-recovered-brace.jpg", (W - 96, 520), valign="center", bg_mode="sand")
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *shot.size), 28, fill=255)
    canvas.paste(shot, (48, 48), mask)

    draw = ImageDraw.Draw(canvas)
    badge(draw, "ХАРАКТЕР", (48, 600), bg=C["deep"], fg=C["mint"])

    title = font(54, 800)
    draw.text((48, 680), "Какой он", font=title, fill=C["ink"])

    traits = [
        ("Умный", "Понимает людей и ситуацию"),
        ("Добрый", "Мягкий и контактный"),
        ("Охранник", "Верный и внимательный"),
        ("Герой", "Рискнул жизнью ради друга"),
    ]

    y = 780
    for i, (name, desc) in enumerate(traits):
        bg = C["white"] if i % 2 == 0 else (236, 244, 240)
        round_rect(draw, (48, y, W - 48, y + 150), 24, fill=bg)
        cx, cy = 110, y + 75
        draw.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), fill=C["mint"] if i != 3 else C["coral"])
        draw.text((cx - 10, cy - 18), str(i + 1), font=font(32, 800), fill=C["deep"])
        draw.text((180, y + 36), name, font=font(36, 800), fill=C["ink"])
        draw.text((180, y + 90), desc, font=font(26, 500), fill=C["muted"])
        y += 170

    canvas.save(OUT / "07-character.jpg", quality=92, optimize=True)


def card_home():
    canvas = Image.new("RGB", (W, H), C["deep"])
    shot = photo("03-recovered-brace.jpg", (W, 1080), valign="center")
    canvas.paste(shot, (0, 0))
    base = canvas.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = overlay.load()
    for y in range(980, H):
        t = (y - 980) / (H - 980)
        a = int(235 * (t ** 0.9))
        for x in range(W):
            px[x, y] = (15, 42, 46, a)
    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)

    badge(draw, "ИЩЕТ ДОМ", (48, 56), bg=C["coral"])

    title = font(68, 800)
    y = 1100
    for line in ["Не хватает", "только своего", "человека"]:
        draw.text((48, y), line, font=title, fill=C["sand"])
        y += 78

    body = font(30, 500)
    text = "Мы надеемся, что Кубику повезёт. Он заслуживает любви."
    draw_multiline(draw, text_wrap(draw, text, body, W - 120), (48, y + 16), body, (220, 230, 226), line_gap=10)

    f = font(28, 800)
    label = "Помочь Кубику найти дом"
    tw = draw.textlength(label, font=f)
    round_rect(draw, (48, 1480, 48 + tw + 56, 1555), 999, fill=C["mint"])
    draw.text((76, 1498), label, font=f, fill=C["deep"])

    base.convert("RGB").save(OUT / "08-home.jpg", quality=92, optimize=True)


def card_help():
    """Explain what the purchase means — common for Ozon charity cards."""
    canvas = Image.new("RGB", (W, H), C["deep"])
    draw = ImageDraw.Draw(canvas)

    badge(draw, "КАК ЭТО РАБОТАЕТ", (48, 56), bg=C["mint"], fg=C["deep"])

    title = font(56, 800)
    draw_multiline(
        draw,
        text_wrap(draw, "Ваша поддержка — реальная помощь", title, W - 120),
        (48, 140),
        title,
        C["sand"],
        line_gap=8,
    )

    items = [
        ("1", "Покупка", "Средства идут на содержание и лечение подопечных приюта"),
        ("2", "Забота", "Корм, лекарства, перевязки и реабилитация"),
        ("3", "Дом", "Мы продолжаем искать Кубику любящую семью"),
    ]

    y = 360
    for num, head, desc in items:
        round_rect(draw, (48, y, W - 48, y + 260), 28, fill=C["deep2"])
        draw.ellipse((80, y + 80, 180, y + 180), fill=C["coral"] if num == "3" else C["mint"])
        draw.text((112, y + 105), num, font=font(48, 800), fill=C["deep"])
        draw.text((220, y + 70), head, font=font(40, 800), fill=C["sand"])
        draw_multiline(
            draw,
            text_wrap(draw, desc, font(28, 500), W - 320),
            (220, y + 140),
            font(28, 500),
            (180, 198, 194),
            line_gap=8,
        )
        y += 290

    # tiny footer
    draw.text((48, 1500), "Приют • Кубик ждёт встречи", font=font(26, 500), fill=(140, 160, 156))
    canvas.save(OUT / "09-help.jpg", quality=92, optimize=True)


def card_gallery_extra():
    """Extra lifestyle outdoor yard shot."""
    canvas = Image.new("RGB", (W, H), C["deep"])
    shot = photo("02-outdoor-yard.jpg", (W, 1180), valign="center")
    canvas.paste(shot, (0, 0))
    base = canvas.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = overlay.load()
    for y in range(1100, H):
        t = (y - 1100) / max(1, H - 1100)
        a = int(220 * (t ** 0.85))
        for x in range(W):
            px[x, y] = (15, 42, 46, a)
    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)
    badge(draw, "ЖИЗНЬ В ПРИЮТЕ", (48, 56), bg=C["white"], fg=C["deep"])
    title = font(58, 800)
    draw.text((48, 1280), "Спокойный.", font=title, fill=C["sand"])
    draw.text((48, 1355), "Добрый.", font=title, fill=C["sand"])
    draw.text((48, 1430), "Готовый к дому.", font=title, fill=C["mint"])
    base.convert("RGB").save(OUT / "10-yard.jpg", quality=92, optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    generators = [
        card_cover,
        card_hero,
        card_story,
        card_injury,
        card_rehab,
        card_now,
        card_character,
        card_home,
        card_help,
        card_gallery_extra,
    ]
    for gen in generators:
        print("→", gen.__name__)
        gen()
    print("Done:", sorted(p.name for p in OUT.glob("*.jpg")))


if __name__ == "__main__":
    main()
