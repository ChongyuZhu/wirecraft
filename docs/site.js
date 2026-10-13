// Optional progressive enhancement: the published page is static HTML.
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
