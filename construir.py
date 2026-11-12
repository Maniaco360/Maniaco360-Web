#!/usr/bin/env python3
"""Genera la web de Maniaco360 a partir de contenido/.  Solo biblioteca estandar."""
import json, re, shutil, html, os, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

R = Path(__file__).resolve().parent
OUT = R / "salida"
S = json.loads((R / "contenido/sitio.json").read_text("utf-8"))
BASE = S["base"].rstrip("/")

# ---------- utilidades ----------
def e(t): return html.escape(str(t), quote=True)
def nl(t): return e(t).replace("\n", "<br>")
def crudo(t): return str(t).replace("\n", "<br>")   # permite <em> en sitio.json

def front_matter(txt):
    if not txt.startswith("---"):
        return {}, txt
    _, fm, cuerpo = txt.split("---", 2)
    datos, actual, modo = {}, None, None
    for linea in fm.strip("\n").split("\n"):
        if not linea.strip():
            continue
        if linea.startswith("  - ") and actual:
            datos[actual].append(json.loads(linea.strip()[2:].strip()))
            continue
        if linea.startswith("  ") and actual and modo == "dict":
            k, v = linea.strip().split(":", 1)
            datos[actual][k.strip()] = int(v.strip())
            continue
        k, v = linea.split(":", 1)
        k, v = k.strip(), v.strip()
        if v == "":
            actual = k
            modo = "dict" if k == "notas" else "list"
            datos[k] = {} if modo == "dict" else []
        else:
            actual, modo = None, None
            if v[:1] == '"' and v[-1:] == '"':
                v = json.loads(v)
            elif v.isdigit():
                v = int(v)
            datos[k] = v
    return datos, cuerpo.strip("\n")

def md_inline(t):
    t = e(t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t

def md(texto):
    out, lista = [], []
    def cerrar():
        if lista:
            out.append("<ul>" + "".join(f"<li>{md_inline(x)}</li>" for x in lista) + "</ul>")
            lista.clear()
    for bloque in texto.split("\n"):
        b = bloque.strip()
        if not b:
            cerrar(); continue
        if b.startswith("### "):
            cerrar(); out.append(f"<h3>{md_inline(b[4:])}</h3>")
        elif b.startswith("## "):
            cerrar(); out.append(f'<h2 id="{slugify(b[3:])}">{md_inline(b[3:])}</h2>')
        elif b.startswith("> "):
            cerrar(); out.append(f"<blockquote>{md_inline(b[2:])}</blockquote>")
        elif b.startswith("- "):
            lista.append(b[2:])
        else:
            cerrar(); out.append(f"<p>{md_inline(b)}</p>")
    cerrar()
    return "\n".join(out)

def slugify(t):
    t = t.lower()
    for a, b in zip("áéíóúñ", "aeioun"): t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]

def fecha_es(f):
    d = datetime.strptime(f, "%Y-%m-%d")
    return f"{d.day:02d}/{d.month:02d}/{d.year}"

ICONO = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32'"
         " rx='6' fill='%23fa4936'/%3E%3Cpath d='M6 24V8h5l5 8 5-8h5v16h-5V16l-5 7-5-7v8z' fill='%23101011'/%3E%3C/svg%3E")

def cabeza(titulo, desc, url, imagen, tipo="website", extra=""):
    img = f"{BASE}/images/{imagen}" if imagen else ""
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#101011">
<title>{e(titulo)}</title>
<meta name="description" content="{e(desc)}">
<link rel="icon" type="image/svg+xml" href="{ICONO}">
<link rel="stylesheet" href="/style.css">
<link rel="canonical" href="{e(url)}">
<link rel="alternate" type="application/rss+xml" title="Reviews de Maniaco360" href="{BASE}/feed.xml">
<meta property="og:site_name" content="Maniaco360">
<meta property="og:locale" content="es_ES">
<meta property="og:type" content="{tipo}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(img)}">
<meta property="og:image:width" content="1600"><meta property="og:image:height" content="900">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(titulo)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(img)}">
{extra}</head><body>"""

def cabecera(activo):
    def a(href, txt, ident="", clase=""):
        if ident and ident == activo:
            clase = (clase + " active").strip()
        c = f' class="{clase}"' if clase else ""
        return f'<a href="{href}"{c}>{txt}</a>'
    r = S["redes"]
    return f"""<a class="skip" href="#contenido">Saltar al contenido</a><header>
