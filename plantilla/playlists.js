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
