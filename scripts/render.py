#!/usr/bin/env python3
"""Render the profile README artwork as light and dark SVG files.

Every visual block of README.md is generated from the content defined below,
with the DEVLOPN palette and subsets of the site's own fonts embedded, so the
images render the same on github.com, in the mobile app and offline.

    python3 -m venv .venv
    .venv/bin/pip install fonttools brotli pillow
    .venv/bin/python scripts/render.py

Facts must stay in sync with https://devlopn.com and, for the audit offer,
with https://audit.devlopn.com/#tarifs.
"""
from __future__ import annotations

import base64
import io
import math
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "src"
OUT = ROOT / "assets"
FONT_FILES = {
    "sans": ROOT / "scripts" / "fonts" / "inter-latin.woff2",
    "mono": ROOT / "scripts" / "fonts" / "jetbrains-mono-latin.woff2",
}

# Palette from devlopn.com (styles.css :root and :root[data-theme="dark"]).
THEMES = {
    "light": {
        "bg": "#f4f3ed", "surface": "#fffefa", "ink": "#23251f", "muted": "#64665e",
        "line": "#d5d6cc", "orange": "#e65c36", "orangeText": "#b4400f",
        "orangeSoft": "#f9e1d6", "sage": "#e3e7dd", "dark": "#22251f",
        "onDark": "#f4f3ed", "darkMuted": "#b4b9ac", "darkLine": "#3e4238",
    },
    "dark": {
        "bg": "#171916", "surface": "#242721", "ink": "#f1f0e9", "muted": "#b4b8ae",
        "line": "#3b4038", "orange": "#ed7956", "orangeText": "#ff9b7c",
        "orangeSoft": "#4b2d22", "sage": "#2b2f28", "dark": "#10120f",
        "onDark": "#f1f0e9", "darkMuted": "#bec2b8", "darkLine": "#2e322b",
    },
}
AUDIT = {  # audit.devlopn.com palette, identical in both themes
    "bg": "#112e40", "ink": "#f1f5f2", "muted": "#a2bbc9", "line": "#456070",
    "mint": "#b9ebd5",
}

# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------
EXPERTISE = [
    ("Build to last",
     "Is each new feature getting harder to ship? I help clarify responsibilities, "
     "manage state and prioritise technical debt so the app can evolve.",
     ["FLUTTER · DART", "BLOC · RIVERPOD · CLEAN ARCHITECTURE"]),
    ("Make delivery dependable",
     "Are releases taking too much effort? I automate delivery, test critical "
     "journeys and improve production monitoring, from pull request to the stores.",
     ["CI/CD · FASTLANE · GITHUB ACTIONS", "FIREBASE · AWS · CRASHLYTICS"]),
    ("Help the team move forward",
     "Does the team need technical direction? I help weigh architecture choices, "
     "review code and share knowledge through day-to-day collaboration.",
     ["TECH LEAD · CODE REVIEW", "MENTORING · PRODUCT THINKING"]),
    ("Put AI agents to work, safely",
     "Are coding agents writing more of your code? I help frame them with lints, tests "
     "and a clear definition of done, and I review what they produce before it ships.",
     ["AI AGENTS · CODE REVIEW", "LINTS · TESTS · DEFINITION OF DONE"]),
]

EXPERIENCE = [
    dict(when="MAR 2025 — PRESENT", sector="AUTOMOTIVE & MOBILITY", company="Renault Digital",
         role="Senior Software Engineer · Freelance", current=True,
         text="Technical lead on the multi-brand Renault, Dacia and Alpine mobile app: "
              "architecture, remote internationalisation, CI/CD and quality.",
         tags=["Flutter / Dart", "Architecture", "CI/CD"]),
    dict(when="AUG 2022 — MAR 2025", sector="TRAVEL & MOBILITY", company="SNCF Connect & Tech",
         role="Senior Developer Dart / Flutter", current=False,
         text="Architecture for a white-label ticket inspection and payment app. JustGo and "
              "Airweb: native integrations, scanning, unit, widget and golden tests, through "
              "to production launch.",
         tags=["Flutter / Dart", "AWS", "Firebase"]),
    dict(when="SINCE JAN 2023", sector="RARE DISEASE DETECTION", company="Zanalys",
         role="Senior Flutter developer · Healthcare", current=True,
         text="A medical solution for the early detection of rare diseases: application audit, "
              "real-time chat, biometric identification, notifications and error handling.",
         tags=["Flutter", "Firebase", "Product"]),
    dict(when="2019 — 2022", sector="CONNECTED SCREENS", company="Easivio",
         role="Co-founder", current=False,
         text="Mobile widgets displayed on Android TV through the Easivio TV companion app, "
              "and Pixhella, a photo-sharing network with a print service.",
         tags=["Flutter", "Firebase", "Android TV"]),
    dict(when="OCT 2014 — NOV 2019", sector="COMPLEX SYSTEMS", company="Thales",
         role="Software engineering · Team management", current=False,
         text="Head of the SmartDisplay competence centre, a 60-person department. Delivery "
              "lead on ALLIOT international parcel tracking for La Poste and Swiss Post.",
         tags=["Engineering", "Management", "Delivery"]),
]

