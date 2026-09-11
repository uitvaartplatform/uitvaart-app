#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Haalt de nieuwste artikelen van Uitvaart-Platform.nl en schrijft ze naar
articles.json, zodat de carrousel in de app automatisch actueel blijft.

Werkwijze (versie 2, klaar voor site 3.0):
  1. Probeer eerst de vaste feed:  https://uitvaart-platform.nl/artikelen-feed.json
     Die wordt door de nieuwe site (3.0) bij elke bouw meegeleverd en is de
     betrouwbaarste bron: geen gepuzzel in HTML, altijd de juiste afbeeldingen.
  2. Bestaat de feed (nog) niet, dan wordt de artikelenpagina zelf uitgelezen,
     zoals voorheen. Dat werkt met zowel de oude als de nieuwe opmaak.

Gebruikt alleen standaard Python, dus er is geen installatie nodig.
Bij twijfel of een fout blijft het bestaande articles.json gewoon staan.
"""
import html
import json
import re
import sys
import urllib.request

SITE = "https://uitvaart-platform.nl"
FEED = SITE + "/artikelen-feed.json"
BRON = SITE + "/artikelen"
MAX_ARTIKELEN = 8
UITVOER = "articles.json"


def haal_op(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; UitvaartPlatformBot/2.0)"},
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        ruw = resp.read()
    return ruw.decode("utf-8", "replace")


def maak_absoluut(url):
    """Maakt van elk soort adres een volledig https-adres."""
    url = html.unescape((url or "").strip())
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("/"):
        return SITE + url
    return SITE + "/" + url


def bruikbare_foto(url):
    """Geen svg-icoontjes, geen ingebedde data-plaatjes."""
    if not url:
        return False
    laag = url.lower().split("?")[0]
    if laag.startswith("data:"):
        return False
    if laag.endswith(".svg"):
        return False
    return True


# ---------------------------------------------------------------- 1. de feed
def via_feed():
    """Leest artikelen-feed.json van de nieuwe site. Geeft een lijst terug,
    of None als de feed niet bestaat of niet klopt."""
    try:
        ruw = haal_op(FEED)
        lijst = json.loads(ruw)
    except Exception:
        return None
    if not isinstance(lijst, list):
        return None

    artikelen = []
    for item in lijst:
        if not isinstance(item, dict):
            continue
        titel = html.unescape(str(item.get("t") or item.get("titel") or "").strip())
        link = maak_absoluut(str(item.get("s") or item.get("url") or ""))
        foto = maak_absoluut(str(item.get("i") or item.get("foto") or ""))
        if not titel or "/artikelen/" not in link or not bruikbare_foto(foto):
            continue
        artikelen.append({"t": titel, "s": link, "i": foto, "c": "", "d": ""})
        if len(artikelen) >= MAX_ARTIKELEN:
            break

    # Alleen bruikbaar als de feed echt wat oplevert.
    return artikelen if artikelen else None


# ------------------------------------------------- 2. de pagina zelf uitlezen
def via_pagina():
    try:
        pagina = haal_op(BRON)
    except Exception as fout:
        print("Kon de pagina niet ophalen:", fout)
        return None

    anchor_re = re.compile(
        r'<a\b[^>]*href="([^"]*/artikelen/[^"#?]+)"[^>]*>(.*?)</a>',
        re.I | re.S,
    )
    img_re = re.compile(r"<img\b[^>]*>", re.I)
    bron_re = re.compile(r'(?:src|data-src|data-original|data-lazy-src)="([^"]+)"', re.I)
    alt_re = re.compile(r'alt="([^"]*)"', re.I)

    data = {}
    volgorde = []

    for m in anchor_re.finditer(pagina):
        url = maak_absoluut(m.group(1))
        binnen = m.group(2)
        if url not in data:
            data[url] = {"i": "", "t": ""}
            volgorde.append(url)

        for img in img_re.findall(binnen):
            bronnen = [maak_absoluut(b) for b in bron_re.findall(img)]
            bronnen = [b for b in bronnen if bruikbare_foto(b)]
            if bronnen and not data[url]["i"]:
                # Voorkeur voor echte artikelfoto's: oude opmaak (_images)
                # en nieuwe opmaak (/foto/). Anders de eerste de beste.
                foto = next(
                    (b for b in bronnen if "_images" in b or "/foto/" in b),
                    bronnen[0],
                )
                data[url]["i"] = foto
            alt = alt_re.search(img)
            if alt and alt.group(1).strip() and not data[url]["t"]:
                data[url]["t"] = html.unescape(alt.group(1).strip())

        if not data[url]["t"]:
            tekst = re.sub(r"<[^>]+>", " ", binnen)
            tekst = html.unescape(re.sub(r"\s+", " ", tekst).strip())
            if tekst:
                data[url]["t"] = tekst

    artikelen = []
    for url in volgorde:
        d = data[url]
        if not d["i"]:
            continue  # de carrousel heeft een foto nodig
        titel = d["t"] or url.rsplit("/", 1)[-1].replace("-", " ").capitalize()
        artikelen.append({"t": titel, "s": url, "i": d["i"], "c": "", "d": ""})
        if len(artikelen) >= MAX_ARTIKELEN:
            break

    return artikelen if artikelen else None


def main():
    artikelen = via_feed()
    herkomst = "feed"
    if artikelen is None:
        artikelen = via_pagina()
        herkomst = "pagina"

    if not artikelen:
        print("Geen artikelen gevonden, bestaande articles.json blijft staan.")
        sys.exit(0)

    with open(UITVOER, "w", encoding="utf-8") as f:
        json.dump(artikelen, f, ensure_ascii=False, indent=2)
    print("articles.json bijgewerkt met", len(artikelen), "artikelen (via", herkomst + ").")


if __name__ == "__main__":
    main()
