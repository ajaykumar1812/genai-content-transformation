// Global Toast Notification Helper
function showToast(message, type = 'success') {
  const toastEl = document.getElementById('appToast');
  if (!toastEl) return;
  const icon = document.getElementById('toastIcon');
  const msgEl = document.getElementById('toastMessage');

  if (type === 'error' || type === 'danger') {
    icon.className = 'bi bi-exclamation-triangle-fill text-danger fs-5';
  } else if (type === 'info') {
    icon.className = 'bi bi-info-circle-fill text-info fs-5';
  } else {
    icon.className = 'bi bi-check-circle-fill text-success fs-5';
  }

  msgEl.textContent = message;
  const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
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

// Global active content state for Studio
window.activeGeneratedContent = "";
window.activeGeneratedTitle = "Gen AI Content Transformation";

// Content Studio Interactive Logic
document.addEventListener('DOMContentLoaded', () => {
  const studioForm = document.getElementById('studioForm');
  const sourceText = document.getElementById('sourceText');
  const clearSourceBtn = document.getElementById('clearSourceBtn');
  const fileInput = document.getElementById('fileInput');
  const dropZone = document.getElementById('dropZone');
  const fileNameDisplay = document.getElementById('fileNameDisplay');
  const copyResultBtn = document.getElementById('copyResultBtn');
  const exportDropdown = document.getElementById('exportDropdown');
  const emptyState = document.getElementById('emptyState');
  const outputContent = document.getElementById('outputContent');
  const resultMeta = document.getElementById('resultMeta');
  const charCount = document.getElementById('charCount');
  const engineBadge = document.getElementById('engineBadge');
  const pptxExportOption = document.getElementById('pptxExportOption');
  const outputFormat = document.getElementById('outputFormat');

  // Clear source button
  if (clearSourceBtn && sourceText) {
    clearSourceBtn.addEventListener('click', () => {
      sourceText.value = '';
      if (fileInput) fileInput.value = '';
      if (fileNameDisplay) fileNameDisplay.textContent = 'Drag & drop document or browse files';
      sourceText.focus();
    });
  }

  // File drag & drop
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
      }
    });
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        fileNameDisplay.textContent = fileInput.files[0].name;
      }
    });
  }

  // Toggle PPTX option based on format
  if (outputFormat && pptxExportOption) {
    outputFormat.addEventListener('change', () => {
      if (outputFormat.value === 'Presentation Deck') {
        pptxExportOption.classList.remove('d-none');
      }
    });
  }

  // Handle Studio Transformation Form Submit
  if (studioForm) {
    studioForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const textVal = sourceText.value.trim();
      const hasFile = fileInput && fileInput.files.length > 0;

      if (!textVal && !hasFile) {
        showToast('Please enter text or choose a document file.', 'error');
        return;
      }

      const btn = document.getElementById('transformBtn');
      const spinner = document.getElementById('btnSpinner');
      const icon = document.getElementById('btnIcon');
      const btnText = document.getElementById('btnText');

      btn.disabled = true;
      spinner.classList.remove('d-none');
      icon.classList.add('d-none');
      btnText.textContent = 'Transforming Content...';

      try {
        const formData = new FormData(studioForm);
        const response = await fetch('/api/transform', {
          method: 'POST',
          body: formData
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || 'Transformation request failed.');
        }

        window.activeGeneratedContent = data.output;
        window.activeGeneratedTitle = `${data.format} Deliverable`;

        emptyState.classList.add('d-none');
        outputContent.classList.remove('d-none');
        outputContent.textContent = data.output;

        copyResultBtn.disabled = false;
        exportDropdown.disabled = false;

        resultMeta.textContent = `${data.format} · Just Now`;
        charCount.textContent = `${data.output.length} characters • ${data.words_output} words`;
        engineBadge.textContent = data.engine;
        engineBadge.className = 'badge bg-success';

        showToast('Content transformed and saved successfully!');
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        btn.disabled = false;
        spinner.classList.add('d-none');
        icon.classList.remove('d-none');
        btnText.textContent = 'Transform Content';
      }
    });
  }

  // Copy result button
  if (copyResultBtn) {
    copyResultBtn.addEventListener('click', async () => {
      if (!window.activeGeneratedContent) return;
      try {
        await navigator.clipboard.writeText(window.activeGeneratedContent);
        showToast('Content copied to clipboard!');
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
    showToast('No content available to export.', 'error');
    return;
  }

  try {
    showToast(`Preparing ${formatType.toUpperCase()} file...`, 'info');
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
    document.getElementById('modalTone').textContent = `${item.audience || 'General'} • ${item.tone || 'Standard'}`;
    document.getElementById('modalDate').textContent = item.created_at ? item.created_at.slice(0, 16).replace('T', ' ') : '';
    document.getElementById('modalContent').textContent = item.output;

    document.getElementById('modalCopyBtn').onclick = () => {
      navigator.clipboard.writeText(item.output).then(() => showToast('Copied to clipboard!'));
    };

    document.getElementById('modalDownloadBtn').onclick = () => {
      downloadBlob(item.output, 'text/plain', `${(item.format || 'output').replace(/\s+/g, '_').toLowerCase()}.txt`);
    };

    const modal = new bootstrap.Modal(document.getElementById('historyModal'));
    modal.show();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
