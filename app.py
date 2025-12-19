from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
import requests
import uuid
import json
import shutil
from datetime import datetime
import threading
import unicodedata
import re
import random

app = Flask(__name__)
CORS(app)

# Configuración de carpetas
AUDIO_FOLDER = os.path.join('static', 'audio')
DATA_FOLDER = os.path.join('data')
DICT_PATH = os.path.join(DATA_FOLDER, 'dictionary_es_qu.json')
BACKUP_DIR = os.path.join(DATA_FOLDER, 'backups')
HISTORY_PATH = os.path.join(DATA_FOLDER, 'history.json')
META_PATH = os.path.join(DATA_FOLDER, 'meta.json')

os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Lock reentrante para permitir llamadas anidadas (evita deadlocks)
DICT_LOCK = threading.RLock()

def _now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

def _utcnow():
    return datetime.utcnow()

def _file_mtime_utc(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.utcfromtimestamp(ts)
    except Exception:
        return None

def _cleanup_audio_folder(ttl_minutes=60):
    """Elimina archivos en AUDIO_FOLDER más antiguos que ttl_minutes.

    Se ejecuta periódicamente en un hilo daemon.
    """
    try:
        now = _utcnow()
        ttl = max(1, int(ttl_minutes))
        for name in os.listdir(AUDIO_FOLDER):
            path = os.path.join(AUDIO_FOLDER, name)
            if not os.path.isfile(path):
                continue
            mtime = _file_mtime_utc(path)
            if not mtime:
                continue
            age_min = (now - mtime).total_seconds() / 60.0
            if age_min > ttl:
                try:
                    os.remove(path)
                except Exception:
                    pass
    except Exception:
        pass

def _start_audio_cleanup_thread():
    """Lanza un hilo que limpia la carpeta de audio cada cierto intervalo."""
    try:
        ttl_env = os.getenv('AUDIO_TTL_MINUTES')
        try:
            ttl_minutes = int(ttl_env) if ttl_env else 60
        except Exception:
            ttl_minutes = 60

        interval_env = os.getenv('AUDIO_CLEAN_INTERVAL_SECONDS')
        try:
            interval_seconds = int(interval_env) if interval_env else 900  # 15 min
        except Exception:
            interval_seconds = 900

        def _loop():
            import time
            while True:
                _cleanup_audio_folder(ttl_minutes)
                try:
                    time.sleep(max(60, interval_seconds))
                except Exception:
                    # si sleep falla, continuar
                    pass

        t = threading.Thread(target=_loop, daemon=True)
        t.start()
    except Exception:
        pass

def _safe_read_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default

def _safe_write_json(path, data):
    tmp_path = f"{path}.tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)

def ensure_meta_initialized():
    meta = _safe_read_json(META_PATH, {})
    changed = False
    if 'current_version' not in meta:
        meta['current_version'] = 0
        changed = True
    if 'last_updated' not in meta:
        meta['last_updated'] = None
        changed = True
    if 'entry_count' not in meta:
        # inicializar con conteo actual si existe
        dic = _safe_read_json(DICT_PATH, {})
        meta['entry_count'] = len(dic)
        changed = True
    if changed:
        _safe_write_json(META_PATH, meta)
    return meta

def load_dictionary():
    return _safe_read_json(DICT_PATH, {})

# -------------------- Normalización y segmentación Kichwa --------------------
_NON_ALNUM_RE = re.compile(r"[^a-zñáéíóúü-]+", re.IGNORECASE)
_DASHES_RE = re.compile(r"[-_·•]+")

def remove_diacritics(text):
    # Normaliza eliminando tildes, conserva ñ
    if not text:
        return ''
    normalized = unicodedata.normalize('NFD', text)
    out_chars = []
    for ch in normalized:
        # Mantener ñ/Ñ explícitamente
        if ch in ('ñ', 'Ñ'):
            out_chars.append(ch)
            continue
        # Omitir marcas diacríticas
        if unicodedata.category(ch) == 'Mn':
            continue
        out_chars.append(ch)
    return unicodedata.normalize('NFC', ''.join(out_chars))

def normalize_kichwa_token(token):
    # minúsculas, quitar tildes, normalizar guiones múltiples a uno, recortar
    t = token.strip().lower()
    t = remove_diacritics(t)
    t = _DASHES_RE.sub('-', t)
    t = t.strip('-')
    return t

def tokenize_kichwa(text):
    if not text:
        return []
    # Reemplazar separadores no alfanum a espacios, preservar guiones como partidores de morfemas
    cleaned = _NON_ALNUM_RE.sub(' ', text)
    tokens = []
    for raw in cleaned.split():
        t = normalize_kichwa_token(raw)
        if not t:
            continue
        # Segmentar por sufijos comunes kichwa (heurístico)
        # Lista básica de morfemas frecuentes
        suffixes = ['-mi', '-m', '-shi', '-sh', '-ka', '-k', '-ta', '-n', '-pak', '-paj', '-sapa', '-kuna']
        # asegurar formato con guión
        parts = t.split('-') if '-' in t else [t]
        # Mantener token completo y sus partes base
        tokens.append(t)
        for p in parts:
            if p and p != t:
                tokens.append(p)
        # Generar variantes sin sufijos con y sin guiones
        for suf in suffixes:
            suf_clean = suf.lstrip('-')
            if t.endswith(suf_clean):
                base = t[: -len(suf_clean)]
                base = base.rstrip('-')
                if base:
                    tokens.append(base)
    # Unificar y devolver únicos preservando orden
    seen = set()
    uniq = []
    for tok in tokens:
        if tok not in seen:
            seen.add(tok)
            uniq.append(tok)
    return uniq

def best_kichwa_match(es_to_qu_dic, text):
    # Intenta reemplazos por frases más largas primero usando normalización/tokenización
    if not text:
        return text
    # Construir mapping normalizado -> original kichwa
    normalized_map = {}
    for es, qu in es_to_qu_dic.items():
        es_norm = normalize_kichwa_token(es)
        if es_norm:
            normalized_map[es_norm] = qu

    # Reemplazo sobre texto normalizado, pero preservando espacios del original
    txt_norm = normalize_kichwa_token(text)
    # Ordenar claves por longitud desc para coincidencias más largas
    keys = sorted(normalized_map.keys(), key=lambda k: -len(k))
    out = txt_norm
    for k in keys:
        if not k: continue
        if k in out:
            out = out.replace(k, normalize_kichwa_token(normalized_map[k]))
    # Devolver versión normalizada traducida; el front muestra el valor final
    return out

# -------------------- Detección automática de idioma --------------------
_KICHWA_CHAR_HINTS = set(list('kqshñ'))
_SPANISH_ONLY_HINTS = set(list('áéíóú'))
_KICHWA_COMMON_TOKENS = {'ñuka','kan','pay','kanka','mashi','alli','shuk','wasi','yachay','mikuy','kawsay','kawsankichu','rimay','mikhuna','yakuk'}

def detect_lang_text(text):
    """Devuelve 'qu' o 'es' heurísticamente para texto."""
    lang, _, _ = detect_lang_with_score(text)
    return lang

def detect_lang_with_score(text):
    """Retorna (lang, score_qu, score_es)."""
    if not text:
        return ('es', 0.0, 0.0)
    t = normalize_kichwa_token(text)
    hints_qu = sum(1 for ch in t if ch in _KICHWA_CHAR_HINTS)
    hints_es = sum(1 for ch in t if ch in _SPANISH_ONLY_HINTS)
    tokens = set(tokenize_kichwa(t))
    common_qu = len(tokens & _KICHWA_COMMON_TOKENS)
    score_qu = hints_qu * 1.0 + common_qu * 2.0
    score_es = hints_es * 1.0
    lang = 'qu' if score_qu >= max(1.0, score_es) else 'es'
    return (lang, float(score_qu), float(score_es))

def backup_dictionary(reason="manual"):
    # Copia con timestamp y versión
    meta = ensure_meta_initialized()
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    version = meta.get('current_version', 0)
    suffix = f"v{version}_{ts}"
    backup_path = os.path.join(BACKUP_DIR, f"dictionary_es_qu_{suffix}.json")
    dic = load_dictionary()
    payload = {
        'metadata': {
            'reason': reason,
            'created_at': _now_iso(),
            'source': 'live-dictionary',
            'version': version,
            'entries': len(dic)
        },
        'dictionary': dic
    }
    _safe_write_json(backup_path, payload)
    return backup_path

def append_history(action, spanish_before=None, spanish_after=None, kichwa_before=None, kichwa_after=None, info=None):
    history = _safe_read_json(HISTORY_PATH, [])
    entry = {
        'timestamp': _now_iso(),
        'action': action,
        'spanish_before': spanish_before,
        'spanish_after': spanish_after,
        'kichwa_before': kichwa_before,
        'kichwa_after': kichwa_after,
        'info': info or {}
    }
    history.append(entry)
    _safe_write_json(HISTORY_PATH, history)

def save_dictionary(new_dic, reason, info=None):
    with DICT_LOCK:
        # Respaldo del estado actual
        backup_dictionary(reason=reason)
        # Guardar nuevo estado
        _safe_write_json(DICT_PATH, new_dic)
        # Actualizar meta
        meta = ensure_meta_initialized()
        meta['current_version'] = int(meta.get('current_version', 0)) + 1
        meta['last_updated'] = _now_iso()
        meta['entry_count'] = len(new_dic)
        _safe_write_json(META_PATH, meta)
        # Guardar última versión final como backup labeled post-save
        try:
            ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            suffix = f"v{meta['current_version']}_{ts}_postsave"
            backup_path = os.path.join(BACKUP_DIR, f"dictionary_es_qu_{suffix}.json")
            payload = {
                'metadata': {
                    'reason': f"{reason}-postsave",
                    'created_at': _now_iso(),
                    'source': 'new-dictionary',
                    'version': meta['current_version'],
                    'entries': len(new_dic),
                    'info': info or {}
                },
                'dictionary': new_dic
            }
            _safe_write_json(backup_path, payload)
        except Exception:
            pass
        return True

# Inicialización de meta e historial al iniciar la app
try:
    ensure_meta_initialized()
    if not os.path.exists(HISTORY_PATH):
        _safe_write_json(HISTORY_PATH, [])
    # Iniciar limpieza periódica de audios
    _start_audio_cleanup_thread()
except Exception:
    pass

# Inicializar traductor
translator = GoogleTranslator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/diccionario')
def diccionario_page():
    return render_template('diccionario.html')

@app.route('/estudiar')
def estudiar_page():
    return render_template('estudiar.html')

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    # Verificar archivo
    audio_file = None
    if 'file' in request.files:
        audio_file = request.files['file']
    else:
        if request.files:
            first_key = next(iter(request.files))
            audio_file = request.files[first_key]

    if not audio_file:
        raw = request.get_data()
        if not raw or len(raw) == 0:
            return jsonify({'error': 'No se recibió audio'}), 400
            
        filename = f"{uuid.uuid4()}.wav"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        try:
            with open(filepath, 'wb') as f:
                f.write(raw)
        except Exception as e:
            return jsonify({'error': 'Error al guardar audio', 'detail': str(e)}), 400
    else:
        filename = f"{uuid.uuid4()}_{audio_file.filename}"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        audio_file.save(filepath)

    # Determinar idioma
    lang_param = request.form.get('lang', '')
    if lang_param in ('qu', 'qu-EC'):
        language_code = 'qu-EC'
    elif lang_param in ('es', 'es-ES', 'es-EC'):
        language_code = 'es-EC'
    elif lang_param:
        language_code = lang_param
    else:
        language_code = None  # autodetección: probar qu-EC y es-EC

    # Procesar audio
    recognizer = sr.Recognizer()
    temp_converted = None
    try:
        # Ruta remota primero (evita depender de ffmpeg). Si hay API key, enviamos el archivo tal cual.
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            provider = (os.getenv('TRANSCRIBE_PROVIDER') or 'openai').lower()
        except Exception:
            api_key = None
            provider = 'openai'

        if api_key and provider == 'openai':
            try:
                headers = {'Authorization': f'Bearer {api_key}'}
                with open(filepath, 'rb') as f_audio:
                    files = {'file': (os.path.basename(filepath), f_audio)}
                    data = {'model': 'whisper-1'}
                    if language_code:
                        try:
                            data['language'] = language_code.split('-')[0]
                        except Exception:
                            pass
                    resp_api = requests.post('https://api.openai.com/v1/audio/transcriptions', headers=headers, files=files, data=data, timeout=120)

                if resp_api.ok:
                    try:
                        resp_json = resp_api.json()
                        text = resp_json.get('text', '')
                        return jsonify({'text': text})
                    except Exception as parse_e:
                        # continuar con flujo local si falla el parseo
                        pass
                else:
                    # Si la API remota falla, continuar con flujo local
                    pass
            except Exception:
                # Continuar con flujo local
                pass

        # Intento directo
        try:
            with sr.AudioFile(filepath) as source:
                audio_data = recognizer.record(source)
        except Exception as read_err:
            # Intentar conversión con pydub
            try:
                from pydub import AudioSegment
                temp_converted = f"{filepath}.converted.wav"
                audio_seg = AudioSegment.from_file(filepath)
                audio_seg = audio_seg.set_frame_rate(16000).set_channels(1)
                audio_seg.export(temp_converted, format='wav')
                
                with sr.AudioFile(temp_converted) as source:
                    audio_data = recognizer.record(source)
            except Exception as conv_err:
                suggestion = None
                try:
                    if isinstance(conv_err, FileNotFoundError) or 'ffmpeg' in str(conv_err).lower():
                        suggestion = 'Configure la variable OPENAI_API_KEY para usar transcripción remota sin ffmpeg, o instale ffmpeg desde https://ffmpeg.org y agréguelo al PATH'
                except Exception:
                    pass
                # Intentar fallback usando una API de transcripción remota (p.ej. OpenAI Whisper)
                try:
                    api_key = os.getenv('OPENAI_API_KEY')
                    provider = os.getenv('TRANSCRIBE_PROVIDER', 'openai').lower()
                except Exception:
                    api_key = None
                    provider = 'openai'

                if api_key and provider == 'openai':
                    try:
                        # Llamada a la API de OpenAI para transcribir el archivo tal cual (acepta mp3, wav, etc.)
                        headers = {'Authorization': f'Bearer {api_key}'}
                        with open(filepath, 'rb') as f_audio:
                            files = {'file': (os.path.basename(filepath), f_audio)}
                            data = {'model': 'whisper-1'}
                            # pasar idioma solo si está definido; si no, permitir autodetección del proveedor
                            if language_code:
                                try:
                                    data['language'] = language_code.split('-')[0]
                                except Exception:
                                    pass
                            resp_api = requests.post('https://api.openai.com/v1/audio/transcriptions', headers=headers, files=files, data=data, timeout=120)

                        if resp_api.ok:
                            try:
                                resp_json = resp_api.json()
                                text = resp_json.get('text', '')
                                return jsonify({'text': text})
                            except Exception as parse_e:
                                # si la respuesta no tiene texto, continuar para devolver el error original
                                conv_err = f"API response parse error: {parse_e}; raw: {resp_api.text}"
                        else:
                            conv_err = f"Transcription API error: {resp_api.status_code} {resp_api.text}"
                    except Exception as api_e:
                        conv_err = f"Transcription API exception: {api_e}"

                return jsonify({
                    'error': 'Error al procesar audio',
                    'detail': str(read_err),
                    'conversion_error': str(conv_err),
                    'suggestion': suggestion
                }), 400

        # Reconocer texto (autodetección si no se definió language_code)
        try:
            if language_code:
                text = recognizer.recognize_google(audio_data, language=language_code)
            else:
                text_qu = ''
                text_es = ''
                try:
                    text_qu = recognizer.recognize_google(audio_data, language='qu-EC')
                except Exception:
                    text_qu = ''
                try:
                    text_es = recognizer.recognize_google(audio_data, language='es-EC')
                except Exception:
                    text_es = ''
                text = text_qu if len(text_qu) >= len(text_es) else text_es
        except sr.UnknownValueError:
            text = ""
        except sr.RequestError as e:
            return jsonify({'error': 'Error en reconocimiento de voz', 'detail': str(e)}), 500

    finally:
        # Limpiar archivos temporales
        try:
            if temp_converted and os.path.exists(temp_converted):
                os.remove(temp_converted)
        except Exception:
            pass
        # Eliminar el archivo original subido/guardado para no acumular
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

    return jsonify({'text': text})

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text = data.get('text', '')
    src = data.get('src', 'auto')
    dest = data.get('dest', 'es')
    
    if not text:
        return jsonify({'translation': ''})

    try:
        # Detección de idioma cuando src es auto
        if src == 'auto':
            detected, score_qu, score_es = detect_lang_with_score(text)
            src = detected
            if dest == 'es' and detected == 'es':
                dest = 'qu'
            elif dest.startswith('qu') and detected.startswith('qu'):
                dest = 'es'

        # Cargar diccionario local
        dic = load_dictionary()

        # Normalizar entrada para mejorar coincidencias
        txt = text.strip()

        # Español -> Kichwa (dic keys en español)
        if dest.startswith('qu') and (src.startswith('es') or src == 'auto'):
            if dic:
                # Reemplazo por frases largas y normalizadas
                out = best_kichwa_match(dic, txt)
                if normalize_kichwa_token(out) != normalize_kichwa_token(txt):
                    return jsonify({'translation': out})

        # Kichwa -> Español: invertimos el dic y utilizamos tokenización/normalización
        if dest.startswith('es') and (src.startswith('qu') or src == 'auto'):
            if dic:
                inv = {normalize_kichwa_token(v): k for k, v in dic.items() if isinstance(v, str)}
                tokens = tokenize_kichwa(txt)
                # sustitución token a token si hay coincidencias exactas normalizadas
                replaced = []
                for tok in tokens:
                    repl = inv.get(tok)
                    replaced.append(repl if repl else tok)
                out = ' '.join(replaced)
                if normalize_kichwa_token(out) != normalize_kichwa_token(txt):
                    return jsonify({'translation': out})

        # Fallback a Google Translate
        try:
            # Mapear códigos de idioma para deep-translator
            lang_map = {
                'es': 'es',
                'qu': 'qu',  # deep-translator soporta quechua
                'qu-EC': 'qu',
                'es-EC': 'es',
                'es-ES': 'es'
            }
            
            src_lang = lang_map.get(src, 'auto')
            dest_lang = lang_map.get(dest, 'es')
            
            if src_lang == 'auto':
                # Para autodetección, usar el idioma detectado
                src_lang = detected if 'detected' in locals() else 'es'
            
            translation = translator.translate(text, source=src_lang, target=dest_lang)
            resp = {'translation': translation}
        except Exception as translate_error:
            # Si falla la traducción, devolver texto original
            resp = {'translation': text, 'translate_error': str(translate_error)}
        try:
            if 'detected' in locals():
                resp['detected_lang'] = detected
                resp['scores'] = {'qu': score_qu, 'es': score_es}
        except Exception:
            pass
        return jsonify(resp)
    except Exception as e:
        return jsonify({'translation': '', 'error': str(e)})

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get('text', '')
    lang = data.get('lang', 'es')

    if not text:
        return jsonify({'audio_url': ''})

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_FOLDER, filename)
    
    try:
        # Normalizar código de idioma y fallback para kichwa/quechua
        lang_code = (lang or 'es').lower()
        try:
            # gTTS espera códigos simples como 'es', 'en' (no 'es-EC')
            if '-' in lang_code:
                lang_code = lang_code.split('-')[0]
            # gTTS no soporta qu/qu-EC; usar voz española como aproximación
            if lang_code in ('qu', 'que', 'quz', 'quy', 'quh'):
                lang_code = 'es'
        except Exception:
            lang_code = 'es'

        try:
            tts = gTTS(text=text, lang=lang_code)
        except Exception as e:
            # Si falla por idioma no soportado, reintentar en español
            try:
                tts = gTTS(text=text, lang='es')
            except Exception:
                raise e
        tts.save(filepath)
        return jsonify({'audio_url': f'/static/audio/{filename}', 'used_lang': lang_code})
    except Exception as e:
        return jsonify({'audio_url': '', 'error': str(e)})

