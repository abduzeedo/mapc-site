#!/usr/bin/env python3
"""Builds the static pages in this folder from pages/*.html (no dependencies, Python 3 standard library).

  python3 build.py

Each page in pages/ starts with `title:` and `description:` lines, a `---` line, then the HTML of <main>.
Placeholders in pages: {{icon:name}}, {{DOWNLOAD_URL}}, {{BUY_URL}}, {{EMAIL}}, {{SITE}}, {{VERSION}}.
Edit the settings below, rebuild, and commit the generated .html files.
"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SITE = "https://mapc.games"
EMAIL = "support@mapc.games"
BUY_URL = "https://abdz.gumroad.com/l/mapcpro"
RELEASES = "https://github.com/abduzeedo/mapc-site/releases"
DOWNLOAD_URL = RELEASES + "/latest/download/MaPC.dmg"
VERSION = "1.0"

ICONS = {
    "gamepad": '<path d="M6 8h12a4 4 0 0 1 4 4.2l-.6 4a2.6 2.6 0 0 1-4.5 1.3L15 15.5H9l-1.9 2a2.6 2.6 0 0 1-4.5-1.3l-.6-4A4 4 0 0 1 6 8z"/><path d="M8 11v3M6.5 12.5h3"/><circle cx="15.5" cy="11.5" r=".6"/><circle cx="17.5" cy="13.5" r=".6"/>',
    "bag": '<path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8a3 3 0 0 1 6 0"/>',
    "cube": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12L4 7.5M12 12v9"/>',
    "sliders": '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>',
    "window": '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 9h18"/>',
    "shield": '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z"/><path d="M9 12l2 2 4-4"/>',
    "code": '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>',
    "backup": '<path d="M7 18a4.5 4.5 0 0 1-.6-8.9A6 6 0 0 1 18 9.5a4 4 0 0 1-.5 8.5H7z"/><path d="M12 15V10M9.5 12.2L12 9.8l2.5 2.4"/>',
    "chart": '<path d="M5 20V10M12 20V4M19 20v-7"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6L7 7M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4"/>',
    "plusapp": '<rect x="4" y="4" width="16" height="16" rx="4"/><path d="M12 8v8M8 12h8"/>',
    "menubar": '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 9h18M15 7h3"/>',
    "wave": '<path d="M4 12h2M8 8v8M12 5v14M16 8v8M20 12h-2"/>',
    "trophy": '<path d="M8 4h8v5a4 4 0 0 1-8 0V4z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M9 20h6"/>',
    "gauge": '<path d="M4 16a8 8 0 1 1 16 0"/><path d="M12 16l4-5"/>',
    "sparkle": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/>',
    "command": '<path d="M9 9V6.5A2.5 2.5 0 1 0 6.5 9H9zm0 0h6m-6 0v6m6-6V6.5A2.5 2.5 0 1 1 17.5 9H15zm0 0v6m0 0h2.5a2.5 2.5 0 1 1-2.5 2.5V15zm0 0H9m0 0v2.5A2.5 2.5 0 1 1 6.5 15H9z"/>',
    "download": '<path d="M12 4v11M7.5 11L12 15.5 16.5 11M5 20h14"/>',
}

# A placeholder pixel "M" until the logo is chosen.
LOGO = ('<svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#1f0f1a"/>'
        '<g fill="#ffb873"><rect x="6" y="7" width="3.6" height="18"/><rect x="22.4" y="7" width="3.6" height="18"/>'
        '<rect x="9.6" y="10.6" width="3.6" height="3.6"/><rect x="18.8" y="10.6" width="3.6" height="3.6"/>'
        '<rect x="14.2" y="14.2" width="3.6" height="3.6"/></g></svg>')

CSP = ("default-src 'none'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; "
       "base-uri 'none'; form-action 'none'")

NAV = [("features", "Features", "index.html#features", True), ("support", "Support", "index.html#support", True),
       ("wall", "Wall of Fame", "wall.html", True), ("faq", "FAQ", "index.html#faq", True)]


def icon(name):
    return ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + "</svg>")


def layout(meta, body, filename):
    title, desc = html.escape(meta["title"], quote=True), html.escape(meta["description"], quote=True)
    url = SITE + "/" + ("" if filename == "index.html" else filename)
    nav = "".join(f'<li class="hide-sm"><a href="{href}">{label}</a></li>' for _, label, href, _ in NAV)
    ld = ""
    if filename == "index.html":
        ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"SoftwareApplication",'
              '"name":"MaPC","operatingSystem":"macOS 15+","applicationCategory":"GameApplication",'
              f'"description":"{desc}","url":"{SITE}/","publisher":{{"@type":"Organization","name":"Steale LLC"}},'
              '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}}</script>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="color-scheme" content="light dark">
<link rel="canonical" href="{url}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="styles.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap nav-shell"><nav class="nav" aria-label="Main">
<a class="brand" href="index.html" aria-label="MaPC home">{LOGO}<span>MaPC</span></a>
<ul>{nav}<li><a class="btn btn-primary btn-sm" href="index.html#download">Download</a></li></ul>
</nav></div>
<main id="main">
{body}
</main>
<footer><div class="wrap">
<div class="foot">
<div class="about"><a class="brand" href="index.html">{LOGO}<span>MaPC</span></a>
<p class="fade">Your PC games, on your Mac.<br>Made by Steale LLC.</p></div>
<div><h4>Product</h4><ul><li><a href="index.html#download">Download</a></li><li><a href="index.html#support">Support MaPC</a></li><li><a href="wall.html">Wall of Fame</a></li><li><a href="changelog.html">What&rsquo;s new</a></li></ul></div>
<div><h4>Help</h4><ul><li><a href="index.html#faq">FAQ</a></li><li><a href="mailto:{EMAIL}">{EMAIL}</a></li><li><a href="{RELEASES}">All releases</a></li></ul></div>
<div><h4>Legal</h4><ul><li><a href="privacy.html">Privacy</a></li><li><a href="terms.html">Terms &amp; refunds</a></li><li><a href="eula.html">License agreement</a></li><li><a href="opensource.html">Open source</a></li></ul></div>
</div>
<div class="legal">
<p>&copy; <span data-year>2026</span> Steale LLC. All rights reserved.</p>
<p>MaPC isn&rsquo;t affiliated with or endorsed by Valve, Epic Games, GOG, Apple or CodeWeavers. Steam, Epic Games, GOG, Apple, Mac, macOS, Metal and CrossOver are trademarks of their owners and are used only to say what MaPC works with.</p>
</div>
</div></footer>
<script src="site.js" defer></script>
</body>
</html>
"""


