/**
 * DOCCRAFT — MAXIMUM-WIDTH DOCUMENT ENGINEERING WORKSTATION CLIENT ENGINE
 * Concept: 1800px Full-Screen Proportions · Custom Geometric Brand Mark · 12 Local PyMuPDF Operations
 * Performance: Native 60-144 FPS Hardware Acceleration · Zero Continuous Scroll Listeners
 */

const CanvasStudio = {
  activeTool: 'merge',
  stagedFiles: [],
  isProcessing: false,
  toolMeta: {
    'merge': {
      title: 'Merge PDF',
      desc: 'Combine multiple PDF documents into a unified file.',
      canvasTitle: 'DOCCRAFT / MERGE_WORKSPACE',
      stateId: 'state-merge',
      accept: '.pdf',
      multiple: true
    },
    'split': {
      title: 'Split PDF',
      desc: 'Partition or extract specific page ranges.',
      canvasTitle: 'DOCCRAFT / SPLIT_PARTITION',
      stateId: 'state-split',
      accept: '.pdf',
      multiple: false
    },
    'rotate': {
      title: 'Rotate Pages',
      desc: 'Reorient document pages by 90°, 180°, or 270°.',
      canvasTitle: 'DOCCRAFT / ROTATE_ORIENTATION',
      stateId: 'state-rotate',
      accept: '.pdf',
      multiple: false
    },
    'img2pdf': {
      title: 'Images → PDF',
      desc: 'Assemble PNG, JPG, BMP image sheets into a single PDF.',
      canvasTitle: 'DOCCRAFT / IMAGE_ASSEMBLY',
      stateId: 'state-images',
      accept: 'image/png, image/jpeg, image/jpg, image/bmp',
      multiple: true
    },
    'pdf2img': {
      title: 'PDF → Images',
      desc: 'Render PDF pages into lossless PNG or compact JPEG images.',
      canvasTitle: 'DOCCRAFT / RASTER_EXTRACTION',
      stateId: 'state-images',
      accept: '.pdf',
      multiple: false
    },
    'watermark': {
      title: 'Add Watermark',
      desc: 'Stamp custom text or confidential overlays onto pages.',
      canvasTitle: 'DOCCRAFT / WATERMARK_STAMP',
      stateId: 'state-watermark',
      accept: '.pdf',
      multiple: false
    },
    'compress': {
      title: 'Compress PDF',
      desc: 'Deflate stream dictionaries and optimize file payload.',
      canvasTitle: 'DOCCRAFT / STREAM_COMPRESS',
      stateId: 'state-compress',
      accept: '.pdf',
      multiple: false
    },
    'add-password': {
      title: 'Add Password',
      desc: 'Encrypt document with standard AES-256 cryptography.',
      canvasTitle: 'DOCCRAFT / ENCRYPTION_SEAL',
      stateId: 'state-password',
      accept: '.pdf',
      multiple: false
    },
    'remove-password': {
      title: 'Remove Password',
      desc: 'Unlock and remove encryption from a protected PDF.',
      canvasTitle: 'DOCCRAFT / DECRYPT_UNLOCK',
      stateId: 'state-password',
      accept: '.pdf',
      multiple: false
    },
    'page-numbers': {
      title: 'Page Numbers',
      desc: 'Stamp continuous page numbering onto header or footer.',
      canvasTitle: 'DOCCRAFT / PAGINATION_INDEX',
      stateId: 'state-merge',
      accept: '.pdf',
      multiple: false
    },
    'pdf-to-word': {
      title: 'PDF → Word',
      desc: 'Extract document structure into Microsoft Word (.docx).',
      canvasTitle: 'DOCCRAFT / DOCX_EXPORT',
      stateId: 'state-merge',
      accept: '.pdf',
      multiple: false
    },
    'pdf-to-excel': {
      title: 'PDF → Excel',
      desc: 'Parse table matrices into Microsoft Excel (.xlsx).',
      canvasTitle: 'DOCCRAFT / XLSX_SPREADSHEET',
      stateId: 'state-merge',
      accept: '.pdf',
      multiple: false
    }
  }
};

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  setupCanvasDragAndDrop();
  initScrollObserver();
  initCompilationSequence();
  selectCanvasTool('merge');
});

/* ==========================================================================
   THEME MANAGEMENT (Persisted in LocalStorage)
   ========================================================================== */