<div class="masthead wrap"><a class="brand" href="/" aria-label="Maniaco360, inicio"><span>MANIACO<span class="red">360</span></span></a>
<span class="brand-note">Videojuegos con criterio propio</span>
<a class="youtube-top" href="{r['youtube']}" target="_blank" rel="noopener noreferrer"><span aria-hidden="true">YouTube</span><span aria-hidden="true">↗</span></a></div>
<nav class="wrap" aria-label="Principal">{a('/#contenido','Inicio','inicio')}{a('/reviews/','Reviews y opiniones','reviews')}{a('/#videos','Vídeos')}{a('/#desarrollo','Diario de desarrollo')}{a('/#sobre-mi','Sobre mí','','nav-about')}</nav></header>"""

PIE = f"""<footer class="wrap site-footer"><p>Maniaco360 · {S['autor']} · <a href="mailto:{S['email']}">{S['email']}</a></p>
<p class="muted">Las imágenes promocionales pertenecen a sus respectivos estudios y editoras.</p></footer>"""

def tarjeta_video(v):
    f = datetime.strptime(v["fecha"], "%Y-%m-%d")
    meses = "ene feb mar abr may jun jul ago sep oct nov dic".split()
    legible = f"{f.day} {meses[f.month - 1]} {f.year}"
    return (f'<article class="video-card"><a href="{e(v["url"])}" target="_blank" rel="noopener noreferrer">'
            f'<img src="{e(v["miniatura"])}" alt="" width="480" height="360" loading="lazy">'
            f'<div class="video-copy"><time datetime="{v["fecha"]}">{legible}</time>'
            f'<h4>{e(v["titulo"])}</h4><span class="text-link">Ver en YouTube ↗</span></div></a></article>')

def playlist(bloque):
    pid, tit = bloque["playlist"], bloque["playlist_titulo"]
    feed = "reviews" if "Veredicto" in tit else "development"
    vids = VIDEOS.get(feed, [])[:3]
    contenido = ("".join(tarjeta_video(v) for v in vids) if vids else
                 '<p class="video-status">Todavía no hay vídeos publicados en esta lista. '
                 'El primero aparecerá aquí cuando esté disponible.</p>')
    return f"""<div class="playlist-block"><h3>{e(tit)}</h3>
