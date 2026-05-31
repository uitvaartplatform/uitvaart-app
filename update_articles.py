#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Haalt de nieuwste artikelen van Uitvaart-Platform.nl en schrijft ze naar
articles.json, zodat de carrousel in de app automatisch actueel blijft.
Gebruikt alleen standaard Python, dus er is geen installatie nodig.
Bij twijfel of een fout blijft het bestaande articles.json gewoon staan.
"""
import json
import re
import sys
import urllib.request

BRON = "https://uitvaart-platform.nl/artikelen"
SITE = "https://uitvaart-platform.nl"
MAX_ARTIKELEN = 8
UITVOER = "articles.json"


def haal_op(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; UitvaartPlatformBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        ruw = resp.read()
    return ruw.decode("utf-8", "replace")


def main():
    try:
        html = haal_op(BRON)
    except Exception as fout:
        print("Kon de pagina niet ophalen:", fout)
        sys.exit(0)  # niet falen, bestaande lijst blijft staan

    anchor_re = re.compile(
        r'<a\b[^>]*href="([^"]*/artikelen/[^"#?]+)"[^>]*>(.*?)</a>',
        re.I | re.S,
    )
    img_re = re.compile(r"<img\b[^>]*>", re.I)
    bron_re = re.compile(r'(?:src|data-src|data-original)="([^"]+)"', re.I)
    alt_re = re.compile(r'alt="([^"]*)"', re.I)

    data = {}
    volgorde = []

    for m in anchor_re.finditer(html):
        href = m.group(1)
        binnen = m.group(2)
        url = href if href.startswith("http") else SITE + href
        if url not in data:
            data[url] = {"i": "", "t": ""}
            volgorde.append(url)

        imgs = img_re.findall(binnen)
        if imgs:
            bronnen = bron_re.findall(imgs[0])
            foto = next((b for b in bronnen if "_images" in b), bronnen[0] if bronnen else "")
            if foto and not data[url]["i"]:
                data[url]["i"] = foto
            alt = alt_re.search(imgs[0])
            if alt and alt.group(1).strip() and not data[url]["t"]:
                data[url]["t"] = alt.group(1).strip()
        else:
            tekst = re.sub(r"<[^>]+>", " ", binnen)
            tekst = re.sub(r"\s+", " ", tekst).strip()
            if tekst and not data[url]["t"]:
                data[url]["t"] = tekst

    artikelen = []
    for url in volgorde:
        d = data[url]
        if not d["i"]:
            continue  # de carrousel heeft een foto nodig
        titel = d["t"] or url.rsplit("/", 1)[-1].replace("-", " ").capitalize()
        foto = d["i"]
        if foto.startswith("//"):
            foto = "https:" + foto
        artikelen.append({"t": titel, "s": url, "i": foto, "c": "", "d": ""})
        if len(artikelen) >= MAX_ARTIKELEN:
            break

    if not artikelen:
        print("Geen artikelen gevonden, bestaande articles.json blijft staan.")
        sys.exit(0)

    with open(UITVOER, "w", encoding="utf-8") as f:
        json.dump(artikelen, f, ensure_ascii=False, indent=2)
    print("articles.json bijgewerkt met", len(artikelen), "artikelen.")


if __name__ == "__main__":
    main()
