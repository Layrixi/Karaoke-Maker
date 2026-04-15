//  KEYBOARD SHORTCUTS 
document.addEventListener('keydown', e => {
  // Space = play/pause
  if (e.code === 'Space' && document.activeElement !== lyricsRaw) {
    e.preventDefault();
    if (video.paused) { video.play(); playBtn.textContent = '⏸'; }
    else { video.pause(); playBtn.textContent = '▶'; }
  }
  // M = mark current time for active line
  if (e.code === 'KeyM' && state.activeLineIdx !== null && state.videoDuration) {
    assignTimestamp(state.activeLineIdx, video.currentTime);
  }
  // Arrow keys: step through lines
  if (e.code === 'ArrowDown' && document.activeElement !== lyricsRaw) {
    e.preventDefault();
    const next = state.activeLineIdx === null ? 0 : Math.min(state.lines.length - 1, state.activeLineIdx + 1);
    selectLine(next);
  }
  if (e.code === 'ArrowUp' && document.activeElement !== lyricsRaw) {
    e.preventDefault();
    const prev = state.activeLineIdx === null ? 0 : Math.max(0, state.activeLineIdx - 1);
    selectLine(prev);
  }
  // Left/Right: nudge video
  if (e.code === 'ArrowLeft' && document.activeElement !== lyricsRaw) {
    e.preventDefault();
    seekTo(video.currentTime - (e.shiftKey ? 5 : 1));
  }
  if (e.code === 'ArrowRight' && document.activeElement !== lyricsRaw) {
    e.preventDefault();
    seekTo(video.currentTime + (e.shiftKey ? 5 : 1));
  }
});

//  INIT 
updateInstructions();

//  QoL
// Clicking outside the active workflow areas clears the active line selection
// and closes the style editor panel.
const FOCUS_SAFE_SELECTORS = [
  '.lyrics-panel',
  '.timeline-section',
  '#stylePanel',
  '.header',
];

document.addEventListener('mousedown', e => {
  const inSafeZone = FOCUS_SAFE_SELECTORS.some(sel => e.target.closest(sel));
  if (inSafeZone) return;

  let changed = false;
  if (state.activeLineIdx !== null) {
    state.activeLineIdx = null;
    renderLyricsList();
    updateInstructions();
    changed = true;
  }

  const panel = document.getElementById('stylePanel');
  if (panel && panel.classList.contains('open')) {
    closeStyleEditor();
  }
});