function initTheme() {
  const savedTheme = localStorage.getItem('doccraft_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('doccraft_theme', newTheme);
  showToast(`Theme switched to ${newTheme} mode`, 'success');
}

/* ==========================================================================
   WORKSPACE COMPILATION SEQUENCE (~750ms)
   ========================================================================== */
function initCompilationSequence() {
  const statusPill = document.getElementById('canvas-active-status');
  if (statusPill) {
    statusPill.textContent = 'INITIALIZING WORKSPACE…';
    setTimeout(() => {
      statusPill.textContent = 'Merge PDF · Ready for Files';
    }, 750);
  }
}

/* ==========================================================================
   SCROLL REVEAL (IntersectionObserver — Single Shot, 60-144 FPS)
   ========================================================================== */
function initScrollObserver() {
  if (!('IntersectionObserver' in window)) {
    document.querySelectorAll('.reveal-on-scroll').forEach(el => el.classList.add('is-revealed'));
    return;
  }

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-revealed');
        obs.unobserve(entry.target); // Unobserve so it only runs once
      }
    });
  }, {
    root: null,
    threshold: 0.08,
    rootMargin: '0px 0px -40px 0px'
  });

  document.querySelectorAll('.reveal-on-scroll').forEach(el => {
    observer.observe(el);
  });
}

/* ==========================================================================
   TOOL SELECTION & CANVAS VISUAL STATE SWITCHER
   ========================================================================== */
function selectCanvasTool(toolId) {
  if (!CanvasStudio.toolMeta[toolId]) return;
  CanvasStudio.activeTool = toolId;

  const meta = CanvasStudio.toolMeta[toolId];

  // 1. Update Tool Rail Active State
  document.querySelectorAll('.rail-tool-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tool') === toolId);
  });

  // 2. Update Inspector & Canvas Headers
  const titleEl = document.getElementById('inspector-tool-title');
  const descEl = document.getElementById('inspector-tool-desc');
  const statusPill = document.getElementById('canvas-active-status');
  const paperTitle = document.getElementById('paper-doc-title');

  if (titleEl) titleEl.textContent = meta.title;
  if (descEl) descEl.textContent = meta.desc;
  if (statusPill) statusPill.textContent = `${meta.title} · Ready for Files`;
  if (paperTitle) paperTitle.textContent = meta.canvasTitle;

  // 3. Switch Canvas Visual State
  const states = ['state-merge', 'state-split', 'state-rotate', 'state-watermark', 'state-compress', 'state-password', 'state-images'];
  states.forEach(sId => {
    const el = document.getElementById(sId);
    if (el) el.style.display = (sId === meta.stateId) ? (sId === 'state-images' ? 'grid' : 'flex') : 'none';
  });

  // 4. Update File Input Target Attributes
  const fileInput = document.getElementById('master-file-input');
  if (fileInput) {
    fileInput.accept = meta.accept;
    fileInput.multiple = meta.multiple;
  }

  // 5. Toggle Dynamic Parameter Panes in Inspector
  document.querySelectorAll('.inspector-param-pane').forEach(pane => {
    pane.style.display = 'none';
  });

  const specificParamPane = document.getElementById(`params-${toolId}`);
  if (specificParamPane) {
    specificParamPane.style.display = 'block';
  } else {
    const defaultPane = document.getElementById('params-default');
    if (defaultPane) defaultPane.style.display = 'block';
  }

  // 6. Reset Workspace Staging
  resetCanvasWorkspace();

  // 7. Scroll to Workspace if Selected from Command Center
  const wsEl = document.getElementById('workspace');
  if (wsEl && window.scrollY > 450) {
    wsEl.scrollIntoView({ behavior: 'auto' });
  }
}

function onSplitModeChange() {
  const mode = document.getElementById('split-mode').value;
  const rangeWrap = document.getElementById('split-range-wrap');
  const chunkWrap = document.getElementById('split-chunk-wrap');

  if (rangeWrap) rangeWrap.style.display = mode === 'range' ? 'flex' : 'none';
  if (chunkWrap) chunkWrap.style.display = mode === 'chunk' ? 'flex' : 'none';
}

function updateRotateVisual() {
  const angle = document.getElementById('rotate-angle').value;
  const dial = document.getElementById('canvas-rotate-dial');
  if (dial) {
    dial.textContent = `⟳ ${angle}°`;
    dial.style.transform = `rotate(${angle}deg)`;
  }
}

function updateWmVisual() {
  const text = document.getElementById('wm-text').value;
  const overlay = document.getElementById('canvas-wm-text');
  if (overlay) {
    overlay.textContent = text || 'CONFIDENTIAL';
  }
}

/* ==========================================================================
   DRAG & DROP / FILE STAGING ON CANVAS
   ========================================================================== */