<div class="video-feed">{contenido}</div>
<a class="text-link" href="https://www.youtube.com/playlist?list={pid}" target="_blank" rel="noopener noreferrer">Ver lista en YouTube ↗</a>
<details class="playlist-embed" data-playlist="{pid}" data-title="{e(tit)}"><summary>Ver el reproductor aquí</summary>
<p class="embed-note">Al abrirlo, se carga contenido de YouTube. Si no se reproduce, utiliza el enlace a la lista.</p>
<div class="playlist-player"></div></details></div>"""

PEQUENAS = set()          # imagenes con version reducida disponible

def img_tag(rev, clase, lazy=True):
    n = rev["imagen"]
    chico = n.replace(".webp", "-800.webp")
    alt = e(rev.get("imagen_alt") or rev["juego"])
    carga = ' loading="lazy"' if lazy else ""
    srcset = (f' srcset="/images/{chico} 800w, /images/{n} 1600w"'
              f' sizes="(max-width: 700px) 100vw, 700px"') if n in PEQUENAS else ""
    return (f'<img src="/images/{n}"{srcset} alt="{alt}" '
            f'width="1600" height="900" class="{clase}"{carga}>')

# ---------- lista de videos de YouTube ----------
CACHE_VIDEOS = R / "contenido/videos.json"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "media": "http://search.yahoo.com/mrss/"}

def descargar_lista(pid):
    url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={pid}"
    with urllib.request.urlopen(url, timeout=20) as r:
        raiz = ET.fromstring(r.read())
    salida = []
    for en in raiz.findall("a:entry", NS)[:6]:
        mg = en.find("media:group", NS)
        salida.append({
            "id": en.findtext("yt:videoId", "", NS),
            "titulo": en.findtext("a:title", "", NS),
            "url": en.find("a:link", NS).get("href"),
            "fecha": en.findtext("a:published", "", NS)[:10],
            "miniatura": mg.find("media:thumbnail", NS).get("url") if mg is not None else "",
        })
    return salida

def cargar_videos():
    cache = json.loads(CACHE_VIDEOS.read_text("utf-8")) if CACHE_VIDEOS.exists() else {}
    listas = {"reviews": S["secciones"]["videos"]["playlist"],
              "development": S["secciones"]["desarrollo"]["playlist"]}
    nuevo, cambios = dict(cache), False
    for clave, pid in listas.items():
        try:
            nuevo[clave] = descargar_lista(pid)
            cambios = True
        except Exception as err:
            print(f"Aviso: no se pudo actualizar la lista {clave} ({err}); se usa la copia guardada.")
    if cambios:
        CACHE_VIDEOS.write_text(json.dumps(nuevo, ensure_ascii=False, indent=1), "utf-8")
    return nuevo

VIDEOS = cargar_videos()

# ---------- cargar reviews ----------
revs = []
for f in sorted((R / "contenido/reviews").glob("*.md")):
    datos, cuerpo = front_matter(f.read_text("utf-8"))
    datos["cuerpo"] = cuerpo
    datos.setdefault("slug", f.stem)
    datos["url"] = f"{BASE}/reviews/{datos['slug']}/"
    revs.append(datos)
revs.sort(key=lambda r: r["fecha"], reverse=True)
ALT = {r["slug"]: r.get("imagen_alt") for r in revs}

# ---------- fragmentos ----------
def anillo(nombre, valor):
    return (f'<div class="rating-item"><div class="rating-ring" style="--rating:{valor}%" role="img" '
            f'aria-label="{e(nombre)}: {valor} sobre 100"><span aria-hidden="true">{valor}<small>/100</small></span></div>'
            f'<h3>{e(nombre)}</h3></div>')

def caja_notas(r):
    anillos = "".join(anillo(k, v) for k, v in r["notas"].items())
    mejor = "".join(f"<li>{e(x)}</li>" for x in r.get("lo_mejor", []))
    falta = "".join(f"<li>{e(x)}</li>" for x in r.get("lo_falta", []))
    return f"""<section class="review-summary" aria-labelledby="summary-title">
