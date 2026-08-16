/* ==========================================================================
   DocCraft Document Studio — Application Logic
   All Flask API calls preserved exactly. UI helpers updated for editorial design.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initDragAndDrop();
  loadHistory();
  initKeyboardNav();
});

/* --------------------------------------------------------------------------
   Theme Management
   -------------------------------------------------------------------------- */
function initTheme() {
  const saved = localStorage.getItem('doccraft_theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
  } else {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('doccraft_theme', next);
  showToast(`Switched to ${next} mode`);
}

/* --------------------------------------------------------------------------
   Mobile Menu
   -------------------------------------------------------------------------- */
function toggleMobileMenu() {
  const links = document.getElementById('nav-links');
  if (links) links.classList.toggle('open');
}

/* --------------------------------------------------------------------------
   Tool Switching — opens workspace panel, no smooth scroll library
   -------------------------------------------------------------------------- */
function openTool(toolId) {
  // Hide all workspace panels
  document.querySelectorAll('.workspace-panel').forEach(el => el.classList.remove('active'));

  const target = document.getElementById(`workspace-${toolId}`);
  if (target) {
    target.classList.add('active');
    // Native instant scroll only — no smooth-scroll library, preserves 60fps
    target.scrollIntoView({ behavior: 'auto', block: 'start' });
  }
}

function closeWorkspace() {
  document.querySelectorAll('.workspace-panel').forEach(el => el.classList.remove('active'));
  // Scroll back to tool index
  const toolIndex = document.getElementById('tools-section');
  if (toolIndex) toolIndex.scrollIntoView({ behavior: 'auto', block: 'start' });
}

function handleComingSoon(toolName) {
  showToast(`${toolName} is coming soon — check back in the next update.`, 'error');
}

/* --------------------------------------------------------------------------
   Keyboard accessibility for tool rows
   -------------------------------------------------------------------------- */
function initKeyboardNav() {
  document.querySelectorAll('.tool-row').forEach(row => {
    row.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        row.click();
      }
    });
  });
}

/* --------------------------------------------------------------------------
   Drag and Drop Upload Handlers
   -------------------------------------------------------------------------- */
const selectedFiles = {
  merge: [],
  split: [],
  rotate: [],
  img2pdf: [],
  pdf2img: [],
  watermark: []
};

function initDragAndDrop() {
  document.querySelectorAll('.dropzone').forEach(zone => {
    const type = zone.dataset.tool;

    ['dragenter', 'dragover'].forEach(evt => {
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add('dragover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(evt => {
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('dragover');
      }, false);
    });

    zone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleFileAddition(type, Array.from(files));
      }
    });
  });
}

function triggerFileInput(type) {
  const input = document.getElementById(`input-${type}`);
  if (input) input.click();
}

function handleFileInputChange(type) {
  const input = document.getElementById(`input-${type}`);
  if (input && input.files) {
    handleFileAddition(type, Array.from(input.files));
  }
}

function handleFileAddition(type, files) {
  if (type === 'split' || type === 'rotate' || type === 'pdf2img' || type === 'watermark') {
    selectedFiles[type] = [files[0]];
  } else {
    selectedFiles[type] = [...selectedFiles[type], ...files];
  }
  renderFilePreviews(type);
}

function removeFile(type, index) {
  selectedFiles[type].splice(index, 1);
  renderFilePreviews(type);
}

