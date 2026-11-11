// ==============================================================================
// GEN AI PLATFORM - COMPREHENSIVE FRONTEND INTERACTION ENGINE
// ==============================================================================

// Global Toast Notification Helper
function showToast(message, type = 'success') {
  const toastEl = document.getElementById('appToast');
  if (!toastEl) return;
  const icon = document.getElementById('toastIcon');
  const msgEl = document.getElementById('toastMessage');

  if (type === 'error' || type === 'danger') {
    icon.className = 'bi bi-exclamation-triangle-fill text-danger fs-5';
  } else if (type === 'warning') {
    icon.className = 'bi bi-exclamation-circle-fill text-warning fs-5';
  } else if (type === 'info') {
    icon.className = 'bi bi-info-circle-fill text-info fs-5';
  } else {
    icon.className = 'bi bi-check-circle-fill text-success fs-5';
  }

  msgEl.textContent = message;
  const toast = new bootstrap.Toast(toastEl, { delay: 4500 });
  toast.show();
}

// Client-side Blob Downloader
function downloadBlob(content, mimeType, filename) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Active Studio deliverable state
window.activeGeneratedContent = "";
window.activeGeneratedTitle = "Gen AI Content Transformation";

// Provider model dictionaries
const PROVIDER_MODELS = {
  gemini: [
    { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash (Fast, Recommended)" },
    { id: "gemini-2.5-pro", name: "Gemini 2.5 Pro (Deep Reasoning)" },
    { id: "gemini-1.5-flash", name: "Gemini 1.5 Flash (Legacy)" },
    { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro (Legacy)" }
  ],
  openai: [
    { id: "gpt-4o-mini", name: "GPT-4o Mini (Fast & Cost-Efficient)" },
    { id: "gpt-4o", name: "GPT-4o (High Intelligence Flagship)" },
    { id: "gpt-4-turbo", name: "GPT-4 Turbo" },
    { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo" }
  ],
  auto: [
    { id: "gemini-2.5-flash", name: "Auto-Selected Default Model" }
  ]
};

// Initialize Theme Management
function initTheme() {
  const savedTheme = localStorage.getItem('app_theme') || document.documentElement.getAttribute('data-bs-theme') || 'dark';
  setTheme(savedTheme);

  const toggleBtn = document.getElementById('themeToggleBtn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-bs-theme');
      const target = current === 'dark' ? 'light' : 'dark';
      setTheme(target);
      localStorage.setItem('app_theme', target);
    });
  }
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-bs-theme', theme);
  const icon = document.getElementById('themeIcon');
  if (icon) {
    icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
  }
}