<div class="summary-top"><div><span class="eyebrow red">MI VALORACIÓN</span><h2 id="summary-title">De un vistazo</h2>
<p>{e(r.get('resumen',''))}</p></div>
<div class="summary-total"><span class="eyebrow">Valoración final</span><strong>{r['final']}<span>/100</span></strong></div></div>
<div class="summary-points"><div><h3>Lo mejor</h3><ul>{mejor}</ul></div><div><h3>Lo que me falta</h3><ul>{falta}</ul></div></div>
<div class="rating-grid" aria-label="Las cuatro notas de Maniaco360">{anillos}</div></section>"""

def tarjeta_grande(r):
    return (f'<a class="review-card" href="/reviews/{r["slug"]}/">{img_tag(r, "review-card-art")}'
            f'<div><span class="eyebrow red">{e(r["juego"])}</span><h3>{e(r["subtitulo"]).capitalize()}.</h3>'
            f'<p>{e(r.get("resumen",""))}</p><time datetime="{r["fecha"]}">{fecha_es(r["fecha"])}</time>'
            f'<span class="text-link">Leer la review ↗</span></div>'
            f'<div class="card-score" aria-label="Nota: {r["final"]} sobre 100">{r["final"]}<span>/100</span></div></a>')

def tarjeta(r):
    return (f'<article class="archive-card"><a href="/reviews/{r["slug"]}/"><div class="archive-image">{img_tag(r, "")}'
            f'<span class="archive-score" aria-label="Nota: {r["final"]} sobre 100">{r["final"]}<small>/100</small></span></div>'
            f'<div class="archive-copy"><time datetime="{r["fecha"]}">{fecha_es(r["fecha"])}</time>'
            f'<span class="eyebrow red">{e(r["juego"])}</span><h3>{e(r["subtitulo"]).capitalize()}.</h3>'
            f'<p>{e(r.get("resumen",""))}</p><span class="text-link">Leer la review ↗</span></div></a></article>')

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"

def ld_review(r):
    return ld({"@context": "https://schema.org", "@type": "Review",
               "itemReviewed": {"@type": "VideoGame", "name": r["juego"]},
               "author": {"@type": "Person", "name": S["autor"], "url": f"{BASE}/#sobre-mi"},
               "publisher": {"@type": "Organization", "name": S["nombre"], "url": BASE + "/"},
               "datePublished": r["fecha"], "inLanguage": "es",
               "reviewRating": {"@type": "Rating", "ratingValue": r["final"], "bestRating": 100, "worstRating": 0},
               "name": f'{r["juego"]} — {r["subtitulo"]}', "reviewBody": r.get("resumen", ""),
               "url": r["url"], "image": f'{BASE}/images/{r["imagen"]}'})

# ---------- paginas ----------
def pagina_review(r):
    extra = ld_review(r)
    head = cabeza(f'{r["juego"]} — {r["subtitulo"]} | Maniaco360', r.get("descripcion", ""), r["url"],
                  r["imagen"], "article", extra)
    cuerpo = r["cuerpo"]
    if r.get("resumen") and cuerpo.startswith(r["resumen"]):
        cuerpo = cuerpo[len(r["resumen"]):].lstrip("\n")
    video = ""
    if r.get("video"):
        vid = r["video"].split("v=")[-1].split("&")[0]
        video = (f'<section class="playlist-block"><h3>La review en vídeo</h3>'
                 f'<details class="playlist-embed" data-video="{e(vid)}"><summary>Ver el vídeo aquí</summary>'
                 f'<p class="embed-note">Al abrirlo, se carga contenido de YouTube.</p><div class="playlist-player">'
                 f'<iframe loading="lazy" width="560" height="315" src="https://www.youtube-nocookie.com/embed/{e(vid)}" '
                 f'title="{e(r["juego"])} en vídeo" frameborder="0" allowfullscreen></iframe></div></details>'
                 f'<a class="text-link" href="{e(r["video"])}" target="_blank" rel="noopener noreferrer">Ver en YouTube ↗</a></section>')
    otras = [x for x in revs if x["slug"] != r["slug"]][:3]
    relacionadas = ('<section class="content-section"><div class="section-title"><div>'
                    '<span class="eyebrow red">SIGUE LEYENDO</span><h2>Otras reviews<span class="red">.</span></h2></div>'
                    '<a class="text-link" href="/reviews/">Todas las reviews ↗</a></div>'
                    '<div class="archive-grid home-recent">' + "".join(tarjeta(x) for x in otras) + "</div></section>")
    return f"""{head}{cabecera('reviews')}