function setupCanvasDragAndDrop() {
  const stage = document.getElementById('canvas-stage');
  if (!stage) return;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    stage.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    stage.addEventListener(eventName, () => stage.classList.add('dragover'), false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    stage.addEventListener(eventName, () => stage.classList.remove('dragover'), false);
  });

  stage.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

function triggerFileInput() {
  const fileInput = document.getElementById('master-file-input');
  if (fileInput) fileInput.click();
}

function onFilesSelected(event) {
  const files = Array.from(event.target.files);
  stageFiles(files);
}

function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = Array.from(dt.files);
  stageFiles(files);
}

function stageFiles(newFiles) {
  if (!newFiles || newFiles.length === 0) return;

  const toolMeta = CanvasStudio.toolMeta[CanvasStudio.activeTool];

  if (toolMeta.multiple) {
    CanvasStudio.stagedFiles.push(...newFiles);
  } else {
    CanvasStudio.stagedFiles = [newFiles[0]];
  }

  updateStagedFilesUI();
}

function updateStagedFilesUI() {
  const files = CanvasStudio.stagedFiles;
  const countEl = document.getElementById('canvas-staged-count');
  const inspectorName = document.getElementById('inspector-file-name');
  const inspectorSize = document.getElementById('inspector-file-size');
  const processBtn = document.getElementById('btn-master-process');
  const statusPill = document.getElementById('canvas-active-status');

  if (files.length === 0) {
    if (countEl) countEl.textContent = '0 Files Loaded';
    if (inspectorName) inspectorName.textContent = 'None';
    if (inspectorSize) inspectorSize.textContent = '0 KB';
    if (processBtn) processBtn.disabled = true;
    return;
  }

  let totalBytes = 0;
  files.forEach(f => totalBytes += f.size);

  if (countEl) countEl.textContent = `${files.length} File${files.length > 1 ? 's' : ''} Staged`;
  if (inspectorName) inspectorName.textContent = files.length === 1 ? files[0].name : `${files[0].name} (+${files.length - 1})`;
  if (inspectorSize) inspectorSize.textContent = formatBytes(totalBytes);
  if (statusPill) statusPill.textContent = `${files.length} file(s) staged · Ready to process`;

  // Validation for multi-file operations
  if (CanvasStudio.activeTool === 'merge' && files.length < 2) {
    if (processBtn) processBtn.disabled = true;
    if (statusPill) statusPill.textContent = 'Add 1 more PDF to merge';
  } else {
    if (processBtn) processBtn.disabled = false;
  }
}

function resetCanvasWorkspace() {
  CanvasStudio.stagedFiles = [];
  const fileInput = document.getElementById('master-file-input');
  if (fileInput) fileInput.value = '';

  const dlBlock = document.getElementById('inspector-dl-block');
  if (dlBlock) dlBlock.classList.remove('active');

  const stage = document.getElementById('canvas-stage');
  if (stage) stage.classList.remove('is-processing');

  updateStagedFilesUI();
}

/* ==========================================================================
   MASTER OPERATION EXECUTION ROUTER (All 12 Endpoints)
   ========================================================================== */
