//  UTILS 

function formatTime(s) {
  if (!s || isNaN(s)) return '0:00';
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60).toString().padStart(2, '0');
  return `${m}:${sec}`;
}

function formatTimeFull(s) {
  if (!s || isNaN(s)) return '0:00.0';
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(1).padStart(4, '0');
  return `${m}:${sec}`;
}

function escHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function showPopUp(msg, duration = 2200) {
  const t = document.getElementById('pop_up');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}

function showFieldTip(msg, anchorEl) {
  const tip = document.getElementById('field_tip');
  tip.textContent = msg.replace(/\\n/g, '\n');
  tip.classList.add('show');
  const rect = anchorEl.getBoundingClientRect();
  tip.style.top  = (rect.bottom + 6) + 'px';
  tip.style.left = rect.left + 'px';
}

function hideFieldTip() {
  document.getElementById('field_tip').classList.remove('show');
}

function download(filename, content) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([content], { type: 'text/plain' }));
  a.download = filename;
  a.click();
}

// Mirrors TextBurner._wrap_text.
// play_res_x/videoH use live rendered dimensions of the video element so line
// breaks match what is visually shown in the overlay. font_size is scaled from
// ASS units to screen pixels before computing charsPerLine, matching the same
// coordinate space as the overlay. Reads state.wrapConfig (from /api/wrap-config).
// fontSize: optional per-line font_size in ASS units; defaults to state.wrapConfig.font_size.
function wrapText(text, fontSize) {
  const { font_size: defaultFontSize, char_width_ratio, play_res_x, play_res_y } = state.wrapConfig;
  const assFont      = fontSize ?? defaultFontSize;
  // compute entirely in ASS coordinate space to match Python exactly
  const charsPerLine = Math.max(1, Math.floor((play_res_x) / (assFont * char_width_ratio))) || 48;

  // split words into smaller ones in case they are very long
  const words = [];
  for (const word of text.split(' ')) {
    let w = word;
    while (w.length > charsPerLine) {
      words.push(w.slice(0, charsPerLine));
      w = w.slice(charsPerLine);
    }
    if (w) words.push(w);
  }

  // build lines 1-by-1, until the line exceeds the character limit
  const lines = [];
  let current = '';
  for (const word of words) {
    if (!current) {
      //line is empty
      current = word;
    } else if (current.length + 1 + word.length <= charsPerLine) {
      current += ' ' + word;
    } else {
      lines.push(current);
      current = word;
    }
  }
  if (current) lines.push(current);
  return lines;
}