<main class="wrap review-page" id="contenido">
<a class="text-link" href="/reviews/">← Todas las reviews</a>
<article><div class="review-heading"><span class="eyebrow red">{e(r['juego'])}</span>
<h1>{e(r['juego'])} — {e(r['subtitulo'])}</h1>
<p class="review-deck">{e(r.get('resumen',''))}</p>
<div class="review-meta"><span><a href="/#sobre-mi">{e(S['autor'])}</a></span>
<time datetime="{r['fecha']}">{fecha_es(r['fecha'])}</time><span>Veredicto 360</span></div></div>
{img_tag(r, 'review-card-art', lazy=False)}
{caja_notas(r)}
{md(cuerpo)}
{video}</article>
{relacionadas}</main>{PIE}<script src="/playlists.js" defer></script></body></html>"""

def pagina_indice():
    url = f"{BASE}/reviews/"
    lista = ld({"@context": "https://schema.org", "@type": "ItemList", "name": "Reviews de Maniaco360",
                "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": r["url"], "name": r["juego"]}
                                    for i, r in enumerate(revs)]})
    head = cabeza("Todas las reviews | Maniaco360",
                  "Reviews de videojuegos con criterio propio. Las notas de Maniaco360, sus puntos fuertes y lo que les falta.",
                  url, revs[0]["imagen"], "website", lista)
    return f"""{head}{cabecera('reviews')}
<main class="wrap" id="contenido">
<div class="section-line"><span>CON CRITERIO PROPIO</span><span>{len(revs):02d} reviews</span></div>
<section class="content-section"><div class="section-title"><div><span class="eyebrow red">EL ARCHIVO</span>
<h1>Todas las reviews<span class="red">.</span></h1></div></div>
<div class="archive-grid">{"".join(tarjeta(r) for r in revs)}</div></section></main>{PIE}</body></html>"""

def pagina_inicio():
    p, sec = S["portada"], S["secciones"]
    temas = "".join(
        f'<a class="topic" href="{t["href"]}"><span class="topic-number">{t["n"]}</span><div>'
        f'<span class="eyebrow red">{e(t["eyebrow"])}</span><h2>{nl(t["titulo"])}</h2><p>{e(t["texto"])}</p></div>'
        f'<span class="topic-arrow" aria-hidden="true">↗</span></a>' for t in p["temas"])
    r = S["redes"]
    redes = "".join(f'<a href="{v}" target="_blank" rel="noopener noreferrer"><span>{k.capitalize()} ↗</span></a>'
                    for k, v in r.items())
    sitio_ld = ld({"@context": "https://schema.org", "@type": "WebSite", "name": S["nombre"], "url": BASE + "/",
                   "inLanguage": "es", "author": {"@type": "Person", "name": S["autor"]},
                   "description": S["descripcion"]})
    head = cabeza(S["titulo"], S["descripcion"], BASE + "/", p["imagen"], "website", sitio_ld)
    resto = "".join(tarjeta(x) for x in revs[1:4])
    sm = S["secciones"]["sobre_mi"]
    return f"""{head}{cabecera('inicio')}
<main class="wrap" id="contenido">
<div class="section-line"><span>{e(p['linea'][0])}</span><span>{e(p['linea'][1])}</span></div>
<section class="feature-grid" aria-label="Presentación de Maniaco360">
<article class="feature"><img class="hero-art" src="/images/{p['imagen']}" alt="{e(p['imagen_alt'])}" width="1536" height="1024" fetchpriority="high">
<div class="feature-shade"></div><div class="feature-content"><span class="badge">{e(p['badge'])}</span>
<h1>{nl(p['titulo'])}</h1><p>{nl(p['texto'])}</p>
<a class="white-button" href="#sobre-mi">{e(p['boton'])} <span aria-hidden="true">↗</span></a></div>
<span class="art-note">{e(p['nota_arte'])}</span></article>
<aside class="sidebar"><div class="side-heading"><span>{e(p['lateral'][0])}</span><span>{e(p['lateral'][1])}</span></div>{temas}</aside></section>
<div class="social-ribbon"><span>{e(p['redes_titulo'])}</span>{redes}</div>
<section id="opiniones" class="content-section"><div class="section-title"><div>
<span class="eyebrow red">{e(sec['opiniones']['eyebrow'])}</span><h2>{e(sec['opiniones']['titulo'])}<span class="red">.</span></h2></div>
<a class="text-link" href="/reviews/">Todas las reviews ↗</a></div>
{tarjeta_grande(revs[0])}<div class="archive-grid home-recent">{resto}</div></section>
<section id="videos" class="content-section"><div class="section-title"><div>
<span class="eyebrow red">{e(sec['videos']['eyebrow'])}</span><h2>{e(sec['videos']['titulo'])}<span class="red">.</span></h2></div>
<a class="text-link" href="{r['youtube']}" target="_blank" rel="noopener noreferrer">Ir al canal <span aria-hidden="true">↗</span></a></div>
{playlist(sec['videos'])}</section>
<section id="desarrollo" class="dev-section"><div class="dev-intro"><span class="eyebrow red">{e(sec['desarrollo']['eyebrow'])}</span>
<h2>{crudo(e(sec['desarrollo']['titulo']).replace('&lt;em&gt;','<em>').replace('&lt;/em&gt;','</em>'))}</h2>
<p>{e(sec['desarrollo']['texto'])}</p></div>{playlist(sec['desarrollo'])}</section>
<section id="sobre-mi" class="content-section"><div class="section-title"><div>
<span class="eyebrow red">{e(sm['eyebrow'])}</span><h2>{nl(sm['titulo'])}</h2></div></div>
{"".join(f'<p>{e(x)}</p>' for x in sm['parrafos'])}
<p><a class="text-link" href="mailto:{S['email']}">Hablamos: {S['email']} ↗</a></p></section>
</main>{PIE}<script src="/playlists.js" defer></script></body></html>"""

def feed():
    it = "".join(f"""<item><title>{e(r['juego'])} — {e(r['subtitulo'])}</title><link>{r['url']}</link>