async function executeActiveTool() {
  if (CanvasStudio.isProcessing || CanvasStudio.stagedFiles.length === 0) return;

  const tool = CanvasStudio.activeTool;
  const files = CanvasStudio.stagedFiles;

  setProcessingState(true);

  try {
    let response;
    const formData = new FormData();

    switch (tool) {
      case 'merge':
        if (files.length < 2) throw new Error('Please select at least 2 PDF files to merge.');
        files.forEach(f => formData.append('files', f));
        response = await postFormData('/api/merge', formData);
        break;

      case 'split':
        formData.append('file', files[0]);
        formData.append('mode', document.getElementById('split-mode').value);
        formData.append('range_str', document.getElementById('split-range').value);
        formData.append('chunk_size', document.getElementById('split-chunk').value);
        response = await postFormData('/api/split', formData);
        break;

      case 'rotate':
        formData.append('file', files[0]);
        formData.append('angle', document.getElementById('rotate-angle').value);
        formData.append('selection', document.getElementById('rotate-selection').value);
        response = await postFormData('/api/rotate', formData);
        break;

      case 'img2pdf':
        files.forEach(f => formData.append('files', f));
        response = await postFormData('/api/image-to-pdf', formData);
        break;

      case 'pdf2img':
        formData.append('file', files[0]);
        formData.append('format', document.getElementById('pdf2img-fmt').value);
        formData.append('dpi', document.getElementById('pdf2img-dpi').value);
        response = await postFormData('/api/pdf-to-image', formData);
        break;

      case 'watermark':
        formData.append('file', files[0]);
        formData.append('type', 'text');
        formData.append('text', document.getElementById('wm-text').value || 'CONFIDENTIAL');
        formData.append('opacity', document.getElementById('wm-opacity').value || '0.3');
        formData.append('angle', document.getElementById('wm-angle').value || '45');
        response = await postFormData('/api/watermark', formData);
        break;

      case 'compress':
        formData.append('file', files[0]);
        response = await postFormData('/api/compress', formData);
        break;

      case 'add-password':
        const pw = document.getElementById('pw-protect-val').value;
        if (!pw) throw new Error('Please specify an encryption password.');
        formData.append('file', files[0]);
        formData.append('password', pw);
        response = await postFormData('/api/add-password', formData);
        break;

      case 'remove-password':
        const unlockPw = document.getElementById('pw-unlock-val').value;
        if (!unlockPw) throw new Error('Please specify the password to unlock this document.');
        formData.append('file', files[0]);
        formData.append('password', unlockPw);
        response = await postFormData('/api/remove-password', formData);
        break;

      case 'page-numbers':
        formData.append('file', files[0]);
        formData.append('position', document.getElementById('pn-position').value);
        formData.append('start_num', document.getElementById('pn-start').value || '1');
        response = await postFormData('/api/page-numbers', formData);
        break;

      case 'pdf-to-word':
        formData.append('file', files[0]);
        response = await postFormData('/api/pdf-to-word', formData);
        break;

      case 'pdf-to-excel':
        formData.append('file', files[0]);
        response = await postFormData('/api/pdf-to-excel', formData);
        break;

      default:
        throw new Error(`Unrecognized tool: ${tool}`);
    }

    if (!response.success) {
      throw new Error(response.error || 'Operation failed.');
    }

    handleOperationSuccess(response);

  } catch (err) {
    showToast(err.message || 'Operation failed', 'error');
  } finally {
    setProcessingState(false);
  }
}

async function postFormData(endpoint, formData) {
  const res = await fetch(endpoint, {
    method: 'POST',
    body: formData
  });
  return await res.json();
}

function setProcessingState(isProcessing) {
  CanvasStudio.isProcessing = isProcessing;
  const stage = document.getElementById('canvas-stage');
  const processBtn = document.getElementById('btn-master-process');
  const statusPill = document.getElementById('canvas-active-status');

  // Trigger signature copper laser scanning line
  if (stage) stage.classList.toggle('is-processing', isProcessing);

  if (processBtn) {
    processBtn.disabled = isProcessing;
    processBtn.innerHTML = isProcessing 
      ? `<span>Compiling…</span>`
      : `<span>Execute Operation</span><svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg>`;
  }

  if (statusPill) {
    statusPill.textContent = isProcessing ? 'Compiling via PyMuPDF Core…' : 'Operation Ready';
  }
}

function handleOperationSuccess(data) {
  const dlBlock = document.getElementById('inspector-dl-block');
  const singleWrap = document.getElementById('single-dl-wrap');
  const multiWrap = document.getElementById('multi-dl-wrap');
  const masterDlBtn = document.getElementById('btn-master-download');

  if (!dlBlock) return;
  dlBlock.classList.add('active');

  if (data.files && Array.isArray(data.files)) {
    if (singleWrap) singleWrap.style.display = 'none';
    if (multiWrap) {
      multiWrap.style.display = 'flex';
      multiWrap.innerHTML = data.files.map(f => `
        <a href="${f.url}" download="${f.filename}" class="btn-download-artifact" style="font-size:0.76rem; height:34px; margin-bottom:4px;">
          <span>${escapeHTML(f.filename)}</span>
        </a>
      `).join('');
    }
  } else if (data.download_url) {
    if (multiWrap) multiWrap.style.display = 'none';
    if (singleWrap) singleWrap.style.display = 'block';
    if (masterDlBtn) {
      masterDlBtn.href = data.download_url;
      masterDlBtn.setAttribute('download', data.filename || 'DocCraft_Output');
    }
  }

  showToast('Operation completed successfully!', 'success');
}

/* ==========================================================================
   TOAST ENGINE & UTILS
   ========================================================================== */
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast-message ${type}`;
  toast.innerHTML = `<span>${escapeHTML(message)}</span>`;

  container.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('show'));

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 250);
  }, 3500);
}

function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0.00 KB';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function escapeHTML(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
