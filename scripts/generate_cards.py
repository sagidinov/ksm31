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


def fit_cover(img: Image.Image, size: tuple[int, int], focus=(0.5, 0.38)) -> Image.Image:
    tw, th = size
    img = img.convert("RGB")
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = int((nw - tw) * focus[0])
    top = int((nh - th) * focus[1])
    left = max(0, min(left, nw - tw))
    top = max(0, min(top, nh - th))
    return img.crop((left, top, left + tw, top + th))


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
    photo = fit_cover(load("01-outdoor-portrait.jpg"), (W, H), focus=(0.52, 0.32))
    base = photo.convert("RGBA")
    base = Image.alpha_composite(base, gradient_overlay((W, H), 20, 235))
    # top soft vignette
    top = gradient_overlay((W, H), 120, 0, color=(15, 42, 46))
    base = Image.alpha_composite(base, top)

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

    # accent bar
    draw.rectangle((48, 1510, 220, 1520), fill=C["mint"])
    out = base.convert("RGB")
    out.save(OUT / "01-cover.jpg", quality=92, optimize=True)


def card_hero():
    canvas = Image.new("RGB", (W, H), C["deep"])
    photo = fit_cover(load("03-recovered-brace.jpg"), (W, 980), focus=(0.45, 0.35))
    canvas.paste(photo, (0, 0))

    # bottom panel
    draw = ImageDraw.Draw(canvas, "RGBA")
    # wave-like panel
    draw.rounded_rectangle((0, 860, W, H), radius=0, fill=C["sand"])
    # overlapping rounded panel
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((36, 820, W - 36, H - 40), radius=36, fill=(0, 0, 0, 45))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    round_rect(draw, (48, 840, W - 48, H - 56), 32, fill=C["white"])

    badge(draw, "ИСТОРИЯ", (80, 880), bg=C["deep"], fg=C["mint"])

    title = font(52, 800)
    y = draw_multiline(
        draw,
        text_wrap(draw, "Рискуя жизнью, спас человека", title, W - 200),
        (80, 960),
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

    # bottom accent chips
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

    # left accent strip
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

    photo = fit_cover(load("04-soft-portrait.jpg"), (W - 96, 620), focus=(0.5, 0.35))
    # rounded photo via mask
    mask = Image.new("L", photo.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, photo.size[0], photo.size[1]), 28, fill=255)
    layer = Image.new("RGB", (W, H), C["sand"])
    layer.paste(photo, (48, 320), mask)
    canvas.paste(layer)

    draw = ImageDraw.Draw(canvas)
    body = font(30, 500)
    paragraphs = [
        "Кубик жил и нёс службу на предприятии в Шебекино.",
        "В тот день, услышав взрывы, вместо бегства он побежал предупредить человека, которого считал другом.",
        "Снаряд разорвался рядом…",
    ]
    y = 980
    for p in paragraphs:
        lines = text_wrap(draw, p, body, W - 120)
        y = draw_multiline(draw, lines, (48, y), body, C["ink"], line_gap=8)
        y += 22

    canvas.save(OUT / "03-story.jpg", quality=92, optimize=True)