# Endpoints del diccionario
@app.route('/api/dictionary', methods=['GET'])
def api_dictionary():
    dict_path = os.path.join('data', 'dictionary_es_qu.json')
    if os.path.exists(dict_path):
        with open(dict_path, 'r', encoding='utf-8') as f:
            dic = json.load(f)
    else:
        dic = {}
    return jsonify({'dictionary': dic})

@app.route('/api/dictionary/add', methods=['POST'])
def api_dictionary_add():
    try:
        data = request.get_json()
        spanish = (data.get('spanish') or '').strip().lower()
        kichwa = (data.get('kichwa') or '').strip()

        if not spanish or not kichwa:
            return jsonify({'error': 'Faltan datos'}), 400

        with DICT_LOCK:
            dic = load_dictionary()
            before = dic.get(spanish)
            dic[spanish] = kichwa
            save_dictionary(dic, reason='add', info={'spanish': spanish})
            append_history(
                action='add' if before is None else 'overwrite',
                spanish_before=spanish if before is not None else None,
                spanish_after=spanish,
                kichwa_before=before,
                kichwa_after=kichwa,
            )
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dictionary/update', methods=['POST'])
def api_dictionary_update():
    try:
        data = request.get_json()
        spanish = (data.get('spanish') or '').strip().lower()
        kichwa = (data.get('kichwa') or '').strip()
        spanish_new = (data.get('spanish_new') or '').strip().lower()

        if not spanish or not kichwa:
            return jsonify({'error': 'Faltan datos'}), 400

        with DICT_LOCK:
            dic = load_dictionary()
            if spanish not in dic:
                return jsonify({'error': 'Palabra no encontrada'}), 404

            before_kichwa = dic.get(spanish)
            dic[spanish] = kichwa

            renamed = False
            if spanish_new and spanish_new != spanish:
                dic[spanish_new] = dic.pop(spanish)
                renamed = True
                spanish_after = spanish_new
            else:
                spanish_after = spanish

            save_dictionary(dic, reason='update', info={'spanish': spanish, 'spanish_new': spanish_new or None})
            append_history(
                action='rename' if renamed else 'update',
                spanish_before=spanish,
                spanish_after=spanish_after,
                kichwa_before=before_kichwa,
                kichwa_after=dic[spanish_after]
            )

        return jsonify({'ok': True, 'spanish': spanish_after, 'kichwa': dic[spanish_after]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dictionary/delete', methods=['POST'])
def api_dictionary_delete():
    try:
        data = request.get_json()
        spanish = (data.get('spanish') or '').strip().lower()

        if not spanish:
            return jsonify({'error': 'Palabra no especificada'}), 400

        with DICT_LOCK:
            dic = load_dictionary()
            if spanish in dic:
                before_kichwa = dic.get(spanish)
                del dic[spanish]
                save_dictionary(dic, reason='delete', info={'spanish': spanish})
                append_history(
                    action='delete',
                    spanish_before=spanish,
                    spanish_after=None,
                    kichwa_before=before_kichwa,
                    kichwa_after=None
                )
                return jsonify({'ok': True})
            else:
                return jsonify({'error': 'Palabra no encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dictionary/import', methods=['POST'])
def api_dictionary_import():
    if 'file' not in request.files:
        return jsonify({'error': 'file required'}), 400

    f = request.files['file']
    # Leer bytes una sola vez y decodificar con fallback
    try:
        raw = f.read()
    except Exception as e:
        return jsonify({'error': f'No se pudo leer el archivo: {e}'}), 400
    try:
        content = raw.decode('utf-8')
    except Exception:
        try:
            content = raw.decode('latin-1')
        except Exception as e:
            return jsonify({'error': f'No se pudo decodificar el archivo: {e}'}), 400
    # Remover BOM si existe
    if content and content[0] == '\ufeff':
        content = content.lstrip('\ufeff')

    import csv, io

    stats = {
        'added': 0,
        'updated': 0,
        'skipped_invalid': 0,
        'skipped_duplicates': 0,
        'total_rows': 0
    }

    with DICT_LOCK:
        current = load_dictionary()

        seen_in_file = set()
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            stats['total_rows'] += 1
            if not row or len(row) < 2:
                stats['skipped_invalid'] += 1
                continue
            es = (row[0] or '').strip().lower()
            qu = (row[1] or '').strip()
            if not es or not qu:
                stats['skipped_invalid'] += 1
                continue
            # duplicados dentro del mismo archivo
            key_pair = (es, qu)
            if key_pair in seen_in_file:
                stats['skipped_duplicates'] += 1
                continue
            seen_in_file.add(key_pair)

            if es in current:
                if current[es] == qu:
                    stats['skipped_duplicates'] += 1
                else:
                    # actualizar valor existente
                    before = current[es]
                    current[es] = qu
                    stats['updated'] += 1
                    append_history(
                        action='bulk-update',
                        spanish_before=es,
                        spanish_after=es,
                        kichwa_before=before,
                        kichwa_after=qu,
                        info={'source': 'import-csv'}
                    )
            else:
                current[es] = qu
                stats['added'] += 1
                append_history(
                    action='bulk-add',
                    spanish_before=None,
                    spanish_after=es,
                    kichwa_before=None,
                    kichwa_after=qu,
                    info={'source': 'import-csv'}
                )

        save_dictionary(current, reason='import-csv', info={'stats': stats})

    return jsonify({'ok': True, **stats})

@app.route('/api/dictionary/export', methods=['GET'])
def api_dictionary_export():
    fmt = (request.args.get('format') or 'json').lower()
    dict_path = os.path.join('data', 'dictionary_es_qu.json')

    if os.path.exists(dict_path):
        with open(dict_path, 'r', encoding='utf-8') as f:
            dic = json.load(f)
    else:
        dic = {}

    if fmt == 'csv':
        # Construir CSV simple "es,kichwa"
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        for es, qu in sorted(dic.items(), key=lambda x: x[0]):
            writer.writerow([es, qu])
        csv_data = output.getvalue()
        from flask import Response
        return Response(csv_data, mimetype='text/csv', headers={
            'Content-Disposition': 'attachment; filename=dictionary_es_qu.csv'
        })

    # Por defecto JSON
    return jsonify({'dictionary': dic})

# -------------------- Estudio: Flashcards y Quizzes --------------------
@app.route('/api/study/flashcards', methods=['GET'])
def api_study_flashcards():
    """Devuelve una lista de tarjetas de estudio basadas en el diccionario.

    Parámetros:
      - dir: 'es2qu' (por defecto) o 'qu2es'
      - limit: cantidad de tarjetas (por defecto 20)
    """
    direction = (request.args.get('dir') or 'es2qu').lower()
    try:
        limit = int(request.args.get('limit', '20'))
    except Exception:
        limit = 20

    dic = load_dictionary()
    if not dic:
        return jsonify({'flashcards': []})

    items = list(dic.items())  # [(es, qu)]
    random.shuffle(items)
    selected = items[: max(0, limit)]

    flashcards = []
    for es, qu in selected:
        if not isinstance(qu, str):
            continue
        if direction == 'qu2es':
            flashcards.append({'front': qu, 'back': es, 'dir': 'qu2es'})
        else:
            flashcards.append({'front': es, 'back': qu, 'dir': 'es2qu'})

    return jsonify({'flashcards': flashcards})

@app.route('/api/study/quiz', methods=['GET'])
def api_study_quiz():
    """Genera preguntas de opción múltiple usando el diccionario.

    Parámetros:
      - dir: 'es2qu' (por defecto) o 'qu2es'
      - limit: número de preguntas (por defecto 10)
      - options: número de opciones por pregunta (por defecto 4)
    """
    direction = (request.args.get('dir') or 'es2qu').lower()
    try:
        limit = int(request.args.get('limit', '10'))
    except Exception:
        limit = 10
    try:
        num_options = max(2, int(request.args.get('options', '4')))
    except Exception:
        num_options = 4

    dic = load_dictionary()
    if not dic:
        return jsonify({'questions': []})

    pairs = [(es, qu) for es, qu in dic.items() if isinstance(qu, str)]
    if not pairs:
        return jsonify({'questions': []})

    random.shuffle(pairs)
    base = pairs[: max(0, limit)]

    questions = []
    for es, qu in base:
        if direction == 'qu2es':
            prompt = qu
            correct = es
            pool = [p[0] for p in pairs if p[1] != qu]
        else:
            prompt = es
            correct = qu
            pool = [p[1] for p in pairs if p[0] != es]

        # construir opciones
        distractors = random.sample(pool, k=min(len(pool), num_options - 1)) if pool else []
        options = distractors + [correct]
        random.shuffle(options)
        questions.append({
            'prompt': prompt,
            'options': options,
            'answer': correct,
            'dir': direction
        })

    return jsonify({'questions': questions})

# Metadatos, historial, backups y restauración
@app.route('/api/dictionary/meta', methods=['GET'])
def api_dictionary_meta():
    meta = ensure_meta_initialized()
    try:
        backups = []
        for name in sorted(os.listdir(BACKUP_DIR)):
            if not name.endswith('.json'): continue
            path = os.path.join(BACKUP_DIR, name)
            try:
                stat = os.stat(path)
                backups.append({'file': name, 'bytes': stat.st_size})
            except Exception:
                backups.append({'file': name})
    except Exception:
        backups = []
    return jsonify({'meta': meta, 'backups': backups})

@app.route('/api/dictionary/history', methods=['GET'])
def api_dictionary_history():
    limit = request.args.get('limit', default='200')
    try:
        limit = int(limit)
    except Exception:
        limit = 200
    history = _safe_read_json(HISTORY_PATH, [])
    return jsonify({'history': history[-limit:]})

@app.route('/api/dictionary/backups', methods=['GET'])
def api_dictionary_backups():
    files = []
    try:
        for name in sorted(os.listdir(BACKUP_DIR)):
            if not name.endswith('.json'): continue
            path = os.path.join(BACKUP_DIR, name)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                meta = data.get('metadata', {})
            except Exception:
                meta = {}
            files.append({'file': name, 'metadata': meta})
    except Exception as e:
        return jsonify({'error': str(e), 'files': files}), 500
    return jsonify({'files': files})

@app.route('/api/dictionary/restore', methods=['POST'])
def api_dictionary_restore():
    body = request.get_json() or {}
    filename = (body.get('file') or '').strip()
    if not filename:
        return jsonify({'error': 'file requerido'}), 400
    target = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(target):
        return jsonify({'error': 'Backup no encontrado'}), 404
    try:
        with open(target, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        new_dic = payload.get('dictionary') or {}
        if not isinstance(new_dic, dict):
            return jsonify({'error': 'Backup inválido'}), 400
        save_dictionary(new_dic, reason='restore', info={'file': filename})
        append_history(action='restore', info={'file': filename})
        return jsonify({'ok': True, 'restored_from': filename, 'entries': len(new_dic)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe():
    return speech_to_text()

@app.route('/api/ffmpeg', methods=['GET'])
def api_ffmpeg():
    """Verifica si ffmpeg está disponible en el sistema y su versión."""
    try:
        import subprocess
        completed = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        ok = completed.returncode == 0
        version = None
        if ok:
            first_line = (completed.stdout or '').splitlines()[0] if completed.stdout else ''
            version = first_line
        return jsonify({'available': ok, 'version': version}), (200 if ok else 404)
    except FileNotFoundError:
        return jsonify({'available': False, 'error': 'ffmpeg no encontrado'}), 404
    except Exception as e:
        return jsonify({'available': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)