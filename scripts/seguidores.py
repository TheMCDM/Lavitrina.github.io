"""Actualiza seguidores.json con los números públicos de Instagram y TikTok.

Si una red no responde, se queda el número anterior (la página nunca queda vacía).
"""
import json
import re
import sys
import urllib.request
from datetime import date

IG_USER = "lavitrinaarteyregalos"
TT_USER = "lavitrina_"
ARCHIVO = "seguidores.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es,en;q=0.8", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_abrev(txt):
    """'27.1K' / '27,1 mil' / '1.2M' -> número."""
    t = txt.strip().lower().replace(",", ".")
    m = re.match(r"([\d.]+)\s*(k|mil|m|mill|millones)?", t)
    if not m:
        return None
    n = float(m.group(1))
    suf = m.group(2) or ""
    if suf in ("k", "mil"):
        n *= 1_000
    elif suf.startswith("m"):
        n *= 1_000_000
    return int(n)


def instagram():
    try:
        data = json.loads(get(
            f"https://i.instagram.com/api/v1/users/web_profile_info/?username={IG_USER}",
            {"x-ig-app-id": "936619743392459"}))
        return int(data["data"]["user"]["edge_followed_by"]["count"])
    except Exception as e:
        print("Instagram (API):", e)
    try:
        html = get(f"https://www.instagram.com/{IG_USER}/")
        m = re.search(r'"edge_followed_by":\{"count":(\d+)\}', html)
        if m:
            return int(m.group(1))
        m = re.search(r'content="([\d.,]+\s*[KkMm]?)\s*(?:Followers|seguidores)', html)
        if m:
            return parse_abrev(m.group(1))
    except Exception as e:
        print("Instagram (página):", e)
    return None


def tiktok():
    try:
        html = get(f"https://www.tiktok.com/@{TT_USER}")
        f = re.search(r'"followerCount":(\d+)', html)
        h = re.search(r'"heartCount":(\d+)', html) or re.search(r'"heart":(\d+)', html)
        return (int(f.group(1)) if f else None, int(h.group(1)) if h else None)
    except Exception as e:
        print("TikTok:", e)
        return (None, None)


def main():
    with open(ARCHIVO, encoding="utf-8") as fh:
        datos = json.load(fh)
    antes = dict(datos)

    ig = instagram()
    tt, likes = tiktok()
    # Ignorar valores raros (por ejemplo 0 o una caída de más de la mitad).
    for clave, nuevo in (("instagram", ig), ("tiktok", tt), ("tiktok_likes", likes)):
        viejo = datos.get(clave) or 0
        if nuevo and nuevo > viejo * 0.5:
            datos[clave] = nuevo
        print(f"{clave}: {viejo} -> {datos.get(clave)} (leído: {nuevo})")

    if datos != antes:
        datos["actualizado"] = date.today().isoformat()
        with open(ARCHIVO, "w", encoding="utf-8") as fh:
            json.dump(datos, fh, indent=2)
            fh.write("\n")
        print("seguidores.json actualizado")
    else:
        print("Sin cambios")
    return 0


if __name__ == "__main__":
    sys.exit(main())
