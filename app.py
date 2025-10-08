from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import requests
import uuid
import json
import shutil
from datetime import datetime
import threading

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

# Lock simple para operaciones en el diccionario
DICT_LOCK = threading.Lock()

def _now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

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
except Exception:
    pass

# Inicializar traductor
translator = Translator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/diccionario')
def diccionario_page():
    return render_template('diccionario.html')

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
        language_code = 'qu-EC'

    # Procesar audio
    recognizer = sr.Recognizer()
    temp_converted = None
    try:
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
                        suggestion = 'Instale ffmpeg desde https://ffmpeg.org y asegúrese de que esté en el PATH del sistema'
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
                            # pasar idioma si es disponible (solo la parte primaria e.g. 'es' o 'qu')
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

        # Reconocer texto
        try:
            text = recognizer.recognize_google(audio_data, language=language_code)
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
        # Cargar diccionario local para kichwa
        if dest.startswith('qu') and (src.startswith('es') or src == 'auto'):
            dict_path = os.path.join('data', 'dictionary_es_qu.json')
            if os.path.exists(dict_path):
                with open(dict_path, 'r', encoding='utf-8') as f:
                    dic = json.load(f)

                txt = text.strip().lower()
                keys = sorted(dic.keys(), key=lambda k: -len(k))
                out = txt
                
                for k in keys:
                    if k in out:
                        out = out.replace(k, dic[k])

                if out != txt:
                    return jsonify({'translation': out})

        # Fallback a Google Translate
        translation = translator.translate(text, src=src, dest=dest)
        return jsonify({'translation': translation.text})
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
        tts = gTTS(text=text, lang=lang)
        tts.save(filepath)
        return jsonify({'audio_url': f'/static/audio/{filename}'})
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
    try:
        content = f.read().decode('utf-8')
    except Exception:
        # intentar latin-1 si utf-8 falla
        try:
            content = f.read().decode('latin-1')
        except Exception as e:
            return jsonify({'error': f'No se pudo leer el archivo: {e}'}), 400

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