PRODUCTS = [
    dict(slug="tripveri", name="Tripveri", category="TRAVEL TECH", status="In progress",
         domain="tripveri.com", image="tripveri.png", mode="peek", pad=0.42, bg={"light": "#dfe9e4", "dark": "#1d2a27"},
         text="Tailored trips built around what you want. Itineraries, places, routes and "
              "a travel guide brought together in one product.",
         stack="NEXT.JS · TYPESCRIPT · SUPABASE · AI"),
    dict(slug="rewvy", name="Rewvy", category="SAAS / RETAIL", status="In progress",
         domain="rewvy.com", image="rewvy.png", mode="contain", pad=0.96,
         text="A digital loyalty platform for merchants: wallet cards, customer "
              "relationships and an app for scanning at checkout.",
         stack="FLUTTER · REACT · NESTJS"),
    dict(slug="simulfin", name="Simulfin", category="FINTECH / WEB APP", status="Beta",
         domain="simulfin.com", image="simulfin-1200.webp", mode="cover", focus=(0.5, 0.55),
         caption="CONCEPT VISUAL",
         text="Bring investments together in one place: stocks, crypto and property. "
              "Track your portfolio and goals with a consolidated view.",
         stack="FINTECH · WEB APP · PRODUCT"),
    dict(slug="tikipik", name="Tikipik", category="PHOTO / MOBILE", status="Beta testing",
         domain="tikipik.com", image="tikipik-800.webp", mode="cover", focus=(0.5, 0.45),
         text="Create and order photo products from your phone. An end-to-end mobile "
              "experience, from choosing pictures to placing an order.",
         stack="FLUTTER · FIREBASE · E-COMMERCE"),
    dict(slug="spoolkeep", name="Spoolkeep", category="MAKER TOOLS / MOBILE", status=None,
         domain="spoolkeep.com", image="spoolkeep.png", mode="contain", pad=0.8, bg={"light": "#efe4d9", "dark": "#2a221d"},
         text="Manage filament spools, track remaining material and calculate the material "
              "cost of 3D prints. Data stays on the device.",
         stack="FLUTTER · BLOC · SQLITE"),
    dict(slug="volutea", name="Volutea", category="DESIGN / E-COMMERCE", status=None,
         domain="volutea.fr", image="volutea-960.webp", mode="cover", focus=(0.5, 0.6),
         text="3D-printed home objects and an online store. Connecting design, manufacturing "
              "and the e-commerce experience.",
         stack="ASTRO · REACT · STRIPE"),
    dict(slug="pixhella", name="Pixhella", category="ENTREPRENEURIAL / PHOTO", status="Completed",
         domain="Watch the demo", image="pixhella.jpg", mode="blur", pad=0.9,
         text="Co-founded within Easivio. A photo-sharing network with a print service: "
              "photo books and prints from the phone, Google Photos, Instagram and Facebook.",
         stack="FLUTTER · FIREBASE · CI/CD"),
    dict(slug="easivio", name="Easivio", category="ENTREPRENEURIAL / CONNECTED SCREENS",
         status="Completed", domain="Watch the demo", image="easivio.jpg", mode="blur", pad=0.9,
         text="Co-founded (2019–2022). Create widgets on mobile, then display them on "
              "Android TV through the Easivio TV companion app.",
         stack="FLUTTER · ANDROID TV · REAL-TIME SYNC"),
]

QUOTES = [
    ("His strong technical expertise helped us make several crucial architecture decisions, "
     "combining rigour, pragmatism and a real ability to bring others along.",
     "Quentin Payré", "Flutter developer · Renault Digital project", "QP"),
    ("As a senior Flutter/Dart developer, Jérémy brought a long-term vision to our projects, "
     "anticipating future needs and proposing suitable, scalable technical solutions.",
     "Patrick Raguin", "Flutter / Fullstack Lead · SNCF Connect project", "PR"),
    ("Highly involved in the team, he stands out for his common sense and ability to challenge "
     "both technical and functional choices, always in service of the product and the user.",
     "Marie Postic", "Product Owner", "MP"),
]

SECTIONS = {
    "expertise": ("01 / EXPERTISE", "The code matters, and so does everything around it",
                  "I connect technical decisions to the realities of your product, your team and your next release."),
    "experience": ("02 / EXPERIENCE", "Experience you can build on",
                   "From large organisations to products built from scratch, all the way to production."),
    "products": ("03 / PRODUCTS", "I also build for myself",
                 "Independent products. Different contexts, the same pleasure in making things work."),
    "audit": ("04 / A FRESH TECHNICAL PERSPECTIVE", "DEVLOPN Audit",
              "A defined scope, public pricing and an expert review, for Flutter and native mobile apps."),
    "quotes": ("05 / IN THEIR WORDS", "A good project is a team effort",
               "LinkedIn excerpts · French originals translated into English."),
    "writing": ("06 / WRITING", "Notes from the audit desk",
                "Field notes on Flutter, iOS and Android, published in French on the DEVLOPN Audit blog."),
    "toolbox": ("07 / TOOLBOX", "What I ship with",
                "Plus a few shadow clones. None of them ships unreviewed."),
    "activity": ("08 / ACTIVITY", "Commit by commit",
                 "Most of my work lives in private client repositories."),
}

BUTTONS = [
    ("site", "DEVLOPN.COM", True),
    ("audit", "AUDIT", False),
    ("linkedin", "LINKEDIN", False),
    ("malt", "MALT 5.0/5", False),
    ("call", "BOOK A CALL", False),
    ("email", "EMAIL", False),
]

# --------------------------------------------------------------------------
# Fonts and text measurement
# --------------------------------------------------------------------------
_FONTS = {name: TTFont(path) for name, path in FONT_FILES.items()}
_CMAPS = {name: font.getBestCmap() for name, font in _FONTS.items()}
WEIGHT_WIDTH = {400: 1.0, 500: 1.02, 600: 1.045, 700: 1.07, 800: 1.09}


def measure(text: str, font: str = "sans", size: float = 16, weight: int = 400, ls: float = 0) -> float:
    if font == "serif":  # Georgia and its fallbacks, approximated
        return len(text) * size * 0.47 + ls * len(text)
    ttf, cmap = _FONTS[font], _CMAPS[font]
    upm = ttf["head"].unitsPerEm
    width = 0.0
    for ch in text:
        glyph = cmap.get(ord(ch))
        width += ttf["hmtx"][glyph][0] if glyph else upm * 0.6
    width = width / upm * size
    if font == "sans":
        width *= WEIGHT_WIDTH.get(weight, 1.0)
    return width + ls * len(text)