// Content Studio Interactive Logic
document.addEventListener('DOMContentLoaded', () => {
  initTheme();

  const studioForm = document.getElementById('studioForm');
  const sourceText = document.getElementById('sourceText');
  const clearSourceBtn = document.getElementById('clearSourceBtn');
  const fileInput = document.getElementById('fileInput');
  const dropZone = document.getElementById('dropZone');
  const fileNameDisplay = document.getElementById('fileNameDisplay');
  const removeFileBtn = document.getElementById('removeFileBtn');
  const providerSelect = document.getElementById('providerSelect');
  const modelSelect = document.getElementById('modelSelect');
  const copyResultBtn = document.getElementById('copyResultBtn');
  const exportDropdown = document.getElementById('exportDropdown');
  const regenerateBtn = document.getElementById('regenerateBtn');
  const emptyState = document.getElementById('emptyState');
  const loadingState = document.getElementById('loadingState');
  const outputContent = document.getElementById('outputContent');
  const renderedMarkdown = document.getElementById('renderedMarkdown');
  const resultMeta = document.getElementById('resultMeta');
  const charCount = document.getElementById('charCount');
  const engineBadge = document.getElementById('engineBadge');
  const errorAlert = document.getElementById('aiErrorAlert');
  const errorTitle = document.getElementById('errorTitle');
  const errorMsg = document.getElementById('errorMessage');
  const errorAction = document.getElementById('errorActionArea');

  // Check for prefilled text from Document Hub
  const prefill = sessionStorage.getItem('studio_source_prefill');
  if (prefill && sourceText) {
    sourceText.value = prefill;
    sessionStorage.removeItem('studio_source_prefill');
    showToast('Document text loaded into Studio!');
  }

  // Clear source button
  if (clearSourceBtn && sourceText) {
    clearSourceBtn.addEventListener('click', () => {
      sourceText.value = '';
      if (fileInput) fileInput.value = '';
      if (fileNameDisplay) fileNameDisplay.textContent = 'Drag & drop document or browse';
      if (removeFileBtn) removeFileBtn.classList.add('d-none');
      sourceText.focus();
    });
  }

  // File remove button
  if (removeFileBtn && fileInput && fileNameDisplay) {
    removeFileBtn.addEventListener('click', () => {
      fileInput.value = '';
      fileNameDisplay.textContent = 'Drag & drop document or browse';
      removeFileBtn.classList.add('d-none');
    });
  }

  // File drag & drop handling
  if (dropZone && fileInput) {
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        fileNameDisplay.textContent = e.dataTransfer.files[0].name;
        if (removeFileBtn) removeFileBtn.classList.remove('d-none');
      }
    });
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        fileNameDisplay.textContent = fileInput.files[0].name;
        if (removeFileBtn) removeFileBtn.classList.remove('d-none');
      }
    });
  }

  // Dynamic Model Population based on selected Provider
  function updateModelOptions() {
    if (!providerSelect || !modelSelect) return;
    const provider = providerSelect.value;
    const models = PROVIDER_MODELS[provider] || PROVIDER_MODELS.gemini;
    modelSelect.innerHTML = '';
    models.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.name;
      modelSelect.appendChild(opt);
    });
  }

  if (providerSelect) {
    providerSelect.addEventListener('change', updateModelOptions);
    updateModelOptions();
  }

  // Helper to execute studio transformation
  async function executeTransformation() {
    const textVal = sourceText.value.trim();
    const hasFile = fileInput && fileInput.files.length > 0;

    if (!textVal && !hasFile) {
      showToast('Please enter source text or attach a document.', 'warning');
      sourceText.focus();
      return;
    }

    const btn = document.getElementById('transformBtn');
    const spinner = document.getElementById('btnSpinner');
    const icon = document.getElementById('btnIcon');
    const btnText = document.getElementById('btnText');

    btn.disabled = true;
    if (regenerateBtn) regenerateBtn.disabled = true;
    spinner.classList.remove('d-none');
    icon.classList.add('d-none');
    btnText.textContent = 'Generating with Online AI...';

    // UI state transitions
    if (errorAlert) errorAlert.classList.add('d-none');
    if (emptyState) emptyState.classList.add('d-none');
    if (outputContent) outputContent.classList.add('d-none');
    if (loadingState) loadingState.classList.remove('d-none');

    try {
      const formData = new FormData(studioForm);
      const response = await fetch('/api/transform', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (!response.ok) {
        const errorCategory = data.category || 'error';
        const err = new Error(data.error || 'Transformation request failed.');
        err.category = errorCategory;
        throw err;
      }

      window.activeGeneratedContent = data.output;
      window.activeGeneratedTitle = `${data.format} Deliverable`;

      if (loadingState) loadingState.classList.add('d-none');
      if (outputContent) outputContent.classList.remove('d-none');

      if (typeof marked !== 'undefined') {
        renderedMarkdown.innerHTML = marked.parse(data.output);
      } else {
        renderedMarkdown.textContent = data.output;
      }

      if (copyResultBtn) copyResultBtn.disabled = false;
      if (exportDropdown) exportDropdown.disabled = false;
      if (regenerateBtn) regenerateBtn.disabled = false;

      if (resultMeta) resultMeta.textContent = `${data.format} · Just Now`;
      if (charCount) charCount.textContent = `${data.output.length} characters • ${data.words_output} words`;
      if (engineBadge) {
        engineBadge.textContent = data.engine;
        engineBadge.className = 'badge bg-success-subtle text-success border border-success-subtle';
      }

      showToast('Deliverable transformed & preserved successfully!');
    } catch (err) {
      if (loadingState) loadingState.classList.add('d-none');
      if (emptyState) emptyState.classList.remove('d-none');

      if (errorAlert) {
        errorAlert.classList.remove('d-none');
        if (err.category === 'authentication_error') {
          errorTitle.textContent = 'API Authentication Required';
          errorAction.classList.remove('d-none');
        } else if (err.category === 'quota_error') {
          errorTitle.textContent = 'API Quota Exceeded';
          errorAction.classList.remove('d-none');
        } else if (err.category === 'network_error') {
          errorTitle.textContent = 'Network / Timeout Error';
          errorAction.classList.add('d-none');
        } else {
          errorTitle.textContent = 'AI Transformation Failed';
          errorAction.classList.add('d-none');
        }
        errorMsg.textContent = err.message;
      }

      if (engineBadge) {
        engineBadge.textContent = 'Generation Failed';
        engineBadge.className = 'badge bg-danger-subtle text-danger border border-danger-subtle';
      }

      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      if (regenerateBtn && window.activeGeneratedContent) regenerateBtn.disabled = false;
      spinner.classList.add('d-none');
      icon.classList.remove('d-none');
      btnText.textContent = 'Transform Content with Online AI';
    }
  }

  if (studioForm) {
    studioForm.addEventListener('submit', (e) => {
      e.preventDefault();
      executeTransformation();
    });
  }

  if (regenerateBtn) {
    regenerateBtn.addEventListener('click', () => {
      executeTransformation();
    });
  }

  // Copy result button
  if (copyResultBtn) {
    copyResultBtn.addEventListener('click', async () => {
      if (!window.activeGeneratedContent) return;
      try {
        await navigator.clipboard.writeText(window.activeGeneratedContent);
        showToast('Deliverable copied to clipboard!');
      } catch (err) {
        showToast('Clipboard access denied by browser.', 'error');
      }
    });
  }
});

