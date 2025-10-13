import { formatDate, formatBytes, showAlert } from './utils.js';

// Variables globales
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let lastTranslation = '';
let localDict = null;
let recognition = null;
let recognitionActive = false;
let currentRecordingLang = null;

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

// Mic helpers
const supportsMediaDevices = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

function humanizeGetUserMediaError(error) {
    const name = error && (error.name || error.code) || '';
    const msg = (error && error.message) || '';
    // Mensajes específicos por tipo de error
    switch (name) {
        case 'NotAllowedError':
        case 'PermissionDeniedError':
            return 'Permiso de micrófono denegado. Haz clic en el candado de la barra de direcciones y permite el micrófono para este sitio.';
        case 'NotFoundError':
        case 'DevicesNotFoundError':
            return 'No se encontró un micrófono. Verifica que el dispositivo esté conectado y habilitado en el sistema.';
        case 'NotReadableError':
        case 'TrackStartError':
            return 'El micrófono está siendo usado por otra aplicación. Ciérrala e inténtalo de nuevo.';
        case 'OverconstrainedError':
            return 'No se pudo satisfacer las restricciones de audio. Intenta con otro micrófono o revisa la configuración de audio del sistema.';
        case 'SecurityError':
            return 'Bloqueado por seguridad del navegador. Asegúrate de usar la app en un contexto seguro (https o localhost).';
        default:
            if (!window.isSecureContext) {
                return 'El navegador requiere un contexto seguro para usar el micrófono. Abre la app en https o en http://localhost/127.0.0.1.';
            }
            if (!supportsMediaDevices) {
                return 'Tu navegador no soporta captura de audio (getUserMedia). Actualiza a una versión moderna.';
            }
            return msg || 'Error al acceder al micrófono.';
    }
}

async function getMicrophoneStream() {
    if (!supportsMediaDevices) {
        throw new Error('getUserMedia no soportado');
    }
    if (!window.isSecureContext) {
        // 127.0.0.1 y localhost cuentan como seguros en la mayoría de navegadores
        throw new Error('Contexto inseguro');
    }
    // Intentar leer permiso si está disponible (no bloqueante)
    try {
        if (navigator.permissions && navigator.permissions.query) {
            const p = await navigator.permissions.query({ name: 'microphone' });
            if (p.state === 'denied') {
                throw new Error('Permiso de micrófono denegado en el navegador');
            }
        }
    } catch (_) {
        // Ignorar: la API de permisos no es estándar en todos los navegadores
    }

    const constraints = {
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            channelCount: 1
        }
    };
    return await navigator.mediaDevices.getUserMedia(constraints);
}

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
                    renderDetected(data);
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
                    renderDetected(data);
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

// Renderizador de idioma detectado
function renderDetected(data) {
    if (!data) return;
    const { detected_lang, scores } = data;
    if (!detected_lang) return;
    const qu = scores?.qu ?? 0;
    const es = scores?.es ?? 0;
    const conf = Math.max(qu, es);
    const label = detected_lang === 'qu' ? 'Kichwa' : 'Español';
    status.textContent = `Detectado: ${label} (confianza ${conf.toFixed(1)})`;
}

function updateRecordingState(recording) {
    isRecording = recording;
    if (recordingIndicator) {
        recordingIndicator.classList.toggle('d-none', !recording);
    }
    // Mantener botones de idioma habilitados para permitir detener con segundo clic
    btnKichwa.disabled = false;
    btnEspanol.disabled = false;
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
        // 1) Intentar Web Speech API (gratis, en el navegador)
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            if (recognitionActive) return;
            recognition = new SpeechRecognition();
            recognition.lang = lang === 'es' ? 'es-EC' : 'qu-EC';
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;
            // Intentar mantener la sesión de reconocimiento activa
            recognition.continuous = true;

            let finalText = '';
            recognition.onstart = () => {
                recognitionActive = true;
                updateRecordingState(true);
                setStatus('Escuchando...');
                currentRecordingLang = lang;
            };
            recognition.onresult = async (event) => {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript || '';
                    if (event.results[i].isFinal) finalText = transcript;
                }
                textoOriginal.value = transcript.trim();
            };
            recognition.onerror = (e) => {
                console.warn('SpeechRecognition error', e);
            };
            recognition.onend = async () => {
                recognitionActive = false;
                updateRecordingState(false);
                setStatus('');
                currentRecordingLang = null;
                const used = (finalText || textoOriginal.value || '').trim();
                if (used) {
                    const destLang = lang === 'es' ? 'qu' : 'es';
                    const translation = await translateText(used, lang, destLang);
                    textoTraducido.value = translation;
                    lastTranslation = translation;
                }
            };
            recognition.start();
            return;
        }

        // 2) Fallback al flujo actual (envía Blob al servidor)
        const stream = await getMicrophoneStream();
        const options = {};
        if (window.MediaRecorder && MediaRecorder.isTypeSupported) {
            if (MediaRecorder.isTypeSupported('audio/webm')) options.mimeType = 'audio/webm';
            else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) options.mimeType = 'audio/webm;codecs=opus';
        }
        mediaRecorder = new MediaRecorder(stream, options);
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
                    throw new Error(JSON.stringify(data));
                }
            } catch (err) {
                console.error('Error procesando audio:', err);
                setStatus('Error al procesar audio');
                let alertMsg = 'Error al procesar el audio';
                try {
                    const parsed = typeof err.message === 'string' ? JSON.parse(err.message) : err;
                    if (parsed && parsed.suggestion) {
                        alertMsg += '\n' + parsed.suggestion;
                    } else if (parsed && parsed.detail) {
                        alertMsg += '\n' + parsed.detail;
                    } else if (parsed && parsed.error) {
                        alertMsg += ': ' + parsed.error;
                    }
                } catch (e) {}
                showAlert(alertMsg, 'danger');
            }

            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        updateRecordingState(true);
        currentRecordingLang = lang;
        
    } catch (err) {
        console.error('Error al iniciar grabación:', err);
        const friendly = humanizeGetUserMediaError(err);
        showAlert(friendly, 'danger');
        updateRecordingState(false);
    }
}

function stopRecording() {
    if (recognition && recognitionActive) {
        try { recognition.stop(); } catch (_) {}
        recognitionActive = false;
    }
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        updateRecordingState(false);
    }
    currentRecordingLang = null;
}

// Event listeners (toggle: clic para iniciar, clic para detener)
btnKichwa.addEventListener('click', () => {
    if (isRecording && currentRecordingLang === 'qu') {
        stopRecording();
    } else if (!isRecording) {
        startRecording('qu');
    } else {
        // Si se está grabando en otro idioma, detener primero y luego iniciar
        stopRecording();
        startRecording('qu');
    }
});

btnEspanol.addEventListener('click', () => {
    if (isRecording && currentRecordingLang === 'es') {
        stopRecording();
    } else if (!isRecording) {
        startRecording('es');
    } else {
        stopRecording();
        startRecording('es');
    }
});

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
                // Lanzar el objeto completo como string para que el bloque catch lo muestre
                throw new Error(JSON.stringify(data));
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