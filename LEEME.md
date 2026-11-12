# Web de Maniaco360

Sitio estático. El contenido vive en `contenido/` y `construir.py` genera el HTML en `salida/`.
No hay CMS, ni base de datos, ni dependencias obligatorias: solo Python. Pillow es opcional y
únicamente sirve para crear las versiones reducidas de las imágenes.

## Añadir una review

1. Copia la imagen a `imagenes/<slug>.webp` (1600 × 900).
2. Crea `contenido/reviews/<slug>.md` con esta cabecera:

```
---
juego: "Nombre del juego"
subtitulo: "la frase que acompaña al título"
slug: nombre-del-juego
fecha: 2026-11-08
imagen: nombre-del-juego.webp
imagen_alt: "Descripción de la imagen para quien no puede verla"
descripcion: "Texto que aparece en Google y al compartir el enlace. Mi nota: 81/100."
resumen: "Una o dos frases de resumen."
video: "https://www.youtube.com/watch?v=XXXXXXXXXXX"
notas:
  Gameplay: 85
  Diseño y progresión: 90
  Narrativa y mundo: 75
  Apartado audiovisual: 75
lo_mejor:
  - "Primer punto."
  - "Segundo punto."
lo_falta:
  - "Primer punto."
  - "Segundo punto."
final: 81
---

## Primer apartado

El texto de la review, en Markdown.
```

3. Guarda y sube el cambio. La web se reconstruye sola.

`video` puede quedar vacío (`""`) hasta que el vídeo esté publicado. Cuando lo rellenes, la review
muestra el reproductor y el enlace al vídeo.

Lo demás se genera solo: portada, índice de reviews, enlaces entre reviews, `sitemap.xml`,
`robots.txt`, `feed.xml`, las etiquetas para compartir en redes y los datos estructurados que
permiten que Google muestre la nota en los resultados de búsqueda.

## Ver el resultado antes de publicar

```
python construir.py
```

Genera `salida/`. Para verlo en el navegador:

```
python -m http.server -d salida 8000
```

y abre `http://localhost:8000`.

## Textos de la portada

Están en `contenido/sitio.json`: titulares, secciones, redes y las listas de YouTube.
`base` define el dominio y se usa en los enlaces canónicos, el sitemap y las etiquetas sociales.

## Publicación

Cualquiera de las dos opciones vale; con Cloudflare Pages el dominio ya está en el sitio correcto.

- **Cloudflare Pages:** conectar el repositorio, comando de construcción `python3 construir.py`,
  carpeta de salida `salida`.
- **GitHub Pages:** ya está el flujo `.github/workflows/publicar.yml`; basta con activar Pages
  en los ajustes del repositorio, con origen «GitHub Actions».

Importante: el dominio debe responder **con y sin `www`**. Hoy `maniaco360.com` a secas no carga,
y los enlaces de los vídeos ya publicados en YouTube apuntan ahí.