function renderFilePreviews(type) {
  const container = document.getElementById(`preview-${type}`);
  if (!container) return;

  container.innerHTML = '';
  const files = selectedFiles[type];

  if (files.length === 0) return;

  files.forEach((file, idx) => {
    const isImage = file.type.startsWith('image/');
    const card = document.createElement('div');
    card.className = 'file-preview-card';

    const thumbHtml = isImage
      ? `<img src="${URL.createObjectURL(file)}" class="file-thumb" alt="Preview">`
      : `<svg class="file-icon-svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"/></svg>`;

    card.innerHTML = `
      <div class="file-info-col">
        ${thumbHtml}
        <div class="file-details">
          <span class="file-name">${file.name}</span>
          <span class="file-meta">${formatBytes(file.size)}</span>
        </div>
      </div>
      <button class="btn-remove" onclick="removeFile('${type}', ${idx})" aria-label="Remove file">×</button>
    `;
    container.appendChild(card);
  });
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/* --------------------------------------------------------------------------
   API Operations — ALL preserved exactly from original
   -------------------------------------------------------------------------- */
async function submitMerge() {
  const files = selectedFiles.merge;
  if (!files || files.length < 2) {
    showToast('Please select at least 2 PDF files to merge.', 'error');
    return;
  }

  const formData = new FormData();
  files.forEach(f => formData.append('files', f));

  const btn = document.getElementById('btn-submit-merge');
  setBtnLoading(btn, true, 'Merging…');

  try {
    const res = await fetch('/api/merge', { method: 'POST', body: formData });
    const data = await res.json();
    setBtnLoading(btn, false, 'Merge PDFs');

    if (data.success) {
      showToast('PDFs merged successfully!');
      const resultBox = document.getElementById('result-merge');
      const dlLink = document.getElementById('dl-merge');
      dlLink.href = data.download_url;
      resultBox.classList.add('show');
      loadHistory();
    } else {
      showToast(data.error || 'Failed to merge PDFs', 'error');
    }
  } catch (err) {
    setBtnLoading(btn, false, 'Merge PDFs');
    showToast('Server connection error. Please try again.', 'error');
  }
}

async function submitSplit() {
  const files = selectedFiles.split;
  if (!files || files.length === 0) {
    showToast('Please select a PDF file to split.', 'error');
    return;
  }

  const mode = document.getElementById('split-mode').value;
  const rangeStr = document.getElementById('split-range').value;
  const chunkSize = document.getElementById('split-chunk').value;

  const formData = new FormData();
  formData.append('file', files[0]);
  formData.append('mode', mode);
  formData.append('range_str', rangeStr);
  formData.append('chunk_size', chunkSize);

  const btn = document.getElementById('btn-submit-split');
  setBtnLoading(btn, true, 'Splitting…');

  try {
    const res = await fetch('/api/split', { method: 'POST', body: formData });
    const data = await res.json();
    setBtnLoading(btn, false, 'Split PDF');

    if (data.success) {
      showToast('PDF split successfully!');
      const resultBox = document.getElementById('result-split');
      const container = document.getElementById('split-dl-list');
      container.innerHTML = '';
      data.files.forEach(f => {
        container.innerHTML += `<div><a class="btn-download" href="${f.url}" download>Download ${f.filename}</a></div>`;
      });
      resultBox.classList.add('show');
      loadHistory();
    } else {
      showToast(data.error || 'Failed to split PDF', 'error');
    }
  } catch (err) {
    setBtnLoading(btn, false, 'Split PDF');
    showToast('Server connection error. Please try again.', 'error');
  }
}

async function submitRotate() {
  const files = selectedFiles.rotate;
  if (!files || files.length === 0) {
    showToast('Please select a PDF file to rotate.', 'error');
    return;
  }

  const angle = document.getElementById('rotate-angle').value;

  const formData = new FormData();
  formData.append('file', files[0]);
  formData.append('angle', angle);

  const btn = document.getElementById('btn-submit-rotate');
  setBtnLoading(btn, true, 'Rotating…');

  try {
    const res = await fetch('/api/rotate', { method: 'POST', body: formData });
    const data = await res.json();
    setBtnLoading(btn, false, 'Rotate Pages');

    if (data.success) {
      showToast('PDF rotated successfully!');
      const resultBox = document.getElementById('result-rotate');
      const dlLink = document.getElementById('dl-rotate');
      dlLink.href = data.download_url;
      resultBox.classList.add('show');
      loadHistory();
    } else {
      showToast(data.error || 'Failed to rotate PDF', 'error');
    }
  } catch (err) {
    setBtnLoading(btn, false, 'Rotate Pages');
    showToast('Server connection error. Please try again.', 'error');
  }
}

async function submitImg2Pdf() {
  const files = selectedFiles.img2pdf;
  if (!files || files.length === 0) {
    showToast('Please select at least 1 image file.', 'error');
    return;
  }

  const formData = new FormData();
  files.forEach(f => formData.append('files', f));

  const btn = document.getElementById('btn-submit-img2pdf');
  setBtnLoading(btn, true, 'Converting…');

  try {
    const res = await fetch('/api/image-to-pdf', { method: 'POST', body: formData });
    const data = await res.json();
    setBtnLoading(btn, false, 'Convert to PDF');

    if (data.success) {
      showToast('Images converted to PDF successfully!');
      const resultBox = document.getElementById('result-img2pdf');
      const dlLink = document.getElementById('dl-img2pdf');
      dlLink.href = data.download_url;
      resultBox.classList.add('show');
      loadHistory();
    } else {
      showToast(data.error || 'Failed to convert images', 'error');
    }
  } catch (err) {
    setBtnLoading(btn, false, 'Convert to PDF');
    showToast('Server connection error. Please try again.', 'error');
  }
}

async function submitPdf2Img() {
  const files = selectedFiles.pdf2img;
  if (!files || files.length === 0) {
    showToast('Please select a PDF file.', 'error');
    return;
  }

  const fmt = document.getElementById('pdf2img-format').value;
  const dpi = document.getElementById('pdf2img-dpi').value;

  const formData = new FormData();
  formData.append('file', files[0]);
  formData.append('format', fmt);
  formData.append('dpi', dpi);

  const btn = document.getElementById('btn-submit-pdf2img');
  setBtnLoading(btn, true, 'Exporting…');

  try {
    const res = await fetch('/api/pdf-to-image', { method: 'POST', body: formData });
    const data = await res.json();
    setBtnLoading(btn, false, 'Export Images');

    if (data.success) {
      showToast('PDF exported to images successfully!');
      const resultBox = document.getElementById('result-pdf2img');
      const container = document.getElementById('pdf2img-dl-list');
      container.innerHTML = '';
      data.files.forEach(f => {
        container.innerHTML += `<div><a class="btn-download" href="${f.url}" download>Download ${f.filename}</a></div>`;
      });
      resultBox.classList.add('show');
      loadHistory();
    } else {
      showToast(data.error || 'Failed to export images', 'error');
    }
  } catch (err) {
    setBtnLoading(btn, false, 'Export Images');
    showToast('Server connection error. Please try again.', 'error');
  }
}

async function submitWatermark() {
  const files = selectedFiles.watermark;
  if (!files || files.length === 0) {
    showToast('Please select a PDF file.', 'error');
    return;
  }

  const text = document.getElementById('wm-text').value;
  const opacity = document.getElementById('wm-opacity').value;

  const formData = new FormData();
  formData.append('file', files[0]);
  formData.append('type', 'text');
  formData.append('text', text);
  formData.append('opacity', opacity);

  const btn = document.getElementById('btn-submit-watermark');
  setBtnLoading(btn, true, 'Applying…');

  try {
    const res = await fetch('/api/watermark', { method: 'POST', body: formData });
    const data = await res.json();
    setBtnLoading(btn, false, 'Apply Watermark');

    if (data.success) {
      showToast('Watermark applied successfully!');
      const resultBox = document.getElementById('result-watermark');
      const dlLink = document.getElementById('dl-watermark');
      dlLink.href = data.download_url;
      resultBox.classList.add('show');
      loadHistory();
    } else {
      showToast(data.error || 'Failed to apply watermark', 'error');
    }
  } catch (err) {
    setBtnLoading(btn, false, 'Apply Watermark');
    showToast('Server connection error. Please try again.', 'error');
  }
}

function toggleSplitOptions() {
  const mode = document.getElementById('split-mode').value;
  document.getElementById('split-range-box').style.display = (mode === 'range') ? 'flex' : 'none';
  document.getElementById('split-chunk-box').style.display = (mode === 'chunk') ? 'flex' : 'none';
}

function setBtnLoading(btn, isLoading, text) {
  if (!btn) return;
  btn.disabled = isLoading;
  btn.textContent = text;
}

/* --------------------------------------------------------------------------
   Recent History — timeline style
   -------------------------------------------------------------------------- */
async function loadHistory() {
  try {
    const res = await fetch('/api/history');
    const data = await res.json();
    const container = document.getElementById('history-container');
    if (!container) return;

    if (!data || data.length === 0) {
      container.innerHTML = '<p class="timeline-empty">No recent operations yet. Process a PDF to see your activity here.</p>';
      return;
    }

    container.innerHTML = '';
    data.slice(0, 8).forEach(item => {
      const el = document.createElement('div');
      el.className = 'timeline-item';
      el.innerHTML = `
        <div class="timeline-left">
          <span class="timeline-badge">${item.operation}</span>
          <span class="timeline-filename">${item.filename}</span>
        </div>
        <span class="timeline-time">${item.timestamp}</span>
      `;
      container.appendChild(el);
    });
  } catch (err) {
    console.error('Failed to load history:', err);
  }
}

/* --------------------------------------------------------------------------
   Toast Notifications — editorial thin-border style
   -------------------------------------------------------------------------- */
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✓' : '⚠';
  toast.innerHTML = `<span class="toast-icon">${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  // Auto-dismiss after 3.5s
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    setTimeout(() => toast.remove(), 200);
  }, 3500);
}
