document.querySelectorAll('.playlist-embed').forEach((panel) => {
  panel.addEventListener('toggle', () => {
    if (!panel.open || panel.querySelector('iframe')) return;
    const frame = document.createElement('iframe');
    const url = new URL('https://www.youtube-nocookie.com/embed');
    url.searchParams.set('listType', 'playlist');
    url.searchParams.set('list', panel.dataset.playlist);
    url.searchParams.set('playsinline', '1');
    frame.src = url.href;
    frame.title = panel.dataset.title;
    frame.allow = 'encrypted-media; picture-in-picture; fullscreen';
    frame.allowFullscreen = true;
    frame.referrerPolicy = 'strict-origin-when-cross-origin';
    panel.querySelector('.playlist-player').append(frame);
  });
});

function videoCard(video) {
  const article = document.createElement('article');
  article.className = 'video-card';
  const link = document.createElement('a');
  link.href = video.url;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  const image = document.createElement('img');
  image.src = video.thumbnail;
  image.alt = '';
  image.width = 480;
  image.height = 360;
  image.loading = 'lazy';
  const copy = document.createElement('div');
  copy.className = 'video-copy';
  const time = document.createElement('time');
  time.dateTime = video.publishedAt;
  time.textContent = new Intl.DateTimeFormat('es-ES', {day:'numeric',month:'short',year:'numeric'}).format(new Date(video.publishedAt));
  const title = document.createElement('h4');
  title.textContent = video.title;
  const action = document.createElement('span');
  action.className = 'text-link';
  action.textContent = 'Ver en YouTube ↗';
  copy.append(time,title,action);
  link.append(image,copy);
  article.append(link);
  return article;
}
document.querySelectorAll('[data-video-feed]').forEach(async feed => {
  try {
    const response = await fetch('/api/youtube?list=' + encodeURIComponent(feed.dataset.videoFeed), {signal:AbortSignal.timeout(25000)});
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    if (data.state === 'unavailable') throw new Error('unavailable');
    feed.replaceChildren();
    if (data.state === 'ready' && data.videos.length) {
      feed.append(...data.videos.map(videoCard));
    } else {
      const message = document.createElement('p');
      message.className = 'video-status';
      message.textContent = 'Todavía no hay vídeos publicados en esta lista. El primero aparecerá aquí cuando esté disponible.';
      feed.append(message);
    }
  } catch {
    feed.replaceChildren();
    const message = document.createElement('p');
    message.className = 'video-status';
    message.textContent = 'Ahora mismo no se pueden cargar los vídeos. Puedes abrir la lista en YouTube.';
    feed.append(message);
  }
});
