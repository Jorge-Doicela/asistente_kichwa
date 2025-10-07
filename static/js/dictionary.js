import { showAlert } from './utils.js';

// Estado global del diccionario
let dictionary = {};

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
function renderDictionary(filter = '') {
    const container = document.getElementById('dictionary-list');
    container.innerHTML = '';

    // Filtrar y ordenar entradas
    const entries = Object.entries(dictionary)
        .filter(([es]) => !filter || es.toLowerCase().includes(filter.toLowerCase()))
        .sort(([a], [b]) => a.localeCompare(b));

    if (entries.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="3" class="text-center py-4 text-muted">
                    ${filter ? 'No se encontraron palabras' : 'No hay palabras en el diccionario'}
                </td>
            </tr>
        `;
        return;
    }

    for (const [es, ki] of entries) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${es}</td>
            <td>${ki}</td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-danger btn-delete" title="Eliminar">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                        <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                    </svg>
                </button>
            </td>
        `;

        // Event listeners
        const deleteBtn = row.querySelector('.btn-delete');
        deleteBtn.addEventListener('click', () => deleteWord(es));

        container.appendChild(row);
    }
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

// Event Listeners
document.getElementById('form-new-word').addEventListener('submit', async (e) => {
    e.preventDefault();
    const spanish = document.getElementById('word-spanish').value.trim().toLowerCase();
    const kichwa = document.getElementById('word-kichwa').value.trim();
    
    if (await addWord(spanish, kichwa)) {
        e.target.reset();
    }
});

document.getElementById('search-dictionary').addEventListener('input', (e) => {
    renderDictionary(e.target.value.trim());
});

document.getElementById('btn-search').addEventListener('click', () => {
    const searchTerm = document.getElementById('search-dictionary').value.trim();
    renderDictionary(searchTerm);
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
loadDictionary();