def wrap(text: str, maxw: float, font: str = "sans", size: float = 16, weight: int = 400) -> list[str]:
    lines, current = [], ""
    for word in text.split(" "):
        candidate = f"{current} {word}".strip()
        if current and measure(candidate, font, size, weight) > maxw:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def font_face(name: str, chars: set[str]) -> str:
    missing = sorted(c for c in chars if ord(c) not in _CMAPS[name] and not c.isspace())
    if missing:
        print(f"  ! {name} has no glyph for {''.join(missing)!r}, a system font will be used")
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt", "ccmp", "locl", "mark", "mkmk"]
    opts.notdef_outline = True
    font = TTFont(FONT_FILES[name])
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(chars) + " ")
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    family = "DevlopnSans" if name == "sans" else "DevlopnMono"
    weights = "100 900" if name == "sans" else "100 800"
    return (f"@font-face{{font-family:{family};font-weight:{weights};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------
def image_uri(name: str, w: int, h: int, mode: str = "cover", focus=(0.5, 0.5),
              pad: float = 1.0, bg: str | None = None, quality: int = 80) -> str:
    im = Image.open(SRC / name)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        flat = Image.new("RGB", im.size, bg or "#ffffff")
        flat.paste(im, mask=im.getchannel("A"))
        im = flat
    im = im.convert("RGB")
    W, H = w * 2, h * 2
    if mode == "cover":
        r = max(W / im.width, H / im.height)
        if r > 1:  # never upscale: shrink the output instead
            W, H, r = round(W / r), round(H / r), 1.0
        im = im.resize((max(W, round(im.width * r)), max(H, round(im.height * r))), Image.LANCZOS)
        x = round((im.width - W) * focus[0])
        y = round((im.height - H) * focus[1])
        im = im.crop((x, y, x + W, y + H))
    elif mode == "peek":  # a tall phone screenshot rising from the bottom edge
        canvas = Image.new("RGB", (W, H), bg)
        sw = round(W * pad)
        shot = im.resize((sw, round(im.height * sw / im.width)), Image.LANCZOS)
        radius = round(sw * 0.06)
        mask = Image.new("L", shot.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, shot.width - 1, shot.height + radius), radius, fill=255)
        frame = Image.new("RGB", (sw + 12, shot.height + 12), "#1d1f1b")
        fmask = Image.new("L", frame.size, 0)
        ImageDraw.Draw(fmask).rounded_rectangle((0, 0, frame.width - 1, frame.height + radius), radius + 6, fill=255)
        x, y = (W - frame.width) // 2, round(H * 0.12)
        canvas.paste(frame, (x, y), fmask)
        canvas.paste(shot, (x + 6, y + 6), mask)
        im = canvas
    else:  # contain on a flat colour ("contain") or on a blurred copy ("blur")
        bbox = im.convert("L").point(lambda v: 255 if v > 14 else 0).getbbox()
        if mode == "blur" and bbox:  # drop letterbox bars
            im = im.crop(bbox)
        r = min(W / im.width, H / im.height) * pad
        inner = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        if mode == "blur":
            cr = max(W / im.width, H / im.height)
            canvas = im.resize((round(im.width * cr) + 2, round(im.height * cr) + 2), Image.LANCZOS)
            canvas = canvas.crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(28))
            canvas = Image.blend(canvas, Image.new("RGB", (W, H), "#000000"), 0.35)
        else:
            canvas = Image.new("RGB", (W, H), bg or im.getpixel((2, 2)))
        canvas.paste(inner, ((W - inner.width) // 2, (H - inner.height) // 2))
        im = canvas
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


# --------------------------------------------------------------------------
# SVG document
# --------------------------------------------------------------------------
BASE_CSS = """
.sans{font-family:DevlopnSans,Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
.mono{font-family:DevlopnMono,'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.serif{font-family:Georgia,'Times New Roman','Noto Serif',serif}
.rise{animation:rise .9s cubic-bezier(.2,.7,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2.6s ease-out infinite}
@keyframes pulse{0%{transform:scale(1);opacity:.6}70%,100%{transform:scale(3.4);opacity:0}}
.draw{animation:draw 1.3s cubic-bezier(.2,.7,.2,1) both}
@keyframes draw{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


class Svg:
    def __init__(self, w: float, h: float, title: str, desc: str = ""):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.parts: list[str] = []
        self.defs: list[str] = []
        self.used = {"sans": set(), "mono": set()}

    def add(self, *parts: str) -> None:
        self.parts.extend(parts)

    def text(self, x, y, s, font="sans", size=16, weight=400, fill="#000", anchor="start",
             ls=0.0, extra="") -> str:
        if font in self.used:
            self.used[font].update(s)
        attrs = [f'x="{x:.1f}"', f'y="{y:.1f}"', f'class="{font}"', f'font-size="{size}"',
                 f'fill="{fill}"']
        if weight != 400:
            attrs.append(f'font-weight="{weight}"')
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if ls:
            attrs.append(f'letter-spacing="{ls}"')
        if extra:
            attrs.append(extra)
        return f"<text {' '.join(attrs)}>{escape(s)}</text>"

    def render(self) -> str:
        faces = "".join(font_face(n, c) for n, c in self.used.items() if c)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:g}" height="{self.h:g}" '
            f'viewBox="0 0 {self.w:g} {self.h:g}" role="img" aria-labelledby="t d">'
            f'<title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>'
            f"<style>{faces}{BASE_CSS}</style>"
            f"<defs>{''.join(self.defs)}</defs>{''.join(self.parts)}</svg>"
        )


def delay(seconds: float) -> str:
    return f'style="animation-delay:{seconds:.2f}s"'


def star(cx: float, cy: float, r: float, fill: str) -> str:
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def arrow(x: float, baseline: float, size: float, color: str, width: float = 1.8) -> str:
    """North-east arrow drawn as a path (the embedded mono font has no ↗ glyph)."""
    top = baseline - size
    return (f'<path d="M{x:.1f} {baseline:.1f}L{x + size:.1f} {top:.1f}M{x + size * .3:.1f} {top:.1f}'
            f'H{x + size:.1f}V{top + size * .7:.1f}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def label_with_arrow(svg: Svg, cx: float, baseline: float, label: str, size: float, weight: int,
                     color: str, ls: float, anchor: str = "middle") -> None:
    """Text followed by an arrow; cx is the centre (middle) or the right edge (end)."""
    tw = measure(label, "mono", size, ls=ls)
    gap, aw = size * 0.6, size * 0.62
    total = tw + gap + aw
    left = cx - total / 2 if anchor == "middle" else cx - total
    svg.add(svg.text(left, baseline, label, "mono", size, weight, color, ls=ls),
            arrow(left + tw + gap, baseline - size * 0.08, aw, color))


def chip(svg: Svg, x, y, label, t, font_size=13, fill=None, stroke=None, color=None, h=28, ls=0.8):
    w = measure(label, "mono", font_size, ls=ls) + 24
    svg.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
            f'fill="{fill or "none"}" stroke="{stroke or "none"}"/>')
    svg.add(svg.text(x + 12, y + h / 2 + font_size * 0.36, label, "mono", font_size, 500,
                     color or t["ink"], ls=ls))
    return w


# --------------------------------------------------------------------------
# Blocks
# --------------------------------------------------------------------------
def header(theme: str) -> Svg:
    t = THEMES[theme]
    s = Svg(1200, 520, "Jérémy Favier — Freelance Flutter Lead Developer",
            "From code to product, with perspective. Architecture, CI/CD and technical "
            "leadership; AI-assisted delivery and Flutter audits. Lyon, France and remote.")
    s.defs.append('<clipPath id="hero"><rect x="624" y="28" width="548" height="464" rx="18"/></clipPath>')
    s.add(f'<rect x=".5" y=".5" width="1199" height="519" rx="24" fill="{t["bg"]}" stroke="{t["line"]}"/>')
    x = 60
    s.add(f'<g class="rise">',
          f'<rect x="{x}" y="74" width="9" height="9" fill="{t["orange"]}"/>',
          s.text(x + 22, 84, "FREELANCE FLUTTER LEAD  ·  LYON & REMOTE", "mono", 15, 500, t["muted"], ls=1.4),
          s.text(x, 138, "Jérémy Favier", "sans", 27, 650, t["ink"], ls=-0.3),
          f'<line x1="{x}" y1="164" x2="568" y2="164" stroke="{t["line"]}"/></g>')
    size, lh, y0 = 60, 68, 232
    lines = ["From code", "to product,"]
    for i, line in enumerate(lines):
        s.add(f'<g class="rise" {delay(0.12 + i * 0.1)}>',
              s.text(x, y0 + i * lh, line, "sans", size, 720, t["ink"], ls=-1.8), "</g>")
    with_w = measure("with ", "sans", size, 700) - 1.8 * 5
    word = "perspective."
    word_w = measure(word, "serif", 64)
    y3 = y0 + 2 * lh
    s.add(f'<g class="rise" {delay(0.32)}>',
          s.text(x, y3, "with", "sans", size, 720, t["ink"], ls=-1.8),
          s.text(x + with_w, y3, word, "serif", 66, 400, t["orange"], ls=-0.5), "</g>")
    ux1, ux2, uy = x + with_w + 4, x + with_w + word_w - 6, y3 + 16
    length = ux2 - ux1 + 10
    s.add(f'<path class="draw" d="M{ux1:.1f} {uy:.1f} C {ux1 + length * .35:.1f} {uy - 6:.1f}, '
          f'{ux1 + length * .7:.1f} {uy + 3:.1f}, {ux2:.1f} {uy - 3:.1f}" fill="none" '
          f'stroke="{t["orange"]}" stroke-width="3" stroke-linecap="round" '
          f'stroke-dasharray="{length:.0f}" style="--len:{length:.0f};animation-delay:.8s"/>')
    s.add(f'<g class="rise" {delay(0.5)}>',
          s.text(x, 418, "Architecture · CI/CD · Technical lead", "sans", 20, 450, t["muted"]),
          s.text(x, 448, "AI-assisted delivery · Flutter audits", "sans", 20, 450, t["muted"]),
          "</g>")
    s.add(f'<g class="rise" {delay(0.6)}>',
          f'<line x1="{x}" y1="468" x2="568" y2="468" stroke="{t["line"]}"/>',
          s.text(x, 497, "DEVLOPN.COM", "mono", 14, 700, t["ink"], ls=1.4),
          f'<circle class="pulse" cx="{568 - measure("AVAILABILITY ON REQUEST", "mono", 13, ls=1.2) - 16}" cy="492.5" r="4" fill="{t["orange"]}"/>',
          f'<circle cx="{568 - measure("AVAILABILITY ON REQUEST", "mono", 13, ls=1.2) - 16}" cy="492.5" r="4" fill="{t["orange"]}"/>',
          s.text(568, 497, "AVAILABILITY ON REQUEST", "mono", 13, 500, t["muted"], "end", ls=1.2),
          "</g>")
    hero = image_uri(f"hero-{theme}-1040.webp", 548, 464, "cover", (0.5, 0.5), quality=82)
    s.add(f'<g class="rise" {delay(0.2)}>',
          f'<rect x="624" y="28" width="548" height="464" rx="18" fill="{t["surface"]}"/>',
          f'<image href="{hero}" x="624" y="28" width="548" height="464" '
          f'preserveAspectRatio="xMidYMid slice" clip-path="url(#hero)"/>',
          f'<rect x="624.5" y="28.5" width="547" height="463" rx="17.5" fill="none" stroke="{t["line"]}"/>',
          "</g>")
    return s


def button(theme: str, label: str, primary: bool) -> Svg:
    t = THEMES[theme]
    w = measure(label, "mono", 15, ls=1.4) + 15 * 1.22 + 44
    s = Svg(round(w + 2), 46, label.title())
    fill, stroke, color = (t["orange"], t["orange"], "#ffffff") if primary else (t["bg"], t["line"], t["ink"])
    if primary and theme == "dark":
        color = "#1a1310"
    s.add(f'<rect x="1" y="1" width="{w:.1f}" height="44" rx="22" fill="{fill}" stroke="{stroke}"/>')
    label_with_arrow(s, 1 + w / 2, 28.5, label, 15, 600, color, 1.4)
    return s


def proof(theme: str) -> Svg:
    t = THEMES[theme]
    s = Svg(1200, 176, "18 years in software development · 5.0/5 on Malt from 12 client reviews",
            "Worked with Renault Digital, SNCF Connect & Tech, Thales and Zanalys.")
    s.add(f'<rect x=".5" y=".5" width="1199" height="175" rx="20" fill="{t["bg"]}" stroke="{t["line"]}"/>')
    s.add(f'<line x1="300" y1="36" x2="300" y2="140" stroke="{t["line"]}"/>',
          f'<line x1="640" y1="36" x2="640" y2="140" stroke="{t["line"]}"/>')
    # 18 years
    lx = 48 + measure("18", "sans", 70, 720, -2) + 16
    s.add('<g class="rise">', s.text(48, 114, "18", "sans", 70, 720, t["ink"], ls=-2),
          s.text(lx, 74, "years in", "sans", 18, 450, t["muted"]),
          s.text(lx, 98, "software", "sans", 18, 450, t["muted"]),
          s.text(lx, 122, "development", "sans", 18, 450, t["muted"]),
          "</g>")
    # Malt rating
    nx = 340
    s.add(f'<g class="rise" {delay(.1)}>', s.text(nx, 100, "5.0", "sans", 64, 720, t["ink"], ls=-2))
    sx = nx + measure("5.0", "sans", 64, 720, -2) + 6
    s.add(s.text(sx, 100, "/ 5", "sans", 24, 600, t["muted"]))
    s.add(*[star(nx + 9 + i * 22, 128, 9, t["orange"]) for i in range(5)])
    s.add(s.text(nx + 122, 134, "12 reviews on Malt", "sans", 17, 450, t["muted"]), "</g>")
    # Clients
    cx = 680
    s.add(f'<g class="rise" {delay(.2)}>',
          f'<rect x="{cx}" y="44" width="8" height="8" fill="{t["orange"]}"/>',
          s.text(cx + 20, 53, "I’VE WORKED WITH", "mono", 13, 500, t["muted"], ls=1.6),
          s.text(cx, 96, "RENAULT DIGITAL  ·  SNCF CONNECT & TECH", "sans", 19, 720, t["ink"], ls=0.6),
          s.text(cx, 130, "THALES  ·  ZANALYS", "sans", 19, 720, t["ink"], ls=0.6),
          "</g>")
    return s


def section_title(theme: str, key: str) -> Svg:
    t = THEMES[theme]
    label, title, sub = SECTIONS[key]
    h = 150 if sub else 118
    s = Svg(1200, h, f"{label} — {title}", sub or "")
    s.add(f'<g class="rise">',
          f'<rect x="2" y="34" width="9" height="9" fill="{t["orange"]}"/>',
          s.text(24, 44, label, "mono", 15, 600, t["orangeText"], ls=1.8),
          s.text(0, 96, title, "sans", 42, 720, t["ink"], ls=-1.2))
    if sub:
        s.add(s.text(1, 134, sub, "sans", 19, 450, t["muted"]))
    s.add("</g>")
    return s


def expertise(theme: str) -> Svg:
    """Expertise cards on a two-column grid."""
    t = THEMES[theme]
    cols, gap, pad = 2, 24, 32
    w = (1198 - gap * (cols - 1)) / cols
    body = [wrap(text, w - 2 * pad, size=19) for _, text, _ in EXPERTISE]
    n = max(len(b) for b in body)
    title_size = 27
    while max(measure(e[0], "sans", title_size, 700, -0.6) for e in EXPERTISE) > w - 2 * pad:
        title_size -= 1
    ch = pad + 20 + 26 + 46 + n * 30 + 26 + 60 + pad
    rows = math.ceil(len(EXPERTISE) / cols)
    h = rows * ch + (rows - 1) * gap
    s = Svg(1200, h + 2, "Expertise: " + ", ".join(e[0].lower() for e in EXPERTISE),
            " ".join(f"{a}. {b}" for a, b, _ in EXPERTISE))
    for i, (title, _, tags) in enumerate(EXPERTISE):
        x = 1 + (i % cols) * (w + gap)
        top = 1 + (i // cols) * (ch + gap)
        y = top + pad
        s.add(f'<g class="rise" {delay(i * 0.1)}>',
              f'<rect x="{x:.1f}" y="{top:.1f}" width="{w:.1f}" height="{ch:.1f}" rx="20" fill="{t["bg"]}" stroke="{t["line"]}"/>',
              s.text(x + pad, y + 20, f"0{i + 1}", "mono", 15, 600, t["orangeText"], ls=1.2),
              s.text(x + pad, y + 64, title, "sans", title_size, 700, t["ink"], ls=-0.6))
        for j, line in enumerate(body[i]):
            s.add(s.text(x + pad, y + 104 + j * 30, line, "sans", 19, 420, t["muted"]))
        ty = top + ch - pad - 42
        s.add(f'<line x1="{x + pad:.1f}" y1="{ty - 18:.1f}" x2="{x + w - pad:.1f}" y2="{ty - 18:.1f}" stroke="{t["line"]}"/>')
        for j, tag in enumerate(tags):
            s.add(s.text(x + pad, ty + 8 + j * 24, tag, "mono", 13, 500, t["ink"], ls=0.8))
        s.add("</g>")
    return s


def experience(theme: str) -> Svg:
    t = THEMES[theme]
    pad, rail, cx = 48, 318, 352
    tw = 1200 - cx - pad
    rows, y = [], pad + 6
    for e in EXPERIENCE:
        lines = wrap(e["text"], tw, size=19)
        hgt = 34 + 30 + len(lines) * 30 + 16 + 30
        rows.append((e, lines, y, hgt))
        y += hgt + 44
    h = y - 44 + pad
    s = Svg(1200, h, "Experience: Renault Digital, SNCF Connect & Tech, Zanalys, Easivio, Thales",
            " ".join(f"{e['company']}, {e['role']} ({e['when'].title()}): {e['text']}" for e in EXPERIENCE))
    s.add(f'<rect x=".5" y=".5" width="1199" height="{h - 1}" rx="22" fill="{t["bg"]}" stroke="{t["line"]}"/>')
    s.add(f'<line x1="{rail}" y1="{pad + 10}" x2="{rail}" y2="{h - pad - 10}" stroke="{t["line"]}" stroke-width="2"/>')
    for i, (e, lines, y, hgt) in enumerate(rows):
        s.add(f'<g class="rise" {delay(i * 0.1)}>',
              s.text(pad, y + 22, e["when"], "mono", 14, 600, t["ink"], ls=1.0),
              s.text(pad, y + 48, e["sector"], "mono", 12, 500, t["orangeText"], ls=1.2))
        if e["current"]:
            s.add(f'<circle class="pulse" cx="{rail}" cy="{y + 16}" r="7" fill="{t["orange"]}"/>',
                  f'<circle cx="{rail}" cy="{y + 16}" r="7" fill="{t["orange"]}"/>')
        else:
            s.add(f'<circle cx="{rail}" cy="{y + 16}" r="7" fill="{t["bg"]}" stroke="{t["muted"]}" stroke-width="2"/>')
        s.add(s.text(cx, y + 26, e["company"], "sans", 28, 720, t["ink"], ls=-0.6),
              s.text(cx, y + 58, e["role"], "sans", 18, 500, t["orangeText"]))
        for j, line in enumerate(lines):
            s.add(s.text(cx, y + 92 + j * 30, line, "sans", 19, 420, t["muted"]))
        cxp = cx
        for tag in e["tags"]:
            cxp += chip(s, cxp, y + 92 + len(lines) * 30 - 8, tag.upper(), t, 12,
                        stroke=t["line"], color=t["ink"]) + 8
        s.add("</g>")
    return s


CARD_W, CARD_IMG = 560, 240


def product_card(theme: str, p: dict) -> Svg:
    t = THEMES[theme]
    pad = 28
    lines = wrap(p["text"], CARD_W - 2 * pad, size=18)
    if len(lines) > 3:
        print(f"  ! {p['name']}: description wraps to {len(lines)} lines")
    h = CARD_IMG + pad + 22 + 50 + 3 * 28 + 22 + 50 + 2
    s = Svg(CARD_W + 2, h, f"{p['name']} — {p['category'].title()}" + (f" · {p['status']}" if p["status"] else ""),
            f"{p['text']} Stack: {p['stack'].title()}.")
    s.defs.append(f'<clipPath id="img"><path d="M1 21a20 20 0 0 1 20-20h{CARD_W - 40}a20 20 0 0 1 20 20v{CARD_IMG - 20}h-{CARD_W}z"/></clipPath>')
    bg = p.get("bg")
    uri = image_uri(p["image"], CARD_W, CARD_IMG, p["mode"], p.get("focus", (0.5, 0.5)),
                    p.get("pad", 1.0), bg[theme] if isinstance(bg, dict) else bg)
    s.add('<g class="rise">',
          f'<rect x="1" y="1" width="{CARD_W}" height="{h - 2}" rx="20" fill="{t["bg"]}"/>',
          f'<image href="{uri}" x="1" y="1" width="{CARD_W}" height="{CARD_IMG}" '
          f'preserveAspectRatio="xMidYMid slice" clip-path="url(#img)"/>',
          f'<line x1="1" y1="{CARD_IMG + 1}" x2="{CARD_W + 1}" y2="{CARD_IMG + 1}" stroke="{t["line"]}"/>',
          f'<rect x="1.5" y="1.5" width="{CARD_W - 1}" height="{h - 3}" rx="19.5" fill="none" stroke="{t["line"]}"/>')
    if p.get("caption"):
        cw = measure(p["caption"], "mono", 11, ls=1.2) + 20
        s.add(f'<rect x="16" y="{CARD_IMG - 38}" width="{cw:.1f}" height="24" rx="12" fill="#000" fill-opacity=".55"/>',
              s.text(26, CARD_IMG - 22, p["caption"], "mono", 11, 500, "#ffffff", ls=1.2))
    y = CARD_IMG + pad
    s.add(s.text(pad + 1, y + 16, p["category"], "mono", 13, 500, t["muted"], ls=1.3))
    if p["status"]:
        label = p["status"].upper()
        cw = measure(label, "mono", 12, ls=1.0) + 26
        live = p["status"] != "Completed"
        s.add(f'<rect x="{CARD_W - pad - cw + 1:.1f}" y="{y - 2}" width="{cw:.1f}" height="26" rx="13" '
              f'fill="{t["orangeSoft"] if live else t["sage"]}"/>',
              s.text(CARD_W - pad + 1 - cw / 2, y + 15.5, label, "mono", 12, 600,
                     t["orangeText"] if live else t["muted"], "middle", ls=1.0))
    s.add(s.text(pad + 1, y + 64, p["name"], "sans", 32, 720, t["ink"], ls=-0.8))
    for j, line in enumerate(lines[:3]):
        s.add(s.text(pad + 1, y + 102 + j * 28, line, "sans", 18, 420, t["muted"]))
    by = h - 30
    s.add(f'<line x1="{pad + 1}" y1="{by - 30}" x2="{CARD_W - pad + 1}" y2="{by - 30}" stroke="{t["line"]}"/>',
          s.text(pad + 1, by, p["stack"], "mono", 12.5, 500, t["ink"], ls=0.8),
          )
    label_with_arrow(s, CARD_W - pad + 1, by, p["domain"], 12.5, 600, t["orangeText"], 0.4, "end")
    s.add("</g>")
    return s


def audit() -> Svg:
    a = AUDIT
    x, rx, rw = 56, 700, 444
    body = wrap("Before a release, a rewrite or a funding round: understand the risks and decide "
                "what to fix first. You receive a prioritised report that I review, contextualise "
                "and sign. Specialist AI agents support the analysis.", 540, size=19)
    platforms_y = 228 + len(body) * 30 + 20
    cta_y = platforms_y + 32
    h = max(cta_y + 48, 432) + 56
    s = Svg(1200, h, "DEVLOPN Audit — know where your app stands",
            "Before a release, a rewrite or a funding round: understand the risks and decide what to "
            "fix first. Three tiers from €990 excl. VAT, delivered in 5 to 10 working days, "
            "8 review areas, report reviewed and signed by Jérémy Favier.")
    s.defs.append('<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
                  f'<path d="M32 0H0V32" fill="none" stroke="{a["line"]}" stroke-opacity=".35"/></pattern>'
                  '<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".35" stop-color="#fff" stop-opacity="1"/></linearGradient>'
                  '<mask id="m"><rect width="1200" height="100%" fill="url(#fade)"/></mask>')
    s.add(f'<rect x=".5" y=".5" width="1199" height="{h - 1}" rx="24" fill="{a["bg"]}"/>',
          f'<rect x="560" y="1" width="639" height="{h - 2}" fill="url(#grid)" mask="url(#m)"/>',
          f'<rect x=".5" y=".5" width="1199" height="{h - 1}" rx="24" fill="none" stroke="{a["line"]}"/>')
    s.add('<g class="rise">',
          f'<rect x="{x}" y="58" width="9" height="9" fill="{a["mint"]}"/>',
          s.text(x + 22, 68, "DEVLOPN / AUDIT", "mono", 15, 600, a["mint"], ls=1.8),
          s.text(x, 128, "Know where your", "sans", 46, 720, a["ink"], ls=-1.4),
          s.text(x, 180, "app stands", "sans", 46, 720, a["ink"], ls=-1.4))
    for j, line in enumerate(body):
        s.add(s.text(x, 228 + j * 30, line, "sans", 19, 420, a["muted"]))
    s.add(s.text(x, platforms_y, "FLUTTER  ·  NATIVE iOS  ·  NATIVE ANDROID", "mono", 13, 500, a["mint"], ls=1.4))
    cta = "EXPLORE DEVLOPN AUDIT"
    cw = measure(cta, "mono", 14, ls=1.2) + 14 * 1.22 + 48
    s.add(f'<rect x="{x}" y="{cta_y}" width="{cw:.1f}" height="48" rx="24" fill="{a["mint"]}"/>')
    label_with_arrow(s, x + cw / 2, cta_y + 29.5, cta, 14, 700, a["bg"], 1.2)
    s.add("</g>")
    steps = [("01", "Understand the architecture", "Structure, state, dependencies"),
             ("02", "Identify the risks", "Security, performance, stores"),
             ("03", "Prioritise the next steps", "Recommendations with context")]
    for i, (n, title, sub) in enumerate(steps):
        y = 50 + i * 80
        s.add(f'<g class="rise" {delay(.15 + i * .1)}>',
              s.text(rx, y + 22, n, "mono", 15, 600, a["mint"], ls=1),
              s.text(rx + 48, y + 22, title, "sans", 22, 650, a["ink"], ls=-0.3),
              s.text(rx + 48, y + 50, sub, "sans", 17, 420, a["muted"]),
              f'<line x1="{rx}" y1="{y + 72}" x2="{rx + rw}" y2="{y + 72}" stroke="{a["line"]}"/>',
              "</g>")
    figs = [("8", "REVIEW AREAS"), ("5–10", "WORKING DAYS"), ("€990", "FROM, EXCL. VAT")]
    fw = rw / 3
    for i, (big, small) in enumerate(figs):
        fx = rx + i * fw
        s.add(f'<g class="rise" {delay(.5 + i * .08)}>',
              s.text(fx, 340, big, "sans", 40, 720, a["ink"], ls=-1),
              s.text(fx, 368, small, "mono", 11.5, 500, a["muted"], ls=1.0),
              "</g>")
    s.add(f'<g class="rise" {delay(.75)}>',
          f'<line x1="{rx}" y1="{h - 98}" x2="{rx + rw}" y2="{h - 98}" stroke="{a["line"]}"/>',
          f'<circle cx="{rx + 4}" cy="{h - 61}" r="4" fill="{a["mint"]}"/>',
          s.text(rx + 20, h - 56, "REVIEWED & SIGNED BY J. FAVIER", "mono", 13, 600, a["mint"], ls=1.4),
          "</g>")
    return s


def quotes(theme: str) -> Svg:
    t = THEMES[theme]
    gap, w, pad = 24, (1198 - 48) / 3, 32
    bodies = [wrap(q, w - 2 * pad, size=19) for q, *_ in QUOTES]
    roles = [wrap(role, w - 2 * pad - 62, size=14, weight=450) for _, _, role, _ in QUOTES]
    n = max(len(b) for b in bodies)
    nr = max(len(r) for r in roles)
    foot = 30 + nr * 20
    h = pad + 74 + n * 30 + 28 + foot + pad
    s = Svg(1200, h + 2, "Recommendations from Quentin Payré, Patrick Raguin and Marie Postic",
            " ".join(f"“{q}” — {name}, {role}." for q, name, role, _ in QUOTES))
    for i, (q, name, role, initials) in enumerate(QUOTES):
        x = 1 + i * (w + gap)
        s.add(f'<g class="rise" {delay(i * .12)}>',
              f'<rect x="{x:.1f}" y="1" width="{w:.1f}" height="{h:.1f}" rx="20" fill="{t["bg"]}" stroke="{t["line"]}"/>',
              s.text(x + pad - 4, 1 + pad + 52, "“", "serif", 84, 400, t["orange"]))
        for j, line in enumerate(bodies[i]):
            s.add(s.text(x + pad, 1 + pad + 74 + j * 30, line, "sans", 19, 420, t["ink"]))
        fy = h - pad - foot + 1
        s.add(f'<line x1="{x + pad:.1f}" y1="{fy - 16}" x2="{x + w - pad:.1f}" y2="{fy - 16}" stroke="{t["line"]}"/>',
              f'<circle cx="{x + pad + 22:.1f}" cy="{fy + 22}" r="22" fill="{t["sage"]}"/>',
              s.text(x + pad + 22, fy + 27, initials, "mono", 13, 700, t["ink"], "middle", ls=0.6),
              s.text(x + pad + 58, fy + 16, name, "sans", 17, 650, t["ink"]))
        for j, line in enumerate(roles[i]):
            s.add(s.text(x + pad + 58, fy + 38 + j * 20, line, "sans", 14, 450, t["muted"]))
        s.add("</g>")
    return s


def footer(theme: str) -> Svg:
    t = THEMES[theme]
    h = 300
    s = Svg(1200, h, "Need a Flutter lead on your team? Book a call",
            "Get in touch with your context and timeline. contact@devlopn.com · cal.com/devlopn")
    s.defs.append('<radialGradient id="glow" cx="1" cy="0" r="1">'
                  f'<stop offset="0" stop-color="{t["orange"]}" stop-opacity=".28"/>'
                  f'<stop offset="1" stop-color="{t["orange"]}" stop-opacity="0"/></radialGradient>')
    s.add(f'<rect x=".5" y=".5" width="1199" height="{h - 1}" rx="24" fill="{t["dark"]}" stroke="{t["darkLine"]}"/>',
          f'<rect x=".5" y=".5" width="1199" height="{h - 1}" rx="24" fill="url(#glow)"/>')
    x = 60
    s.add('<g class="rise">',
          f'<circle class="pulse" cx="{x + 4}" cy="70" r="4" fill="{t["orange"]}"/>',
          f'<circle cx="{x + 4}" cy="70" r="4" fill="{t["orange"]}"/>',
          s.text(x + 22, 75, "LET’S TALK", "mono", 15, 600, t["orange"], ls=1.8),
          s.text(x, 140, "Need a Flutter lead", "sans", 52, 720, t["onDark"], ls=-1.6),
          s.text(x, 198, "on your team?", "sans", 52, 720, t["onDark"], ls=-1.6),
          s.text(x, 248, "Tell me about your context and timeline: I’ll tell you where I stand.",
                 "sans", 19, 420, t["darkMuted"]),
          "</g>")
    cta = "BOOK A CALL"
    cw = measure(cta, "mono", 16, ls=1.4) + 16 * 1.22 + 60
    bx = 1200 - 60 - cw
    s.add(f'<g class="rise" {delay(.2)}>',
          f'<rect x="{bx:.1f}" y="112" width="{cw:.1f}" height="58" rx="29" fill="{t["orange"]}"/>')
    label_with_arrow(s, bx + cw / 2, 146.5, cta, 16, 700, "#ffffff" if theme == "light" else "#1a1310", 1.4)
    s.add(
          s.text(1140, 206, "cal.com/devlopn", "mono", 14, 500, t["darkMuted"], "end", ls=0.6),
          s.text(1140, 230, "contact@devlopn.com", "mono", 14, 500, t["darkMuted"], "end", ls=0.6),
          "</g>")
    return s


# --------------------------------------------------------------------------
def write(name: str, svg: Svg) -> None:
    path = OUT / f"{name}.svg"
    data = svg.render()
    path.write_text(data, encoding="utf-8")
    print(f"  {path.relative_to(ROOT)}  {len(data) / 1024:.0f} KB")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    write("audit", audit())
    for theme in THEMES:
        write(f"header-{theme}", header(theme))
        write(f"proof-{theme}", proof(theme))
        write(f"expertise-{theme}", expertise(theme))
        write(f"experience-{theme}", experience(theme))
        write(f"quotes-{theme}", quotes(theme))
        write(f"footer-{theme}", footer(theme))
        for key in SECTIONS:
            write(f"title-{key}-{theme}", section_title(theme, key))
        for slug, label, primary in BUTTONS:
            write(f"btn-{slug}-{theme}", button(theme, label, primary))
        for p in PRODUCTS:
            write(f"card-{p['slug']}-{theme}", product_card(theme, p))


if __name__ == "__main__":
    main()
