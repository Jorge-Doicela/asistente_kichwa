from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import requests
import uuid
import json

app = Flask(__name__)
CORS(app)

# Configuración de carpetas
AUDIO_FOLDER = os.path.join('static', 'audio')
DATA_FOLDER = os.path.join('data')
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

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
        spanish = data.get('spanish', '').strip().lower()
        kichwa = data.get('kichwa', '').strip()
        
        if not spanish or not kichwa:
            return jsonify({'error': 'Faltan datos'}), 400
            
        dict_path = os.path.join('data', 'dictionary_es_qu.json')
        dic = {}
        if os.path.exists(dict_path):
            with open(dict_path, 'r', encoding='utf-8') as f:
                dic = json.load(f)
                
        dic[spanish] = kichwa
        
        with open(dict_path, 'w', encoding='utf-8') as f:
            json.dump(dic, f, ensure_ascii=False, indent=2)
            
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dictionary/update', methods=['POST'])
def api_dictionary_update():
    try:
        data = request.get_json()
        spanish = data.get('spanish', '').strip().lower()
        kichwa = data.get('kichwa', '').strip()
        spanish_new = (data.get('spanish_new') or '').strip().lower()

        if not spanish or not kichwa:
            return jsonify({'error': 'Faltan datos'}), 400

        dict_path = os.path.join('data', 'dictionary_es_qu.json')
        if not os.path.exists(dict_path):
            return jsonify({'error': 'Diccionario no encontrado'}), 404

        with open(dict_path, 'r', encoding='utf-8') as f:
            dic = json.load(f)

        if spanish not in dic:
            return jsonify({'error': 'Palabra no encontrada'}), 404

        # Actualizar valor
        dic[spanish] = kichwa

        # Renombrar clave si se envía spanish_new
        if spanish_new and spanish_new != spanish:
            dic[spanish_new] = dic.pop(spanish)
            spanish = spanish_new

        with open(dict_path, 'w', encoding='utf-8') as f:
            json.dump(dic, f, ensure_ascii=False, indent=2)

        return jsonify({'ok': True, 'spanish': spanish, 'kichwa': dic[spanish]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dictionary/delete', methods=['POST'])
def api_dictionary_delete():
    try:
        data = request.get_json()
        spanish = data.get('spanish', '').strip().lower()
        
        if not spanish:
            return jsonify({'error': 'Palabra no especificada'}), 400
            
        dict_path = os.path.join('data', 'dictionary_es_qu.json')
        if not os.path.exists(dict_path):
            return jsonify({'error': 'Diccionario no encontrado'}), 404
            
        with open(dict_path, 'r', encoding='utf-8') as f:
            dic = json.load(f)
            
        if spanish in dic:
            del dic[spanish]
            with open(dict_path, 'w', encoding='utf-8') as f:
                json.dump(dic, f, ensure_ascii=False, indent=2)
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
    content = f.read().decode('utf-8')
    
    dict_path = os.path.join('data', 'dictionary_es_qu.json')
    import csv, io
    
    dic = {}
    if os.path.exists(dict_path):
        with open(dict_path, 'r', encoding='utf-8') as fh:
            try:
                dic = json.load(fh)
            except Exception:
                dic = {}

    reader = csv.reader(io.StringIO(content))
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