def card_injury():
    photo = fit_cover(load("05-recovery-bandages.jpg"), (W, H), focus=(0.5, 0.4))
    base = photo.convert("RGBA")
    base = Image.alpha_composite(base, gradient_overlay((W, H), 40, 230))
    draw = ImageDraw.Draw(base)

    badge(draw, "СПАСЕНИЕ", (48, 48), bg=C["coral"])

    # content panel
    panel_box = (48, 980, W - 48, H - 56)
    round_rect(draw, panel_box, 32, fill=(255, 255, 255, 235))

    title = font(46, 800)
    y = draw_multiline(
        draw,
        text_wrap(draw, "Истекающего кровью привезли в приют", title, W - 160),
        (80, 1020),
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

    out = base.convert("RGB")
    out.save(OUT / "04-injury.jpg", quality=92, optimize=True)


def card_rehab():
    canvas = Image.new("RGB", (W, H), C["deep"])
    photo = fit_cover(load("06-recovery-crate.jpg"), (W - 96, 720), focus=(0.45, 0.35))
    mask = Image.new("L", photo.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *photo.size), 28, fill=255)
    canvas.paste(photo, (48, 48), mask)

    draw = ImageDraw.Draw(canvas)
    badge(draw, "РЕАБИЛИТАЦИЯ", (48, 810), bg=C["mint"], fg=C["deep"])

    title = font(52, 800)
    y = draw_multiline(
        draw,
        text_wrap(draw, "2 месяца — на руках у врачей", title, W - 120),
        (48, 890),
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

    # stats row
    stats = [("30 кг", "вес"), ("2 мес.", "реабилитация"), ("3 лапы", "сейчас")]
    x = 48
    for val, label in stats:
        round_rect(draw, (x, 1360, x + 340, 1520), 24, fill=C["deep2"])
        draw.text((x + 28, 1390), val, font=font(44, 800), fill=C["mint"])
        draw.text((x + 28, 1455), label, font=font(26, 500), fill=(180, 198, 194))
        x += 360

    canvas.save(OUT / "05-rehab.jpg", quality=92, optimize=True)


def card_now():
    photo = fit_cover(load("01-outdoor-portrait.jpg"), (W, H), focus=(0.5, 0.34))
    base = photo.convert("RGBA")
    # side gradient for text readability
    side = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = side.load()
    for y in range(H):
        for x in range(W):
            t = max(0, (x - W * 0.35) / (W * 0.65))
            a = int(200 * (t ** 1.1))
            # actually darken left for text? Better bottom panel again
            pass
    base = Image.alpha_composite(base, gradient_overlay((W, H), 10, 220))
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

    out = base.convert("RGB")
    out.save(OUT / "06-now.jpg", quality=92, optimize=True)


def card_character():
    canvas = Image.new("RGB", (W, H), C["sand"])
    draw = ImageDraw.Draw(canvas)

    photo = fit_cover(load("03-recovered-brace.jpg"), (W - 96, 560), focus=(0.42, 0.4))
    mask = Image.new("L", photo.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *photo.size), 28, fill=255)
    canvas.paste(photo, (48, 48), mask)

    draw = ImageDraw.Draw(canvas)
    badge(draw, "ХАРАКТЕР", (48, 640), bg=C["deep"], fg=C["mint"])

    title = font(54, 800)
    draw.text((48, 720), "Какой он", font=title, fill=C["ink"])

    traits = [
        ("Умный", "Понимает людей и ситуацию"),
        ("Добрый", "Мягкий и контактный"),
        ("Охранник", "Верный и внимательный"),
        ("Герой", "Рискнул жизнью ради друга"),
    ]

    y = 820
    for i, (name, desc) in enumerate(traits):
        bg = C["white"] if i % 2 == 0 else (236, 244, 240)
        round_rect(draw, (48, y, W - 48, y + 150), 24, fill=bg)
        # accent circle
        cx, cy = 110, y + 75
        draw.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), fill=C["mint"] if i != 3 else C["coral"])
        draw.text((cx - 10, cy - 18), str(i + 1), font=font(32, 800), fill=C["deep"])
        draw.text((180, y + 36), name, font=font(36, 800), fill=C["ink"])
        draw.text((180, y + 90), desc, font=font(26, 500), fill=C["muted"])
        y += 170

    canvas.save(OUT / "07-character.jpg", quality=92, optimize=True)


def card_home():
    photo = fit_cover(load("04-soft-portrait.jpg"), (W, H), focus=(0.5, 0.32))
    base = photo.convert("RGBA")
    base = Image.alpha_composite(base, gradient_overlay((W, H), 30, 240))
    draw = ImageDraw.Draw(base)

    badge(draw, "ИЩЕТ ДОМ", (48, 56), bg=C["coral"])

    title = font(68, 800)
    y = 1080
    for line in ["Не хватает", "только своего", "человека"]:
        draw.text((48, y), line, font=title, fill=C["sand"])
        y += 78

    body = font(30, 500)
    text = "Мы надеемся, что Кубику повезёт. Он заслуживает любви."
    draw_multiline(draw, text_wrap(draw, text, body, W - 120), (48, y + 16), body, (220, 230, 226), line_gap=10)

    # CTA pill
    f = font(28, 800)
    label = "Помочь Кубику найти дом"
    tw = draw.textlength(label, font=f)
    round_rect(draw, (48, 1480, 48 + tw + 56, 1555), 999, fill=C["mint"])
    draw.text((76, 1498), label, font=f, fill=C["deep"])

    out = base.convert("RGB")
    out.save(OUT / "08-home.jpg", quality=92, optimize=True)


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
    photo = fit_cover(load("02-outdoor-yard.jpg"), (W, H), focus=(0.45, 0.45))
    base = photo.convert("RGBA")
    base = Image.alpha_composite(base, gradient_overlay((W, H), 15, 200))
    draw = ImageDraw.Draw(base)
    badge(draw, "ЖИЗНЬ В ПРИЮТЕ", (48, 56), bg=C["white"], fg=C["deep"])
    title = font(58, 800)
    draw.text((48, 1280), "Спокойный.", font=title, fill=C["sand"])
    draw.text((48, 1355), "Добрый.", font=title, fill=C["sand"])
    draw.text((48, 1430), "Готовый к дому.", font=title, fill=C["mint"])
    out = base.convert("RGB")
    out.save(OUT / "10-yard.jpg", quality=92, optimize=True)


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