def fill(text):
    text = re.sub(r"\{\{icon:(\w+)\}\}", lambda m: icon(m.group(1)), text)
    for key, value in {"DOWNLOAD_URL": DOWNLOAD_URL, "BUY_URL": BUY_URL, "EMAIL": EMAIL, "SITE": SITE,
                       "VERSION": VERSION, "RELEASES": RELEASES}.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def main():
    for src in sorted((ROOT / "pages").glob("*.html")):
        head, _, body = src.read_text(encoding="utf-8").partition("\n---\n")
        meta = dict(line.split(":", 1) for line in head.strip().splitlines())
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        (ROOT / src.name).write_text(layout(meta, fill(body.strip()), src.name), encoding="utf-8")
        print("built", src.name)

    # The license agreement is plain text.
    eula = html.escape((ROOT / "pages" / "eula.txt").read_text(encoding="utf-8").strip())
    body = f'<div class="wrap"><article class="doc"><h1>License agreement</h1><pre>{eula}</pre></article></div>'
    meta = {"title": "License agreement — MaPC", "description": "The MaPC end user license agreement."}
    (ROOT / "eula.html").write_text(layout(meta, body, "eula.html"), encoding="utf-8")
    print("built eula.html")

    (ROOT / "favicon.svg").write_text(LOGO.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1), encoding="utf-8")
    pages = ["", "wall.html", "changelog.html", "privacy.html", "terms.html", "opensource.html", "eula.html"]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{SITE}/{p}</loc></url>\n" for p in pages) + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    (ROOT / "CNAME").write_text("mapc.games\n", encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    if not (ROOT / "supporters.json").exists():
        (ROOT / "supporters.json").write_text('{\n  "updated": "",\n  "supporters": []\n}\n', encoding="utf-8")


if __name__ == "__main__":
    main()
