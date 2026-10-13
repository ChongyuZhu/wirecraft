// Optional progressive enhancement: the published page is static HTML.
const tabs = [...document.querySelectorAll('[role="tab"]')];
function selectTask(tab) {
  tabs.forEach(item => {
    const active = item === tab;
    item.setAttribute('aria-selected', String(active));
    item.tabIndex = active ? 0 : -1;
    const panel = document.getElementById(item.getAttribute('aria-controls'));
    panel.hidden = !active;
    if (!active) panel.querySelectorAll('video').forEach(video => video.pause());
  });
}
tabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectTask(tab));
  tab.addEventListener('keydown', event => {
    let next;
    if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
    if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = tabs.length - 1;
    if (next !== undefined) {
      event.preventDefault();
      selectTask(tabs[next]);
      tabs[next].focus();
    }
  });
});
// Keep hidden recordings quiet and avoid multiple clips playing together.
document.querySelectorAll('video').forEach(video => {
  video.addEventListener('play', () => {
    document.querySelectorAll('video').forEach(other => {
      if (other !== video) other.pause();
    });
  });
});
document.querySelectorAll('details').forEach(details => {
  details.addEventListener('toggle', () => {
    if (!details.open) details.querySelectorAll('video').forEach(video => video.pause());
  });
});
const copyButton = document.getElementById('copy-citation');
copyButton.addEventListener('click', async () => {
  const code = document.getElementById('bibtex');
  const status = document.getElementById('copy-status');
  try {
    if (!navigator.clipboard) throw new Error('Clipboard unavailable');
    await navigator.clipboard.writeText(code.textContent);
    copyButton.textContent = 'Copied!';
    status.textContent = 'Citation copied to clipboard.';
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(code);
    selection.removeAllRanges();
    selection.addRange(range);
    copyButton.textContent = 'Text selected';
    status.textContent = 'Use your browser’s Copy command to copy the selected citation.';
  }
});
