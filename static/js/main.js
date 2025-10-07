import { formatDate, formatBytes, showAlert } from './utils.js';

// Variables globales
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let lastTranslation = '';
let localDict = null;

// Referencias DOM
const btnKichwa = document.getElementById('btn-kichwa');
const btnEspanol = document.getElementById('btn-espanol');
const btnPlay = document.getElementById('btn-play');
const textoOriginal = document.getElementById('texto-original');
const textoTraducido = document.getElementById('texto-traducido');
const textoManual = document.getElementById('texto-manual');
const btnTraducirManual = document.getElementById('btn-traducir-manual');
const recordingIndicator = document.querySelector('.recording-indicator');
const srcLangInputs = document.querySelectorAll('input[name="src-lang"]');
const status = document.getElementById('status');

// Cargar diccionario local una vez
async function loadLocalDictionary() {
    if (localDict) return localDict;
    try {
        const resp = await fetch('/api/dictionary');
        if (!resp.ok) return {};
        const data = await resp.json();
        localDict = data.dictionary || {};
        return localDict;
    } catch (e) {
        console.warn('No se pudo cargar diccionario local', e);
        return {};
    }
}

// Traducción usando diccionario local y fallback al servicio remoto
async function translateText(text, src, dest) {
    if (!text?.trim()) return '';

    try {
        setStatus('Traduciendo...');

        // 1. Intentar con diccionario local primero
        const dict = await loadLocalDictionary();
        let translation = text.trim().toLowerCase();

        if (src === 'es' && dest === 'qu') {
            const keys = Object.keys(dict).sort((a, b) => b.length - a.length);
            for (const key of keys) {
                if (key && translation.includes(key)) {
                    translation = translation.split(key).join(dict[key]);
                }
            }

            // Si la traducción no cambió, intentar con el servicio remoto
            if (translation === text.trim().toLowerCase()) {
                const resp = await fetch('/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, src, dest })
                });

                if (resp.ok) {
                    const data = await resp.json();
                    translation = data.translation || translation;
                }
            }
        } else if (src === 'qu' && dest === 'es') {
            // Para traducciones de Kichwa a Español, invertir el diccionario
            const reversedDict = {};
            for (const [key, value] of Object.entries(dict)) {
                reversedDict[value] = key;
            }

            const keys = Object.keys(reversedDict).sort((a, b) => b.length - a.length);
            for (const key of keys) {
                if (key && translation.includes(key)) {
                    translation = translation.split(key).join(reversedDict[key]);
                }
            }

            // Si no se encontró traducción, usar servicio remoto
            if (translation === text.trim().toLowerCase()) {
                const resp = await fetch('/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, src, dest })
                });

                if (resp.ok) {
                    const data = await resp.json();
                    translation = data.translation || translation;
                }
            }
        }

        setStatus('');
        return translation;
    } catch (error) {
        console.error('Error en traducción:', error);
        setStatus('Error al traducir');
        throw error;
    }
}

// TTS con fallback
async function speakText(text, langPrefer) {
    if (!text) return { ok: false };
    
    try {
        if ('speechSynthesis' in window) {
            const utter = new SpeechSynthesisUtterance(text);
            const voices = window.speechSynthesis.getVoices();
            if (voices?.length) {
                const preferred = voices.find(v => v.lang?.startsWith(langPrefer));
                if (preferred) utter.voice = preferred;
            }
            utter.lang = langPrefer;

            return new Promise((resolve) => {
                utter.onend = () => resolve({ ok: true });
                utter.onerror = (e) => resolve({ ok: false, error: e });
                window.speechSynthesis.speak(utter);
            });
        }
    } catch (e) {
        console.warn('speechSynthesis failed', e);
    }

    // Fallback: TTS por servidor
    try {
        const resp = await fetch('/text-to-speech', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text, 
                lang: langPrefer.startsWith('qu') ? 'qu' : langPrefer 
            })
        });
        const data = await resp.json();
        if (resp.ok && data.audio_url) {
            const audio = new Audio(data.audio_url);
            await audio.play();
            return { ok: true };
        }
    } catch (e) {
        console.error('TTS error:', e);
    }

    return { ok: false };
}

// Helpers
function setStatus(msg) {
    status.textContent = msg;
}

function updateRecordingState(recording) {
    isRecording = recording;
    recordingIndicator.classList.toggle('d-none', !recording);
    btnKichwa.disabled = recording;
    btnEspanol.disabled = recording;
    btnTraducirManual.disabled = recording;
}

function getSelectedSrcLang() {
    return document.querySelector('input[name="src-lang"]:checked').value;
}

