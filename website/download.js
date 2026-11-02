// The PS5 anchor remains a direct-download fallback if scripting is unavailable.
const platformDialog = document.querySelector('.download-dialog');
if (platformDialog && typeof platformDialog.showModal === 'function') {
  let downloadOrigin;
  document.querySelectorAll('.download-button').forEach(trigger => {
    trigger.setAttribute('aria-haspopup', 'dialog');
    trigger.setAttribute('aria-controls', 'download-platform-dialog');
    trigger.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); downloadOrigin = trigger;
      platformDialog.showModal();
    });
  });
  platformDialog.querySelector('.download-close').addEventListener('click', () => platformDialog.close());
  platformDialog.addEventListener('click', event => {
    if (event.target !== platformDialog) return;
    const bounds = platformDialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) platformDialog.close();
  });
  platformDialog.addEventListener('close', () => downloadOrigin?.focus());
  fetch('windows-release.json', { cache: 'no-cache' }).then(response => response.ok ? response.json() : null).then(release => {
    if (!release?.available || typeof release.setup_url !== 'string') return;
    const url = new URL(release.setup_url);
    if (url.protocol !== 'https:' || url.hostname !== 'github.com' || !url.pathname.startsWith('/LoZazaMastro/Pixel-Museum/releases/')) return;
    const windows = platformDialog.querySelector('.platform-windows');
    windows.href = url.href; windows.removeAttribute('aria-disabled'); windows.removeAttribute('tabindex');
    windows.querySelector('.platform-detail').textContent = 'Download setup';
  }).catch(() => {});
}
