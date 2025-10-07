import { formatDate, formatBytes, showAlert } from './utils.js';

// Estado global para estadísticas
let currentStats = {
    files: 0,
    words: 0,
    space: 0
};

function updateStats() {
    document.getElementById('stats-files').textContent = currentStats.files;
    document.getElementById('stats-words').textContent = currentStats.words;
    document.getElementById('stats-space').textContent = formatBytes(currentStats.space);

    // Actualizar progreso de almacenamiento
    const progressBar = document.querySelector('.storage-progress');
    const maxStorage = 100 * 1024 * 1024; // 100MB ejemplo
    const percentage = (currentStats.space / maxStorage) * 100;
    progressBar.style.width = `${Math.min(percentage, 100)}%`;
    progressBar.setAttribute('aria-valuenow', percentage);
}

async function loadUploads() {
    const container = document.getElementById('uploads-list');
    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center p-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        </div>
    `;

    try {
        const [uploadsResp, statsResp] = await Promise.all([
            fetch('/api/uploads'),
            fetch('/api/stats')
        ]);

        const [uploadsData, statsData] = await Promise.all([
            uploadsResp.json(),
            statsResp.json()
        ]);

        const uploads = uploadsData.uploads || [];

        // Actualizar estadísticas globales
        if (statsData.success) {
            currentStats = {
                files: statsData.stats.total_files || 0,
                words: statsData.stats.total_words || 0,
                space: statsData.stats.total_space || 0
            };
            updateStats();
        }

        // Actualizar estadísticas
        currentStats.files = uploads.length;
        currentStats.space = uploads.reduce((acc, u) => acc + (u.size || 0), 0);
        updateStats();

        if (uploads.length === 0) {
            container.innerHTML = `
                <div class="text-center p-5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="bi bi-file-earmark-music text-muted mb-3" viewBox="0 0 16 16">
                        <path d="M11 6.64a1 1 0 0 0-1.243-.97l-1 .25A1 1 0 0 0 8 6.89v4.306A2.572 2.572 0 0 0 7 11c-.5 0-.974.134-1.338.377-.36.24-.662.628-.662 1.123s.301.883.662 1.123c.364.243.839.377 1.338.377.5 0 .974-.134 1.338-.377.36-.24.662-.628.662-1.123V8.89l2-.5V6.64z"/>
                        <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                    </svg>
                    <p class="text-muted mb-0">No hay archivos subidos</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        uploads.forEach(u => {
            const item = document.createElement('div');
            item.className = 'list-group-item border-0 py-3';
            item.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="file-icon me-3">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-file-earmark-music" viewBox="0 0 16 16">
                            <path d="M11 6.64a1 1 0 0 0-1.243-.97l-1 .25A1 1 0 0 0 8 6.89v4.306A2.572 2.572 0 0 0 7 11c-.5 0-.974.134-1.338.377-.36.24-.662.628-.662 1.123s.301.883.662 1.123c.364.243.839.377 1.338.377.5 0 .974-.134 1.338-.377.36-.24.662-.628.662-1.123V8.89l2-.5V6.64z"/>
                            <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                        </svg>
                    </div>
                    <div class="flex-grow-1 min-width-0">
                        <h6 class="mb-0 text-truncate">${u.original_name || u.filename}</h6>
                        <p class="mb-0 small text-muted">
                            ${formatDate(u.uploaded_at)} · ${formatBytes(u.size || 0)}
                        </p>
                        ${u.text ? `
                            <div class="mt-2">
                                <div class="form-control form-control-sm bg-light border-0" style="font-size: 0.875rem;">${u.text}</div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="ms-3 d-flex gap-2">
                        <button class="btn btn-sm btn-play-audio" title="Reproducir">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-play-fill" viewBox="0 0 16 16">
                                <path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z"/>
                            </svg>
                        </button>
                        <a href="/static/audio/${u.filename}" download class="btn btn-sm btn-play-audio" title="Descargar">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download" viewBox="0 0 16 16">
                                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                            </svg>
                        </a>
                        <button class="btn btn-sm btn-delete" title="Eliminar">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                                <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                                <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;

            // Event listeners
            const playBtn = item.querySelector('.btn-play-audio');
            playBtn.addEventListener('click', () => {
                const url = '/static/audio/' + u.filename;
                const audio = new Audio(url);
                audio.play();
            });

            const deleteBtn = item.querySelector('.btn-delete');
            deleteBtn.addEventListener('click', async () => {
                if (!confirm('¿Estás seguro de que deseas eliminar este archivo?')) return;
                
                try {
                    const r = await fetch('/api/upload/' + u.filename, { method: 'DELETE' });
                    if (r.ok) {
                        item.remove();
                        currentStats.files--;
                        currentStats.space -= (u.size || 0);
                        updateStats();
                        
                        if (container.children.length === 0) {
                            loadUploads(); // Recargar para mostrar mensaje de vacío
                        }
                    } else {
                        alert('Error al eliminar el archivo');
                    }
                } catch (err) {
                    console.error(err);
                    alert('Error al eliminar el archivo');
                }
            });

            container.appendChild(item);
        });

    container.innerHTML = '';
    container.appendChild(table);
  } catch (err) {
    container.innerHTML = '<div class="alert alert-danger">Error cargando uploads</div>';
    console.error(err);
  }
}

window.addEventListener('load', loadUploads);

// función eliminada - ya no usamos sugerencias externas

window.addEventListener('load', loadUploads);

// Manejar import CSV
const csvInput = document.getElementById('csv-file');
const btnImportCsv = document.getElementById('btn-import-csv');
const importResult = document.getElementById('import-result');
if (btnImportCsv) {
  btnImportCsv.addEventListener('click', async () => {
    if (!csvInput.files || csvInput.files.length === 0) { importResult.textContent = 'Selecciona un archivo CSV'; return; }
    const fd = new FormData();
    fd.append('file', csvInput.files[0]);
    importResult.textContent = 'Importando...';
    try {
      const r = await fetch('/api/dictionary/import', { method: 'POST', body: fd });
      const data = await r.json();
      if (r.ok) {
        importResult.textContent = `Importado: ${data.added} entradas`;
        loadSuggestions();
      } else {
        importResult.textContent = 'Error al importar';
      }
    } catch (err) {
      importResult.textContent = 'Error al importar';
      console.error(err);
    }
  });
}