// Dynamic Multi-format Export Handler
async function exportContent(formatType) {
  const content = window.activeGeneratedContent;
  const title = window.activeGeneratedTitle || "Gen AI Transformed Content";
  if (!content) {
    showToast('No content available to export.', 'warning');
    return;
  }

  try {
    showToast(`Preparing ${formatType.toUpperCase()} deliverable...`, 'info');
    const response = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content, type: formatType, title: title })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || 'Export request failed');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transformed_content.${formatType}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`${formatType.toUpperCase()} exported successfully!`);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// View History Item in Modal
async function viewHistoryItem(itemId) {
  try {
    const res = await fetch(`/api/history/${itemId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to load record');

    const item = data.item;
    document.getElementById('modalTitle').textContent = item.title || item.format;
    document.getElementById('modalFormat').textContent = item.format;
    document.getElementById('modalTone').textContent = `${item.provider || 'AI'} • ${item.tone || 'Standard'}`;
    document.getElementById('modalDate').textContent = item.created_at ? item.created_at.slice(0, 16).replace('T', ' ') : '';
    const modalContentEl = document.getElementById('modalContent');
    if (typeof marked !== 'undefined') {
      modalContentEl.innerHTML = marked.parse(item.output);
    } else {
      modalContentEl.textContent = item.output;
    }

    document.getElementById('modalCopyBtn').onclick = () => {
      navigator.clipboard.writeText(item.output).then(() => showToast('Copied to clipboard!'));
    };

    document.getElementById('modalDownloadBtn').onclick = () => {
      downloadBlob(item.output, 'text/plain', `${(item.format || 'deliverable').replace(/\s+/g, '_').toLowerCase()}.txt`);
    };

    const modal = new bootstrap.Modal(document.getElementById('historyModal'));
    modal.show();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