// Event Listeners
async function handleManualTranslate() {
    const text = textoManual.value.trim();
    if (!text) {
        showAlert('Por favor escribe algo para traducir', 'warning');
        return;
    }

    try {
        btnTraducirManual.disabled = true;
        btnTraducirManual.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span class="ms-2">Traduciendo...</span>
        `;

        const srcLang = getSelectedSrcLang();
        const destLang = srcLang === 'es' ? 'qu' : 'es';

        textoOriginal.value = text;
        const translation = await translateText(text, srcLang, destLang);
        textoTraducido.value = translation;
        lastTranslation = translation;

    } catch (error) {
        console.error('Error al traducir:', error);
        showAlert('Error al traducir el texto', 'danger');
    } finally {
        btnTraducirManual.disabled = false;
        btnTraducirManual.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-translate me-2" viewBox="0 0 16 16">
                <path d="M4.545 6.714 4.11 8H3l1.862-5h1.284L8 8H6.833l-.435-1.286H4.545zm1.634-.736L5.5 3.956h-.049l-.679 2.022H6.18z"/>
                <path d="M0 2a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v3h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-3H2a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H2zm7.138 9.995c.193.301.402.583.63.846-.748.575-1.673 1.001-2.768 1.292.178.217.451.635.555.867 1.125-.359 2.08-.844 2.886-1.494.777.665 1.739 1.165 2.93 1.472.133-.254.414-.673.629-.89-1.125-.253-2.057-.694-2.82-1.284.681-.747 1.222-1.651 1.621-2.757H14V8h-3v1.047h.765c-.318.844-.74 1.546-1.272 2.13a6.066 6.066 0 0 1-.415-.492 1.988 1.988 0 0 1-.94.31z"/>
            </svg>
            Traducir
        `;
    }
}

// Manejo de grabación de voz
async function startRecording(lang) {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks);
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('lang', lang);

            try {
                setStatus('Procesando audio...');
                const resp = await fetch('/transcribe', {
                    method: 'POST',
                    body: formData
                });
                const data = await resp.json();

                if (resp.ok && data.text) {
                    textoOriginal.value = data.text;
                    const destLang = lang === 'es' ? 'qu' : 'es';
                    const translation = await translateText(data.text, lang, destLang);
                    textoTraducido.value = translation;
                    lastTranslation = translation;
                    setStatus('');
                } else {
                    throw new Error(data.error || 'Error al procesar audio');
                }
            } catch (err) {
                console.error('Error procesando audio:', err);
                setStatus('Error al procesar audio');
                showAlert('Error al procesar el audio', 'danger');
            }

            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        updateRecordingState(true);
        
    } catch (err) {
        console.error('Error al iniciar grabación:', err);
        showAlert('Error al acceder al micrófono', 'danger');
        updateRecordingState(false);
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        updateRecordingState(false);
    }
}

// Event listeners
btnKichwa.addEventListener('mousedown', () => startRecording('qu'));
btnKichwa.addEventListener('mouseup', stopRecording);
btnKichwa.addEventListener('mouseleave', stopRecording);

btnEspanol.addEventListener('mousedown', () => startRecording('es'));
btnEspanol.addEventListener('mouseup', stopRecording);
btnEspanol.addEventListener('mouseleave', stopRecording);

// Event listener para traducción manual
btnTraducirManual.addEventListener('click', handleManualTranslate);
textoManual.addEventListener('keypress', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleManualTranslate();
    }
});

// Event listener para reproducir traducción
btnPlay.addEventListener('click', async () => {
    if (!lastTranslation) return;
    const srcLang = getSelectedSrcLang();
    const destLang = srcLang === 'es' ? 'qu' : 'es';
    await speakText(lastTranslation, destLang);
});

// Manejo de subida de archivos
const uploadAudio = document.getElementById('upload-audio');
const uploadLang = document.getElementById('upload-lang');
const btnUpload = document.getElementById('btn-upload');
const uploadedList = document.getElementById('uploaded-list');

btnUpload.addEventListener('click', async () => {
    const files = uploadAudio.files;
    if (!files.length) {
        showAlert('Por favor selecciona al menos un archivo', 'warning');
        return;
    }

    const originalBtnText = btnUpload.innerHTML;
    btnUpload.disabled = true;
    btnUpload.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        <span class="ms-2">Procesando...</span>
    `;

    try {
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('lang', uploadLang.value);

            const resp = await fetch('/speech-to-text', {
                method: 'POST',
                body: formData
            });

            const data = await resp.json();
            if (resp.ok && data.text) {
                textoOriginal.value = data.text;
                const translation = await translateText(
                    data.text,
                    uploadLang.value,
                    uploadLang.value === 'es' ? 'qu' : 'es'
                );
                textoTraducido.value = translation;
                lastTranslation = translation;
            } else {
                throw new Error(data.error || 'Error al procesar archivo');
            }
        }

        uploadAudio.value = '';
        showAlert('Archivos procesados correctamente', 'success');
    } catch (err) {
        console.error('Error al procesar archivos:', err);
        let errorMsg = 'Error al procesar los archivos';
        
        // Intentar obtener más detalles del error
        if (err.message) {
            errorMsg += ': ' + err.message;
        }
        
        // Si hay una sugerencia del servidor (como instalar ffmpeg)
        try {
            const data = JSON.parse(err.message);
            if (data.suggestion) {
                errorMsg += '\n' + data.suggestion;
            }
        } catch (e) {}
        
        showAlert(errorMsg, 'danger');
    } finally {
        btnUpload.disabled = false;
        btnUpload.innerHTML = originalBtnText;
    }
});