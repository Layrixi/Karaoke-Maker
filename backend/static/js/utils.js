//  UTILS 

function _getWrapValues(style) {
  return {
    font_file:      style.font_file,
    font_size:      style.font_size,
    bold:           style.bold,
    italic:         style.italic,
    letter_spacing: style.letter_spacing,
    angle:          style.angle,
  };
}

function _isRewrapNeeded(style1, style2) {
  return  style1.font_file      !== style2.font_file      ||
          style1.font_size      !== style2.font_size      ||
          style1.bold           !== style2.bold           ||
          style1.italic         !== style2.italic         ||
          style1.letter_spacing !== style2.letter_spacing ||
          style1.angle          !== style2.angle;
}

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