<guid isPermaLink="true">{r['url']}</guid><pubDate>{datetime.strptime(r['fecha'],'%Y-%m-%d').strftime('%a, %d %b %Y 09:00:00 +0100')}</pubDate>
<description>{e(r.get('resumen',''))} Nota: {r['final']}/100.</description></item>""" for r in revs)
    return f"""<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
<title>Reviews de Maniaco360</title><link>{BASE}/reviews/</link><language>es-ES</language>
<description>{e(S['descripcion'])}</description>{it}</channel></rss>"""

# ---------- escribir ----------
def escribir(ruta, texto):
    p = OUT / ruta
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto, "utf-8")

if OUT.exists():
    try:
        shutil.rmtree(OUT)          # limpieza; si el sistema no permite borrar, se escribe encima
    except OSError:
        pass
def preparar_estaticos():
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    shutil.copy(R / "plantilla/estilo.css", OUT / "style.css")
    shutil.copy(R / "plantilla/playlists.js", OUT / "playlists.js")
    try:
        from PIL import Image
    except ImportError:
        Image = None
        print("Aviso: Pillow no esta instalado; se publican las imagenes a tamano completo.")
    for img in sorted((R / "imagenes").glob("*.webp")):
        shutil.copy(img, OUT / "images" / img.name)
        if Image is None:
            continue
        im = Image.open(img)
        if im.width > 800:
            im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS).save(
                OUT / "images" / img.name.replace(".webp", "-800.webp"), quality=82, method=6)
            PEQUENAS.add(img.name)

preparar_estaticos()
escribir("index.html", pagina_inicio())
escribir("reviews/index.html", pagina_indice())
for r in revs:
    escribir(f"reviews/{r['slug']}/index.html", pagina_review(r))
escribir("feed.xml", feed())
escribir("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
escribir("CNAME", BASE.split("//")[-1] + "\n")   # dominio propio para GitHub Pages
escribir(".nojekyll", "")                        # publicar los archivos tal cual, sin Jekyll
hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
urls = [(BASE + "/", hoy, "1.0"), (f"{BASE}/reviews/", hoy, "0.9")] + [(r["url"], r["fecha"], "0.8") for r in revs]
escribir("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
         + "".join(f"<url><loc>{u}</loc><lastmod>{m}</lastmod><priority>{p}</priority></url>" for u, m, p in urls)
         + "</urlset>")
print(f"Generado en {OUT}: {len(revs)} reviews, {sum(1 for _ in OUT.rglob('*') if _.is_file())} archivos")
