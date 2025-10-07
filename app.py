from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import uuid

app = Flask(__name__)
CORS(app)

AUDIO_FOLDER = os.path.join('static', 'audio')
os.makedirs(AUDIO_FOLDER, exist_ok=True)
DATA_FOLDER = os.path.join('data')
os.makedirs(DATA_FOLDER, exist_ok=True)
UPLOADS_JSON = os.path.join(DATA_FOLDER, 'uploads.json')

# Cargar/guardar metadatos de uploads
def load_uploads():
    try:
        import json
        if os.path.exists(UPLOADS_JSON):
            with open(UPLOADS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_uploads(uploads):
    try:
        import json
        with open(UPLOADS_JSON, 'w', encoding='utf-8') as f:
            json.dump(uploads, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

translator = Translator()

@app.route('/')
def index():
    return render_template('index.html')

# -----------------------------------
# 1️⃣ Endpoint Speech-to-Text
# -----------------------------------
@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    # Verificar archivo: intentar varios enfoques para mayor robustez
    audio_file = None
    # 1) Campo 'file' en form-data
    if 'file' in request.files:
        audio_file = request.files['file']
    else:
        # 2) Si cualquier otra clave en request.files, tomar la primera
        if request.files:
            first_key = next(iter(request.files))
            audio_file = request.files[first_key]

    filepath = None
    if audio_file:
        # Guardar con extensión original para intentar procesarlo
        filename = f"{uuid.uuid4()}_{audio_file.filename}"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        audio_file.save(filepath)
    else:
        # 3) Si no hay archivos pero sí datos binarios en el body, guardarlos
        raw = request.get_data()
        if raw and len(raw) > 0:
            filename = f"{uuid.uuid4()}.wav"
            filepath = os.path.join(AUDIO_FOLDER, filename)
            try:
                with open(filepath, 'wb') as f:
                    f.write(raw)
            except Exception as e:
                return jsonify({'error': 'No se pudo guardar el audio recibido', 'detail': str(e)}), 400
        else:
            return jsonify({'error': 'No se recibi\u00f3 audio en request.files ni en el body'}), 400

    # Determinar idioma si fue enviado desde el frontend (ej. 'qu' o 'es' o códigos completos)
    lang_param = request.form.get('lang', '')
    if lang_param in ('qu', 'qu-EC'):
        language_code = 'qu-EC'
    elif lang_param in ('es', 'es-ES', 'es-EC'):
        # usar es-EC por consistencia si se pide 'es'
        language_code = 'es-EC'
    elif lang_param:
        language_code = lang_param
    else:
        # por defecto intentar kichwa
        language_code = 'qu-EC'

    recognizer = sr.Recognizer()
    temp_converted = None
    try:
        # Intento directo primero
        try:
            with sr.AudioFile(filepath) as source:
                audio_data = recognizer.record(source)
        except Exception as read_err:
            # Intentar conversi\u00f3n con pydub (ffmpeg/avlib) a WAV PCM si est\u00e1 disponible
            try:
                from pydub import AudioSegment
                temp_converted = f"{filepath}.converted.wav"
                # pydub detecta formato desde la extensi\u00f3n o desde el contenido
                audio_seg = AudioSegment.from_file(filepath)
                # Convertir a mono 16kHz WAV (opcional, 16000 puede mejorar reconocimiento)
                audio_seg = audio_seg.set_frame_rate(16000).set_channels(1)
                audio_seg.export(temp_converted, format='wav')
                with sr.AudioFile(temp_converted) as source:
                    audio_data = recognizer.record(source)
            except Exception as conv_err:
                # Detectar si fall\u00f3 por falta de ffmpeg (pydub lo necesita)
                suggestion = None
                try:
                    if isinstance(conv_err, FileNotFoundError):
                        suggestion = 'ffmpeg no encontrado: instala ffmpeg y agr\u00e9galo al PATH (https://ffmpeg.org)'
                    else:
                        msg = str(conv_err).lower()
                        if 'ffmpeg' in msg or 'avconv' in msg or 'no such file' in msg:
                            suggestion = 'ffmpeg no encontrado: instala ffmpeg y agr\u00e9galo al PATH (https://ffmpeg.org)'
                except Exception:
                    suggestion = None

                resp = {'error': 'No se pudo procesar el archivo de audio', 'detail': str(read_err), 'conversion_error': str(conv_err), 'filepath': filepath}
                if suggestion:
                    resp['suggestion'] = suggestion
                return jsonify(resp), 400

        # Reconocer texto
        try:
            text = recognizer.recognize_google(audio_data, language=language_code)
        except sr.UnknownValueError:
            text = ""
        except sr.RequestError as e:
            return jsonify({'error': 'Error en el reconocimiento de voz', 'detail': str(e)}), 500
    finally:
        # Limpiar archivos temporales si existen
        try:
            if temp_converted and os.path.exists(temp_converted):
                os.remove(temp_converted)
        except Exception:
            pass

    # Limpiar archivo temporal
    try:
        os.remove(filepath)
    except Exception:
        pass

    return jsonify({'text': text})

# -----------------------------------
# 2️⃣ Endpoint Traducción
# -----------------------------------
@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text = data.get('text', '')
    src = data.get('src', 'auto')  # idioma origen
    dest = data.get('dest', 'es')  # idioma destino
    if not text:
        return jsonify({'translation': ''})

    # Si la traducción es de Español a Kichwa, usar un diccionario local para mejorar la calidad.
    try:
        if dest.startswith('qu') and (src.startswith('es') or src == 'auto'):
            # Cargar diccionario local
            import json
            dict_path = os.path.join('data', 'dictionary_es_qu.json')
            if os.path.exists(dict_path):
                with open(dict_path, 'r', encoding='utf-8') as f:
                    dic = json.load(f)

                # Normalizar texto para buscar coincidencias
                txt = text.strip().lower()

                # Reemplazar frases más largas primero
                keys = sorted(dic.keys(), key=lambda k: -len(k))
                out = txt
                for k in keys:
                    if k in out:
                        out = out.replace(k, dic[k])

                # Si después del reemplazo sigue habiendo texto en español (pocas coincidencias), intentar fallback a translator
                if out.strip() and any(c.isalpha() for c in out) and out != txt:
                    return jsonify({'translation': out})
                else:
                    # Fallback: usar googletrans para intentar traducción automática general, luego dejar que el diccionario corrija coincidencias parciales
                    translation = translator.translate(text, src=src, dest=dest)
                    # intentar mapear palabras sueltas con el diccionario
                    translated = translation.text
                    lower = translated.lower()
                    for k in keys:
                        if k in lower:
                            translated = translated.replace(k, dic.get(k, k))
                    return jsonify({'translation': translated})

        # Default: usar googletrans
        translation = translator.translate(text, src=src, dest=dest)
        return jsonify({'translation': translation.text})
    except Exception as e:
        return jsonify({'translation': '', 'error': str(e)})


# -----------------------------------
# Endpoint para subir un archivo de audio y devolver URL + transcripción
# -----------------------------------
@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    # Esperamos form-data con 'file' (uno o varios) y opcional 'lang'
    if not request.files:
        return jsonify({'error': 'No se recibi\u00f3 archivo'}), 400

    files = request.files.getlist('file') or []
    # Si no viene con la clave 'file', tomar todos los archivos enviados
    if not files:
        files = list(request.files.values())

    lang_param = request.form.get('lang', '')
    if lang_param in ('qu', 'qu-EC'):
        language_code = 'qu-EC'
    elif lang_param in ('es', 'es-ES', 'es-EC'):
        language_code = 'es-EC'
    elif lang_param:
        language_code = lang_param
    else:
        language_code = 'qu-EC'

    results = []
    uploads = load_uploads()
    for audio_file in files:
        original_name = getattr(audio_file, 'filename', 'uploaded')
        filename = f"{uuid.uuid4()}_{original_name}"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        audio_file.save(filepath)

        recognizer = sr.Recognizer()
        temp_converted = None
        text = ''
        try:
            try:
                with sr.AudioFile(filepath) as source:
                    audio_data = recognizer.record(source)
            except Exception as read_err:
                try:
                    from pydub import AudioSegment
                    temp_converted = f"{filepath}.converted.wav"
                    audio_seg = AudioSegment.from_file(filepath)
                    audio_seg = audio_seg.set_frame_rate(16000).set_channels(1)
                    audio_seg.export(temp_converted, format='wav')
                    with sr.AudioFile(temp_converted) as source:
                        audio_data = recognizer.record(source)
                except Exception as conv_err:
                    results.append({'audio_url': f'/static/audio/{filename}', 'text': '', 'error': 'No se pudo procesar el archivo', 'detail': str(conv_err)})
                    continue

            try:
                text = recognizer.recognize_google(audio_data, language=language_code)
            except sr.UnknownValueError:
                text = ''
            except sr.RequestError as e:
                results.append({'audio_url': f'/static/audio/{filename}', 'text': '', 'error': 'Error en el reconocimiento de voz', 'detail': str(e)})
                continue
        finally:
            try:
                if temp_converted and os.path.exists(temp_converted):
                    os.remove(temp_converted)
            except Exception:
                pass

        # Guardar metadatos
        import datetime
        meta = {
            'filename': filename,
            'original_name': original_name,
            'text': text,
            'uploaded_at': datetime.datetime.utcnow().isoformat() + 'Z'
        }
        uploads.append(meta)
        save_uploads(uploads)

        results.append({'audio_url': f'/static/audio/{filename}', 'text': text})

    return jsonify({'results': results})


@app.route('/api/uploads', methods=['GET'])
def api_uploads():
    uploads = load_uploads()
    return jsonify({'uploads': uploads})


@app.route('/api/upload/<filename>', methods=['DELETE'])
def api_delete_upload(filename):
    uploads = load_uploads()
    new_uploads = [u for u in uploads if u.get('filename') != filename]
    if len(new_uploads) == len(uploads):
        return jsonify({'error': 'No encontrado'}), 404
    # borrar fichero
    filepath = os.path.join(AUDIO_FOLDER, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
    save_uploads(new_uploads)
    return jsonify({'ok': True})


@app.route('/admin')
def admin_page():
    return render_template('admin.html')





@app.route('/api/dictionary', methods=['GET'])
def api_dictionary():
    dict_path = os.path.join('data', 'dictionary_es_qu.json')
    import json
    if os.path.exists(dict_path):
        with open(dict_path, 'r', encoding='utf-8') as f:
            dic = json.load(f)
    else:
        dic = {}
    return jsonify({'dictionary': dic})


@app.route('/api/dictionary/import', methods=['POST'])
def api_dictionary_import():
    # Espera form-data con 'file' CSV (es,qu)
    if 'file' not in request.files:
        return jsonify({'error': 'file required'}), 400
    f = request.files['file']
    content = f.read().decode('utf-8')
    import csv, io, json
    reader = csv.reader(io.StringIO(content))
    dict_path = os.path.join('data', 'dictionary_es_qu.json')
    dic = {}
    if os.path.exists(dict_path):
        with open(dict_path, 'r', encoding='utf-8') as fh:
            try:
                dic = json.load(fh)
            except Exception:
                dic = {}

    added = 0
    for row in reader:
        if not row: continue
        es = row[0].strip().lower()
        qu = row[1].strip() if len(row) > 1 else ''
        if es and qu:
            dic[es] = qu
            added += 1

    with open(dict_path, 'w', encoding='utf-8') as fh:
        json.dump(dic, fh, ensure_ascii=False, indent=2)

    return jsonify({'ok': True, 'added': added})

# -----------------------------------
# 3️⃣ Endpoint Text-to-Speech
# -----------------------------------
@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get('text', '')
    lang = data.get('lang', 'es')  # idioma para TTS

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

if __name__ == '__main__':
    app.run(debug=True)
