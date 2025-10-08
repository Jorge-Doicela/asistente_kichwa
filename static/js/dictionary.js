import { showAlert } from './utils.js';

// Estado global del diccionario
let dictionary = {};
let currentFilter = '';
let sortBy = 'spanish';
let sortDir = 'asc';
let pageSize = 10;
let currentPage = 1;
let swapped = false; // controla si se muestran columnas invertidas

// Cargar diccionario
async function loadDictionary() {
    try {
        const r = await fetch('/api/dictionary');
        const data = await r.json();
        dictionary = data.dictionary || {};
        renderDictionary();
    } catch (err) {
        console.error('Error cargando diccionario:', err);
        showAlert('Error cargando el diccionario', 'danger');
    }
}

// Renderizar diccionario
function renderDictionary(filter = currentFilter) {
    const container = document.getElementById('dictionary-list');
    container.innerHTML = '';

    // Filtrar y ordenar entradas
    let entries = Object.entries(dictionary)
        .filter(([es, qu]) => {
            const left = swapped ? qu : es;
            return !filter || left.toLowerCase().includes(filter.toLowerCase());
        })
        .sort((a, b) => {
            const valA = (sortBy === 'spanish' ? a[0] : a[1]) || '';
            const valB = (sortBy === 'spanish' ? b[0] : b[1]) || '';
            const cmp = valA.localeCompare(valB);
            return sortDir === 'asc' ? cmp : -cmp;
        });

    if (entries.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="3" class="text-center py-4 text-muted">
                    ${filter ? 'No se encontraron palabras' : 'No hay palabras en el diccionario'}
                </td>
            </tr>
        `;
        document.getElementById('pagination').innerHTML = '';
        return;
    }

    // Paginación
    const totalItems = entries.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const pageEntries = entries.slice(start, end);

    for (const [es, ki] of pageEntries) {
        const row = document.createElement('tr');
        const colA = swapped ? ki : es;
        const colB = swapped ? es : ki;
        row.innerHTML = `
            <td class="cell-a">${colA}</td>
            <td class="cell-b">${colB}</td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-secondary btn-edit me-2" title="Editar">✏️</button>
                <button class="btn btn-sm btn-outline-danger btn-delete" title="Eliminar">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                        <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                    </svg>
                </button>
            </td>
        `;

        // Event listeners
        row.querySelector('.btn-delete').addEventListener('click', () => deleteWord(es));
        row.querySelector('.btn-edit').addEventListener('click', () => inlineEdit(row, es, ki));

        container.appendChild(row);
    }

    // Render paginación
    renderPagination(totalPages);
}

// Agregar palabra
async function addWord(spanish, kichwa) {
    try {
        const r = await fetch('/api/dictionary/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({spanish, kichwa})
        });

        if (r.ok) {
            dictionary[spanish] = kichwa;
            renderDictionary();
            showAlert('Palabra agregada correctamente', 'success');
            return true;
        } else {
            throw new Error('Error agregando palabra');
        }
    } catch (err) {
        console.error('Error:', err);
        showAlert('Error agregando palabra', 'danger');
        return false;
    }
}

// Eliminar palabra
async function deleteWord(spanish) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta palabra?')) return;

    try {
        const r = await fetch('/api/dictionary/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({spanish})
        });

        if (r.ok) {
            delete dictionary[spanish];
            renderDictionary();
            showAlert('Palabra eliminada correctamente', 'success');
        } else {
            throw new Error('Error eliminando palabra');
        }
    } catch (err) {
        console.error('Error:', err);
        showAlert('Error eliminando palabra', 'danger');
    }
}

// Editar en línea
function inlineEdit(row, spanish, kichwa) {
    const cellA = row.querySelector('.cell-a');
    const cellB = row.querySelector('.cell-b');
    const originalA = cellA.textContent;
    const originalB = cellB.textContent;
    const inputA = document.createElement('input');
    const inputB = document.createElement('input');
    inputA.className = 'form-control form-control-sm';
    inputB.className = 'form-control form-control-sm';
    inputA.value = originalA;
    inputB.value = originalB;
    cellA.innerHTML = '';
    cellB.innerHTML = '';
    cellA.appendChild(inputA);
    cellB.appendChild(inputB);

    const actions = row.querySelector('td.text-end');
    const prevHTML = actions.innerHTML;
    actions.innerHTML = '<button class="btn btn-sm btn-success me-2">Guardar</button><button class="btn btn-sm btn-outline-secondary">Cancelar</button>';
    const btnSave = actions.querySelector('.btn-success');
    const btnCancel = actions.querySelector('.btn-outline-secondary');

    btnCancel.addEventListener('click', () => {
        cellA.textContent = originalA;
        cellB.textContent = originalB;
        actions.innerHTML = prevHTML;
        actions.querySelector('.btn-delete').addEventListener('click', () => deleteWord(spanish));
        actions.querySelector('.btn-edit').addEventListener('click', () => inlineEdit(row, spanish, kichwa));
    });

    btnSave.addEventListener('click', async () => {
        // Determinar nuevo par es/qu en función del estado de intercambio
        let newSpanish, newKichwa;
        if (swapped) {
            newSpanish = inputB.value.trim().toLowerCase();
            newKichwa = inputA.value.trim();
        } else {
            newSpanish = inputA.value.trim().toLowerCase();
            newKichwa = inputB.value.trim();
        }

        if (!newSpanish || !newKichwa) {
            showAlert('Completa ambos campos', 'warning');
            return;
        }

        try {
            const r = await fetch('/api/dictionary/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ spanish, spanish_new: newSpanish, kichwa: newKichwa })
            });
            const data = await r.json();
            if (!r.ok || !data.ok) throw new Error(data.error || 'Error actualizando');
            // Actualizar estado local
            delete dictionary[spanish];
            dictionary[newSpanish] = newKichwa;
            renderDictionary(currentFilter);
            showAlert('Entrada actualizada', 'success');
        } catch (e) {
            console.error(e);
            showAlert('Error al actualizar', 'danger');
        }
    });
}

// Paginación UI
function renderPagination(totalPages) {
    const ul = document.getElementById('pagination');
    ul.innerHTML = '';
    const createItem = (label, page, disabled = false, active = false) => {
        const li = document.createElement('li');
        li.className = `page-item${disabled ? ' disabled' : ''}${active ? ' active' : ''}`;
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = label;
        a.addEventListener('click', (e) => {
            e.preventDefault();
            if (disabled) return;
            currentPage = page;
            renderDictionary(currentFilter);
        });
        li.appendChild(a);
        return li;
    };

    ul.appendChild(createItem('«', Math.max(1, currentPage - 1), currentPage === 1));
    for (let p = 1; p <= totalPages; p++) {
        if (p === 1 || p === totalPages || Math.abs(p - currentPage) <= 2) {
            ul.appendChild(createItem(String(p), p, false, p === currentPage));
        } else if (p === 2 && currentPage > 4) {
            const li = document.createElement('li');
            li.className = 'page-item disabled';
            li.innerHTML = '<span class="page-link">…</span>';
            ul.appendChild(li);
        } else if (p === totalPages - 1 && currentPage < totalPages - 3) {
            const li = document.createElement('li');
            li.className = 'page-item disabled';
            li.innerHTML = '<span class="page-link">…</span>';
            ul.appendChild(li);
        }
    }
    ul.appendChild(createItem('»', Math.min(totalPages, currentPage + 1), currentPage === totalPages));
}

// Event Listeners
document.getElementById('form-new-word').addEventListener('submit', async (e) => {
    e.preventDefault();
    const spanish = document.getElementById('word-spanish').value.trim().toLowerCase();
    const kichwa = document.getElementById('word-kichwa').value.trim();
    
    if (await addWord(spanish, kichwa)) {
        e.target.reset();
    }
});

// Debounce search
const searchInput = document.getElementById('search-dictionary');
let debounceTimer = null;
searchInput.addEventListener('input', (e) => {
    const value = e.target.value.trim();
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        currentFilter = value;
        currentPage = 1;
        renderDictionary(currentFilter);
    }, 250);
});

document.getElementById('btn-search').addEventListener('click', () => {
    currentFilter = document.getElementById('search-dictionary').value.trim();
    currentPage = 1;
    renderDictionary(currentFilter);
});

// Controles de orden y tamaño de página
document.getElementById('sort-by').addEventListener('change', (e) => {
    sortBy = e.target.value;
    currentPage = 1;
    renderDictionary(currentFilter);
});
document.getElementById('sort-dir').addEventListener('change', (e) => {
    sortDir = e.target.value;
    renderDictionary(currentFilter);
});
document.getElementById('page-size').addEventListener('change', (e) => {
    pageSize = parseInt(e.target.value, 10) || 10;
    currentPage = 1;
    renderDictionary(currentFilter);
});

// Exportar CSV/JSON
document.getElementById('btn-export-csv').addEventListener('click', async () => {
    try {
        const r = await fetch('/api/dictionary/export?format=csv');
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'dictionary_es_qu.csv';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error(e);
        showAlert('No se pudo exportar CSV', 'danger');
    }
});
document.getElementById('btn-export-json').addEventListener('click', async () => {
    try {
        const r = await fetch('/api/dictionary/export?format=json');
        const data = await r.json();
        const blob = new Blob([JSON.stringify(data.dictionary || {}, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'dictionary_es_qu.json';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error(e);
        showAlert('No se pudo exportar JSON', 'danger');
    }
});

// Intercambio de columnas visuales
document.getElementById('toggle-direction').addEventListener('click', () => {
    swapped = !swapped;
    // Actualizar encabezados
    const thA = document.getElementById('th-col-a');
    const thB = document.getElementById('th-col-b');
    const temp = thA.textContent;
    thA.textContent = thB.textContent;
    thB.textContent = temp;
    // Re-render
    renderDictionary(currentFilter);
});

// Manejar importación CSV
const csvInput = document.getElementById('csv-file');
const btnImportCsv = document.getElementById('btn-import-csv');
const importResult = document.getElementById('import-result');

btnImportCsv.addEventListener('click', async () => {
    if (!csvInput.files || csvInput.files.length === 0) {
        importResult.textContent = 'Selecciona un archivo CSV';
        importResult.className = 'alert alert-warning mt-2';
        return;
    }

    const fd = new FormData();
    fd.append('file', csvInput.files[0]);
    
    importResult.textContent = 'Importando...';
    importResult.className = 'alert alert-info mt-2';
    
    try {
        const r = await fetch('/api/dictionary/import', {
            method: 'POST',
            body: fd
        });
        
        const data = await r.json();
        if (r.ok) {
            importResult.textContent = `Importado: ${data.added} entradas`;
            importResult.className = 'alert alert-success mt-2';
            loadDictionary();  // Recargar diccionario
            csvInput.value = '';  // Limpiar input
        } else {
            throw new Error(data.error || 'Error al importar');
        }
    } catch (err) {
        importResult.textContent = 'Error al importar diccionario';
        importResult.className = 'alert alert-danger mt-2';
        console.error(err);
    }
});

// Cargar diccionario al inicio
// Cargar diccionario al inicio
loadDictionary();