// --  CONFIG --

// Calls backend text wrapping method and returns an array of wrapped lines, or null on failure.
async function wrapTextLine(text, style) {
  try {
    const res = await fetch('/api/wrap-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, style }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.lines ?? null;
  } catch (_) {
    return null;
  }
}


// -- VOCAL REMOVAL API --

async function uploadVideo(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('/api/upload-video', { method: 'POST', body: formData });
  if (!res.ok) throw new Error('Upload failed');
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data.filename;
}

async function removeVocals(btn) {
  if (!state.uploadedVideoFilename) {
    showPopUp('Load a video first');
    return;
  }
  const originalLabel = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Processing...';
  document.getElementById('vocalProcessingHint').style.display = 'block';
  try {
    const res = await fetch('/api/remove-vocals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: state.uploadedVideoFilename })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Processing failed');
    state.vocalsRemovedFor = state.uploadedVideoFilename;
    state.instrumentalAudioUrl = data.audio_download_url;
    showPopUp('Vocals removed — ready to render');
    updateVocalRemovalButtons();
    document.getElementById('instrumentalDownloadPopup').classList.add('show');
  } catch (e) {
    showPopUp('Error: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = originalLabel;
    document.getElementById('vocalProcessingHint').style.display = 'none';
  }
}

// Shows the single "Download Instrumental" button in place of the two removal
// buttons once vocals have been removed for the currently loaded video.
function updateVocalRemovalButtons() {
  const removed = state.uploadedVideoFilename !== null && state.vocalsRemovedFor === state.uploadedVideoFilename;
  document.getElementById('removeVocalsBtn').style.display = removed ? 'none' : '';
  document.getElementById('removeVocalsCpuBtn').style.display = removed ? 'none' : '';
  document.getElementById('downloadInstrumentalBtn').style.display = removed ? '' : 'none';
}

document.getElementById('downloadInstrumentalBtn').addEventListener('click', () => {
  document.getElementById('instrumentalDownloadPopup').classList.add('show');
});

document.getElementById('idpDownloadBtn').addEventListener('click', () => {
  document.getElementById('instrumentalDownloadPopup').classList.remove('show');
  if (!state.instrumentalAudioUrl) return;
  const a = document.createElement('a');
  a.href = state.instrumentalAudioUrl;
  a.download = '';
  a.click();
});

document.getElementById('idpNoThanksBtn').addEventListener('click', () => {
  document.getElementById('instrumentalDownloadPopup').classList.remove('show');
});

// "Remove using GPU" / "Remove with CPU" both call the same endpoint for now —
// the device split is visual only until the backend supports per-request device selection.
document.getElementById('removeVocalsBtn').addEventListener('click', () => removeVocals(document.getElementById('removeVocalsBtn')));
document.getElementById('removeVocalsCpuBtn').addEventListener('click', () => removeVocals(document.getElementById('removeVocalsCpuBtn')));

// -- VIDEO RENDER API --

function showRenderChoicePopup() {
  document.getElementById('renderChoicePopup').classList.add('show');
}

function hideRenderChoicePopup() {
  document.getElementById('renderChoicePopup').classList.remove('show');
}

async function performRender(useInstrumental) {
  const synced = state.lines.filter(l => l.timestamp !== null);
  const btn = document.getElementById('renderVideoBtn');
  btn.disabled = true;
  btn.textContent = 'Rendering…';
  try {
    const res = await fetch('/api/render-video', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: state.uploadedVideoFilename, lines: synced, use_instrumental: useInstrumental }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Render failed');
    const a = document.createElement('a');
    a.href = data.download_url;
    a.download = '';
    a.click();
    showPopUp('Rendered video ready!');
  } catch (e) {
    showPopUp('Error: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Render Video';
  }
}

document.getElementById('renderVideoBtn').addEventListener('click', () => {
  if (!state.uploadedVideoFilename) {
    showPopUp('Load a video first');
    return;
  }
  const synced = state.lines.filter(l => l.timestamp !== null);
  if (synced.length === 0) {
    showPopUp('Sync at least one line first');
    return;
  }
  showRenderChoicePopup();
});

document.getElementById('rcpInstrumentalBtn').addEventListener('click', () => {
  hideRenderChoicePopup();
  if (state.vocalsRemovedFor !== state.uploadedVideoFilename) {
    showPopUp("Remove vocals first — this video hasn't had vocals removed yet");
    return;
  }
  performRender(true);
});

document.getElementById('rcpOriginalBtn').addEventListener('click', () => {
  hideRenderChoicePopup();
  performRender(false);
});

document.getElementById('rcpCancelBtn').addEventListener('click', hideRenderChoicePopup);

// --  FONT API CALL --

async function fetchFontList() {
  try {
    const res = await fetch('/api/fonts');
    if (!res.ok) return;
    const data = await res.json();
    state.availableFonts = data.fonts;
    if (data.fonts.length > 0) {
      DEFAULT_STYLE.font_file = data.fonts[0];
    }
    const fonts = Array.isArray(data.fonts) ? data.fonts : [];
    state.availableFonts = fonts;
    DEFAULT_STYLE.font_file = fonts[0] ?? '';
    const select = document.getElementById('se_font_file');
    select.innerHTML = '';  // clear existing options
    fonts.forEach(filename => {
      const option = document.createElement('option');
      option.value = filename;
      const stem = filename.split('/').pop().replace(/\.[^.]+$/, '');
      option.textContent = stem;  // display filename stem only, without folder prefix or extension
      select.appendChild(option);
    });
  } catch (e) {
    console.warn('Could not load font list:', e);
  }
}
