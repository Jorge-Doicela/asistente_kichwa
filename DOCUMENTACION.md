# Objetivo principal
- Crear una aplicación web educativa para traducir y aprender Kichwa ↔ Español con voz, diccionario editable y herramientas de estudio. Referencias principales: README.md, app.py.

# Alcance funcional
- Traducción y detección de idioma (heurística + fallback): funciones en app.py (`detect_lang_text`, `detect_lang_with_score`). UI en index.html.
- Entrada por voz y transcripción: endpoint en app.py y uso de audio en main.js.
- Texto a voz (TTS): endpoint en app.py, archivos en audio.
- Diccionario local editable: obtener/añadir/actualizar/eliminar, importación/exportación CSV/JSON. Endpoints en app.py (`api_dictionary*`). Datos en dictionary_es_qu.json, plantilla base_dictionary.csv.
- Historial, meta y backups: gestión de cambios y restauración con funciones en app.py (`append_history`, `backup_dictionary`, `save_dictionary`). Archivos: history.json, meta.json, backups en backups.
- Módulo de estudio: flashcards y quizzes generados desde el diccionario. Endpoints en app.py (`api_study_flashcards`, `api_study_quiz`); vista estudiar.html.
- Interfaz del diccionario: búsqueda, paginación y ayudas en diccionario.html; estilos en style.css.

# Entregables esperados
- App ejecutable localmente con `python app.py` (instrucciones en README.md).
- Exportación CSV/JSON y backups automáticos en backups.
- Interfaz web con traducción, TTS, transcripción y módulo de estudio (archivos en templates y static).

# Limitaciones y supuestos
- Detección de idioma basada en heurística de tokens/caracteres (no ML robusto).
- Dependencias externas: `gtts`, `speech_recognition`, `googletrans` y posible `ffmpeg` (ver app.py y README.md).
- Importación CSV espera formato `español,kichwa` (sin encabezados); ejemplo en base_dictionary.csv.

# Métricas / criterios de éxito
- Diccionario persistente con backups e historial actualizados; meta.json refleja `entry_count` y `last_updated`.
- Endpoints clave disponibles: traducir, importar, exportar, flashcards, TTS.
- Interfaz usable en navegador moderno con reproducción TTS funcional.

# Resumen final
- Aplicación web para traducir, editar y estudiar Kichwa ↔ Español con soporte de voz, historial y backups; código central en app.py y documentación en README.md.

# Requisitos y entorno (hardware / software / variables de entorno)

## Hardware (mínimo recomendado)
- PC Windows 10/11.
- Micrófono y altavoces/auriculares para transcripción y TTS.
- CPU 2 núcleos, 4+ GB RAM (8 GB recomendado).
- SSD con espacio libre ≥ 200 MB + espacio para backups y audio.
- Conexión a Internet (para googletrans/gTTS y APIs externas).

## Software
- Python 3.10 o 3.11 (3.8+ suele funcionar).
- pip y virtualenv.
- Navegador moderno (Chrome, Edge, Firefox).
- ffmpeg instalado y en PATH (requerido por pydub/procesamiento de audio).
- Git (opcional).

## Dependencias Python principales
- Flask
- gTTS
- SpeechRecognition
- googletrans (ej. 4.0.0-rc1)
- pydub
- requests
- python-dotenv (opcional, para cargar .env)
- numpy (si se usa en procesamiento)
- cualquier otra dependencia listada en requirements.txt del proyecto

Ejemplo de requirements.txt (colocar en la raíz del proyecto):
````text
Flask>=2.0
gTTS>=2.2
SpeechRecognition>=3.8
googletrans==4.0.0-rc1
pydub>=0.25
python-dotenv>=0.21
requests>=2.28
````

## Variables de entorno recomendadas
- FLASK_APP=app.py
- FLASK_ENV=development (o production)
- SECRET_KEY=una_clave_secreta_para_sessiones
- DATA_DIR=data
- AUDIO_DIR=static\audio
- UPLOAD_FOLDER=static\uploads
- MAX_CONTENT_LENGTH=16777216  (16 MB)
- FFMPEG_PATH=C:\path\to\ffmpeg\bin\ffmpeg.exe (si no está en PATH)
- HOST=0.0.0.0
- PORT=5000
- TTS_PROVIDER=gtts

Ejemplo de `.env`:
````text
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=changeme123
DATA_DIR=data
AUDIO_DIR=static\audio
FFMPEG_PATH=
HOST=127.0.0.1
PORT=5000
````

## Comandos de instalación y ejecución (Windows)
````bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# opcional: exportar variables o usar .env
python app.py
# o con flask
set FLASK_APP=app.py
set FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
````

## Notas operativas
- Asegurar permisos del micrófono en Windows para el navegador y la aplicación si se usa captura en cliente.
- Confirmar que ffmpeg esté accesible si pydub u otros procesos de audio fallan.
- Realizar pruebas con un pequeño diccionario antes de importar masivo.
- Hacer backups periódicos de la carpeta data (automaticados por la app en data/backups).

# Instalación y puesta en marcha (pasos exactos, Windows)

1) Abrir PowerShell o CMD y situarse en la carpeta del proyecto:
```powershell
cd "C:\Users\Lab Escuela 6\Desktop\asistente_kichwa"
```

2) Crear y activar entorno virtual
- PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
# Si da error por ExecutionPolicy: Ejecutar como admin:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
- CMD:
```cmd
python -m venv venv
venv\Scripts\activate
```

3) Crear requirements.txt (si no existe) y luego instalar dependencias
````text
Flask>=2.0
gTTS>=2.2
SpeechRecognition>=3.8
googletrans==4.0.0-rc1
pydub>=0.25
python-dotenv>=0.21
requests>=2.28
````
Instalar:
```powershell
pip install -r requirements.txt
```

4) Instalar ffmpeg (si no está)
- Descargar build Windows desde https://www.gyan.dev/ffmpeg/builds/ o https://ffmpeg.org/download.html
- Extraer a C:\ffmpeg (estructura: C:\ffmpeg\bin\ffmpeg.exe)
- Añadir a PATH (PowerShell):
```powershell
setx PATH "$($env:Path);C:\ffmpeg\bin"
```
Cerrar y reabrir terminal después de setx.

5) Crear archivo .env con variables recomendadas (opcional)
````text
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=changeme123
DATA_DIR=data
AUDIO_DIR=static\audio
FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
HOST=127.0.0.1
PORT=5000
TTS_PROVIDER=gtts
````
(Si usas python-dotenv, la app cargará estas variables; si no, puedes exportarlas manualmente.)

6) Crear carpetas de datos si no existen
```powershell
mkdir data
mkdir data\backups
mkdir static\audio
mkdir static\uploads
```

7) Inicializar o verificar diccionario base
- Si hay data/base_dictionary.csv, puedes importar; si no, asegúrate de tener dictionary_es_qu.json o copiar plantilla.

8) Ejecutar la aplicación
- Opción directa:
```powershell
python app.py
```
- Opción Flask:
```powershell
set FLASK_APP=app.py
set FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```
Abrir en navegador: http://127.0.0.1:5000

9) Pruebas rápidas
- Probar endpoints: /api/translate, interfaz principal, módulo estudiar, import/export diccionario, TTS y grabación de voz en la UI.
- Ver logs en la terminal para errores; revisar meta.json y data/backups para confirmación de backups.

Notas rápidas
- Si el navegador no permite usar micrófono, verificar permisos de Windows y HTTPS (al hacer pruebas locales HTTP suele funcionar con permisos del navegador).
- Si pydub falla, confirmar ffmpeg accesible (ffmpeg -version en terminal).
- Para producción, usar un servidor WSGI (gunicorn/Waitress) y configurar FLASK_ENV=production.

# Uso (interfaz, flujos principales)

## Interfaz general
- Barra superior: búsqueda/traducción rápida, botón de grabar voz, selector de idioma (auto/dirección), botón de TTS.
- Panel principal: entrada de texto (izq), resultado de traducción (der), botones de copiar/compartir/escuchar.
- Menú lateral: Diccionario, Estudiar, Importar/Exportar, Historial / Backups, Ajustes.
- Páginas clave: / (inicio), /diccionario, /estudiar, /configuración.

## Flujo 1 — Traducción rápida (texto)
1. Escribir o pegar texto en el cuadro de entrada.
2. La app detecta idioma (heurística) o usar selector manual.
3. Hacer clic en "Traducir".
4. Ver resultado a la derecha; opciones:
   - Reproducir TTS (icono altavoz).
   - Copiar resultado.
   - Añadir pares nuevos al diccionario (botón “Guardar en diccionario”).

UX esperado: respuesta instantánea, indicador de idioma detectado y fuente (heurística / fallback).

## Flujo 2 — Entrada por voz y transcripción
1. Hacer clic en el botón "Grabar".
2. Conceder permiso de micrófono al navegador.
3. Grabar y parar; la transcripción aparece en el cuadro de entrada.
4. Traducir como en el Flujo 1 o editar texto manualmente.
5. Guardar la transcripción al diccionario si aplica.

Notas: la grabación usa API Web; la transcripción puede enviarse al endpoint /api/transcribe o procesarse en cliente.

## Flujo 3 — Texto a voz (TTS)
- Reproducir: usar el icono de altavoz junto a cualquier texto (entrada o traducción).
- Descargar audio: botón de descarga en la interfaz TTS.
- Configuración: elegir proveedor (gTTS) y velocidad/idioma en Ajustes.

API ejemplo (curl):
```bash
curl -X POST "http://127.0.0.1:5000/api/tts" -d "text=Hola&lang=es"
```

## Flujo 4 — Gestión del diccionario
- Buscar palabra/entrada en /diccionario.
- Añadir: formulario "Nueva entrada" con español y kichwa.
- Editar / Eliminar: botones por fila.
- Paginación y filtros (por idioma, por etimología si existe).
- Importar CSV: subir archivo (formato: español,kichwa).
- Exportar: botones CSV / JSON en la vista del diccionario.
- Guardado: cada cambio genera historial y backup automático.

API endpoints relevantes:
- GET /api/dictionary
- POST /api/dictionary/add
- PUT /api/dictionary/update/:id
- DELETE /api/dictionary/delete/:id
- POST /api/dictionary/import
- GET /api/dictionary/export?format=csv

## Flujo 5 — Módulo de estudio
- Flashcards:
  - Seleccionar dirección (ES→QU o QU→ES) y número de tarjetas.
  - Revisar tarjetas, marcar "conozco"/"no conozco".
- Quiz:
  - Preguntas de opción múltiple o rellenar espacios.
  - Calificación al final y opción de repetir fallos.
- Generación: usa entradas del diccionario y filtros (nivel, etiquetas).

API:
- GET /api/study/flashcards?count=20&dir=es_qu
- GET /api/study/quiz?count=10&dir=qu_es

## Flujo 6 — Historial y backups
- Cada guardado importante crea un backup en data/backups y una entrada en data/history.json.
- Vista Historial: lista de cambios con opción "restaurar".
- Restauración: seleccionar backup y confirmar (sobrescribe dictionary actual).

## Flujo 7 — Importar / Exportar masivo
- Importar CSV: validar formato; vista previa de cambios antes de aplicar.
- Exportar: descargar JSON o CSV completo del diccionario.
- Recomendación: hacer backup manual antes de importaciones masivas.

## Operaciones administrativas rápidas
- Reiniciar app: cerrar terminal y ejecutar python app.py.
- Ver logs: revisar la terminal donde corre Flask.
- Confirmar ffmpeg: ffmpeg -version en PowerShell.
- Editar .env: ajustar SECRET_KEY, DATA_DIR, HOST/PORT.

## Consejos de uso
- Probar primero con pocas entradas antes de import masivo.
- Mantener copias de seguridad externas además de los backups automáticos.
- Ajustar permisos de micrófono en Windows si la grabación no funciona.

# API — Endpoints detallados

A continuación se listan los endpoints principales que ofrece la aplicación. Para ejemplos se usa http://127.0.0.1:5000 como base.

---

### 1) POST /api/translate
- Descripción: traducir texto y devolver idioma detectado.
- Parámetros (form o JSON):
  - text (string) — requerido
  - src (string) — opcional, p. ej. "es" o "qu" (auto si no)
  - dest (string) — opcional, p. ej. "qu" o "es"
- Ejemplo request:
````bash
```bash
curl -X POST "http://127.0.0.1:5000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola, ¿cómo estás?"}'
```
````
- Ejemplo response (200):
````json
{
  "text": "Hola, ¿cómo estás?",
  "detected_lang": "es",
  "translation": "Rimaykullayki, allin kachanki?",
  "provider": "googletrans",
  "score": 0.92
}
````
- Códigos HTTP: 200 OK, 400 Bad Request (falta text), 500 Internal Error.

---

### 2) POST /api/transcribe
- Descripción: enviar audio y recibir transcripción.
- Parámetros (multipart/form-data):
  - file (audio) — requerido (wav/mp3/ogg)
  - lang (string) — opcional (p.ej. "es" o "qu")
- Ejemplo request:
````bash
```bash
curl -X POST "http://127.0.0.1:5000/api/transcribe" \
  -F "file=@grabacion.wav" \
  -F "lang=es"
```
````
- Ejemplo response (200):
````json
{
  "transcript": "Hola que tal",
  "lang": "es",
  "confidence": 0.87
}
````
- Códigos HTTP: 200, 400 (archivo inválido), 415 Unsupported Media Type, 500.

---

### 3) POST /api/tts
- Descripción: generar audio TTS y devolver URL o nombre de archivo.
- Parámetros (form o JSON):
  - text (string) — requerido
  - lang (string) — opcional ("es" por defecto)
  - slow (bool) — opcional
  - filename (string) — opcional
- Ejemplo request:
````bash
```bash
curl -X POST "http://127.0.0.1:5000/api/tts" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola","lang":"es","slow":false}'
```
````
- Ejemplo response (200):
````json
{
  "filename": "tts_1690000000.mp3",
  "audio_url": "/static/audio/tts_1690000000.mp3"
}
````
- Códigos HTTP: 200, 400 (texto vacío), 500.

---

### 4) GET /api/dictionary
- Descripción: obtener entradas del diccionario (paginado, búsqueda).
- Query params:
  - q (string) — búsqueda libre
  - page (int) — por defecto 1
  - per_page (int) — por defecto 20
  - lang (string) — filtrar por idioma si aplica
- Ejemplo:
````bash
```bash
curl "http://127.0.0.1:5000/api/dictionary?q=agua&page=1&per_page=10"
```
````
- Ejemplo response (200):
````json
{
  "page": 1,
  "per_page": 10,
  "total": 123,
  "items": [
    {"id":"1","es":"agua","qu":"yaku","tags":["sustantivo"]},
    ...
  ]
}
````
- Códigos: 200, 400.

---

### 5) POST /api/dictionary/add
- Descripción: añadir nueva entrada.
- Body JSON:
  - es (string) — requerido
  - qu (string) — requerido
  - tags (array/string) — opcional
- Ejemplo:
````bash
```bash
curl -X POST "http://127.0.0.1:5000/api/dictionary/add" \
  -H "Content-Type: application/json" \
  -d '{"es":"fuego","qu":"nina","tags":["elemento"]}'
```
````
- Response (201):
````json
{"id":"124","es":"fuego","qu":"nina","created": "2025-10-08T12:00:00"}
````
- Códigos: 201 Created, 400 Bad Request, 409 Conflict (ya existe).

---

### 6) PUT /api/dictionary/update/<id>
- Descripción: actualizar entrada por id.
- URL param: id
- Body JSON: campos a actualizar (es/qu/tags)
- Ejemplo:
````bash
```bash
curl -X PUT "http://127.0.0.1:5000/api/dictionary/update/124" \
  -H "Content-Type: application/json" \
  -d '{"qu":"ninaña","tags":["elemento","modificado"]}'
```
````
- Response (200):
````json
{"id":"124","es":"fuego","qu":"ninaña","updated":"2025-10-08T12:10:00"}
````
- Códigos: 200, 400, 404 Not Found.

---

### 7) DELETE /api/dictionary/delete/<id>
- Descripción: eliminar entrada por id.
- URL param: id
- Ejemplo:
````bash
```bash
curl -X DELETE "http://127.0.0.1:5000/api/dictionary/delete/124"
```
````
- Response (200):
````json
{"id":"124","deleted":true}
````
- Códigos: 200, 404.

---

### 8) POST /api/dictionary/import
- Descripción: importar CSV masivo (vista previa opcional).
- Parámetros (multipart/form-data):
  - file (csv) — requerido (formato español,kichwa, sin encabezado por defecto)
  - preview (bool) — opcional; si true devuelve vista previa sin aplicar
  - delimiter (string) — opcional, default ","
- Ejemplo:
````bash
```bash
curl -X POST "http://127.0.0.1:5000/api/dictionary/import" \
  -F "file=@base_dictionary.csv" \
  -F "preview=true"
```
````
- Response preview (200):
````json
{"preview": true, "rows": 150, "to_add": 140, "to_update": 10, "sample":[{"es":"hola","qu":"rimay"}]}
````
- Response aplicado (200):
````json
{"imported":140,"updated":10,"skipped":0,"backup":"data/backups/dictionary_import_20251008.json"}
````
- Códigos: 200, 400 (formato inválido), 500.

---

### 9) GET /api/dictionary/export
- Descripción: exportar diccionario completo.
- Query params:
  - format (csv|json) — default json
- Ejemplo:
````bash
```bash
curl "http://127.0.0.1:5000/api/dictionary/export?format=csv" -o export.csv
```
````
- Response: archivo CSV o JSON (200).
- Códigos: 200, 400.

---

### 10) GET /api/study/flashcards
- Descripción: generar flashcards desde el diccionario.
- Query params:
  - count (int) — por defecto 20
  - dir (string) — "es_qu" o "qu_es"
  - tags (string) — opcional
- Ejemplo:
````bash
```bash
curl "http://127.0.0.1:5000/api/study/flashcards?count=10&dir=es_qu"
```
````
- Response (200):
````json
{
  "count":10,
  "cards":[
    {"id":"12","front":"agua","back":"yaku"},
    ...
  ]
}
````
- Códigos: 200, 400.

---

### 11) GET /api/study/quiz
- Descripción: generar quiz (opción múltiple o relleno).
- Query params:
  - count, dir, type (mcq|fill)
- Ejemplo response (200):
````json
{
  "count":10,
  "type":"mcq",
  "questions":[
    {"id":"5","question":"¿Qué significa 'yaku'?", "options":["agua","fuego","tierra"], "answer":"agua"},
    ...
  ]
}
````
- Códigos: 200, 400.

---

### 12) GET /api/history
- Descripción: obtener historial de cambios.
- Response (200):
````json
[
  {"id":"h1","action":"import","timestamp":"2025-10-08T10:00:00","meta":{...}},
  ...
]
````
- Códigos: 200.

---

### 13) POST /api/history/restore
- Descripción: restaurar backup/historial.
- Body JSON:
  - backup (string) — nombre de archivo o id de backup requerido
- Ejemplo:
````bash
```bash
curl -X POST "http://127.0.0.1:5000/api/history/restore" \
  -H "Content-Type: application/json" \
  -d '{"backup":"dictionary_es_qu_v1_20251008.json"}'
```
````
- Response (200):
````json
{"restored": true, "backup":"data/backups/dictionary_es_qu_v1_20251008.json"}
````
- Códigos: 200, 400, 404.

---

### 14) GET /api/meta
- Descripción: metadatos del sistema/diccionario.
- Response (200):
````json
{
  "entry_count": 1250,
  "last_updated": "2025-10-08T12:00:00",
  "version": "v1"
}
````
- Códigos: 200.

---

Notas generales
- Todos los endpoints JSON esperan y devuelven UTF-8.
- Errores devuelven { "error": "mensaje" } con el código HTTP apropiado.
- Operaciones que modifican el diccionario generan backup automático y entrada en history.
- Para subir archivos (audio/CSV) usar multipart/form-data.

# Diccionario — Estructura data/, import/export, backups

## Estructura de la carpeta data/
- data/
  - dictionary_es_qu.json        — diccionario principal (persistente)
  - base_dictionary.csv          — plantilla / ejemplo CSV (es,qu)
  - meta.json                    — metadatos (conteo, versión, last_updated)
  - history.json                 — log de operaciones (imports, cambios, restores)
  - backups/                     — copias de seguridad (snapshots .json)
    - dictionary_es_qu_v1_20251008_164755_postsave.json
  - other files (exports temporales, imports pendientes)

## Formato del diccionario (dictionary_es_qu.json)
- Representación: lista de objetos JSON (array) o mapa id → objeto. Recomendada: array para mantener orden e historial simple.
- Esquema por entrada:
  - id (string) — id único (timestamp o uuid)
  - es (string) — entrada en español
  - qu (string) — entrada en kichwa
  - tags (array[string]) — opcional (p. ej. ["sustantivo"])
  - created (ISO8601) — timestamp de creación
  - updated (ISO8601) — timestamp de última modificación
  - metadata (obj) — opcional (fuente, notas)

Ejemplo (fragmento):
```json
{
  "id": "20251008_164700_001",
  "es": "agua",
  "qu": "yaku",
  "tags": ["sustantivo"],
  "created": "2025-10-08T16:47:00Z",
  "updated": "2025-10-08T16:47:00Z"
}
```

## CSV — formato de importación / exportación
- Formato esperado (por fila, sin encabezado por defecto):
  - español,kichwa
- Opcional: tercer campo tags separados por `;` (implementación variable)
- Ejemplo CSV:
```csv
agua,yaku
fuego,nina
tierra,allpa
hola,rimay
```
- Al importar:
  - Validar número de columnas y codificación UTF-8.
  - Trim de espacios, normalizar mayúsculas/minúsculas.
  - Opcional: preview que muestra cuántas filas se añadirán/actualizarán.

## Exportación
- Soporta JSON y CSV:
  - JSON: volcado completo de dictionary_es_qu.json (array).
  - CSV: convertir cada entrada a `es,qu[,tags]`.
- Endpoint: /api/dictionary/export?format=csv|json
- Recomendación: agregar headers HTTP para forzar descarga.

## Backups (naming, cuándo, cómo)
- Carpeta: data/backups/
- Convención de nombre: dictionary_es_qu_v{version}_{YYYYMMDD_HHMMSS}_{action}.json
  - Ejemplo: dictionary_es_qu_v1_20251008_164755_postsave.json
  - action: presave/postsave/import_restore/etc.
- Cuándo se crea un backup:
  - Antes y después de operaciones masivas (import).
  - Al guardar cambios importantes (import, delete masivo, restore).
  - Opcional: cada N cambios o al cerrar la app (configurable).
- Mecanismo seguro:
  1. Serializar a archivo temporal (data/tmp_XXXXX.json).
  2. fsync / flush (si aplica).
  3. Renombrar atómico a data/backups/...
  4. Finalmente reemplazar dictionary_es_qu.json por nuevo archivo atómico (tmp → dictionary_es_qu.json).
- Mantener un máximo de N backups (p. ej. 50) y rotación automática si se desea.

## history.json (registro de cambios)
- Array de entradas con:
  - id (uuid/timestamp)
  - action (import|add|update|delete|restore)
  - timestamp
  - user (si aplica)
  - meta (counts, backup_path, affected_ids)
- Permite historial y restauración guiada por UI.

Ejemplo:
```json
{
  "id":"h_20251008_165000",
  "action":"import",
  "timestamp":"2025-10-08T16:50:00Z",
  "meta":{"imported":140,"updated":10,"backup":"data/backups/dictionary_import_20251008.json"}
}
```

## Restauración (restore)
- Vía API: POST /api/history/restore { "backup": "data/backups/archivo.json" }
- Proceso:
  1. Validar existencia del backup.
  2. Crear backup presave del estado actual.
  3. Reemplazar dictionary_es_qu.json por backup seleccionado (método atómico).
  4. Registrar action restore en history.json y crear backup postsave.
- Alternativa manual: copiar archivo desde data/backups → dictionary_es_qu.json (asegurar cierre de la app o bloqueo).

## Buenas prácticas operativas
- Siempre hacer backup automático antes de imports/operaciones destructivas.
- Validar encoding UTF-8 en CSV antes de importar.
- Mantener meta.json consistente: actualizar entry_count y last_updated en cada save.
- Operaciones atómicas para evitar corrupciones si la app se interrumpe.
- Hacer pruebas de restore en entorno de desarrollo antes de producir cambios masivos.

# Estudiar — Flashcards / Quiz (configuración y ejemplos)

## Resumen
Módulo para generar flashcards y quizzes desde el diccionario. Soporta dirección (es→qu, qu→es), filtros por tags, tamaño, tipo de pregunta (MCQ / fill), y opciones de repetición espaciada (SRS) básica.

## Configuración (variables / parámetros del servidor)
- DEFAULT_FLASHCARD_COUNT = 20
- DEFAULT_QUIZ_COUNT = 10
- FLASHCARD_DIRS = ["es_qu","qu_es"]
- QUIZ_TYPES = ["mcq","fill"]
- SRS_ENABLED = true/false
- SRS_LEVELS = [1,2,3,4,5] (intervalos configurables en días)
- STUDY_DATA_PATH = data/study_progress.json (opcional, guarda estado por usuario)

Puedes exponer estas constantes en app.py o config.py y permitir edición vía UI.

## Endpoints relevantes
- GET /api/study/flashcards
  - Query params:
    - count (int) — número de tarjetas (default 20)
    - dir (string) — "es_qu" o "qu_es" (default es_qu)
    - tags (comma) — filtrar por tags
    - shuffle (bool) — mezclar (default true)
  - Response: lista de tarjetas {id, front, back, tags}

- GET /api/study/quiz
  - Query params:
    - count (int) — número de preguntas (default 10)
    - dir (string) — "es_qu" o "qu_es"
    - type (string) — "mcq" | "fill"
    - tags (comma)
  - Response: preguntas con formato según type

- POST /api/study/answer (opcional)
  - Body JSON: { question_id, answer, correct (bool), elapsed_ms }
  - Usa para registrar progreso / SRS.

## Reglas de generación (algoritmo)
- Seleccionar entradas filtradas por tags.
- Orden:
  1. Priorizar entradas con estado SRS bajo (si SRS habilitado).
  2. Completar con entradas aleatorias.
- Para MCQ:
  - Tomar la entrada target.
  - Generar 3 distractores seleccionando otras entradas al azar (mismo idioma y categoría si posible).
  - Mezclar opciones y marcar la correcta.
- Para Fill:
  - Proveer frase o sola palabra con campo en blanco; evaluar igualdad normalizada (ignorar mayúsculas, tildes opcional).

Pseudocódigo (resumen):
````python
# seleccionar entradas
candidates = filter_by_tags(dictionary, tags)
priority = sort_by_srs_due(candidates)  # si SRS
selected = take(priority, count)
for item in selected:
  if quiz_type == "mcq":
    distractors = sample(candidates.exclude(item), 3)
    options = shuffle([item.correct_answer] + distractors)
  else:
    prompt = item.front
````

## Ejemplos de request / response

Flashcards — ejemplo:
````bash
```bash
curl "http://127.0.0.1:5000/api/study/flashcards?count=5&dir=es_qu"
```
````
````json
{
  "count": 5,
  "cards": [
    {"id":"12","front":"agua","back":"yaku","tags":["sustantivo"]},
    {"id":"34","front":"fuego","back":"nina","tags":["sustantivo"]},
    {"id":"98","front":"hola","back":"rimay","tags":["saludo"]},
    {"id":"21","front":"tierra","back":"allpa","tags":["sustantivo"]},
    {"id":"56","front":"cantar","back":"takiy","tags":["verbo"]}
  ]
}
````

Quiz MCQ — ejemplo:
````bash
```bash
curl "http://127.0.0.1:5000/api/study/quiz?count=3&dir=es_qu&type=mcq"
```
````
````json
{
  "count": 3,
  "type": "mcq",
  "questions": [
    {
      "id":"12",
      "question":"¿Qué significa 'agua'?",
      "options":["yaku","nina","allpa","rimay"]
    },
    {
      "id":"34",
      "question":"¿Qué significa 'fuego'?",
      "options":["nina","yaku","allpa","takiy"]
    },
    {
      "id":"98",
      "question":"¿Cómo se dice 'hola'?",
      "options":["rimay","yaku","nina","allpa"]
    }
  ]
}
````

Quiz Fill — ejemplo:
````bash
```bash
curl "http://127.0.0.1:5000/api/study/quiz?count=2&dir=qu_es&type=fill"
```
````
````json
{
  "count":2,
  "type":"fill",
  "questions":[
    {"id":"12","prompt":"yaku","answer":"agua"},
    {"id":"21","prompt":"allpa","answer":"tierra"}
  ]
}
````

Registro de respuesta (POST /api/study/answer) — ejemplo:
````bash
```bash
curl -X POST "http://127.0.0.1:5000/api/study/answer" \
  -H "Content-Type: application/json" \
  -d '{"question_id":"12","answer":"yaku","correct":true,"elapsed_ms":4500}'
```
````
Response:
````json
{"saved": true, "next_review":"2025-10-10T12:00:00Z","srs_level":2}
````

## Scoring y SRS básico
- Si correct:
  - aumentar nivel SRS (nivel +=1), programar next_review = now + interval[level]
- Si incorrect:
  - bajar nivel (nivel = max(1, level-1)), next_review = now + interval[level]
- Intervalos configurables (ejemplo en días): [1,2,4,7,14]

## UI / UX sugerido
- Flashcards: mostrar front; botón "Mostrar respuesta"; botones: "No lo sé", "Casi", "Lo sé" (mapear a SRS adjustments).
- Quiz MCQ: feedback inmediato y marcador.
- Progreso: mostrar barra de sesión, porcentaje correcto, resumen al final con tarjetas falladas.
- Opcional: botón para repetir fallos sólo.

## Buenas prácticas
- Usar sampling sin reemplazo en sesión para evitar repeticiones inmediatas.
- Ofrecer preview antes de iniciar (número y tags).
- Guardar progreso local + server para retomar sesiones.

# Desarrollo — estructura del código, docstrings y estilo

## Estructura recomendada
- Paquetes claros, separación web / lógica / datos / tests:
````text
// project root
asistente_kichwa/
├─ app.py
├─ config.py
├─ requirements.txt
├─ pyproject.toml
├─ README.md
├─ data/
├─ templates/
├─ static/
├─ src/
│  ├─ asistentekichwa/
│  │  ├─ __init__.py
│  │  ├─ api.py
│  │  ├─ dictionary.py
│  │  ├─ tts.py
│  │  ├─ transcribe.py
│  │  └─ study.py
├─ tests/
│  ├─ test_dictionary.py
│  └─ test_api.py
└─ .github/workflows/ci.yml
````

## Convenciones de estilo
- Seguir PEP 8.
- Uso de type hints en funciones públicas.
- Nombrado: snake_case para funciones/variables, PascalCase para clases.
- Módulos pequeños (SRP): cada archivo < 400 líneas si es posible.
- Commits con Conventional Commits (feat/, fix/, chore/).

## Docstrings
- Usar estilo Google o NumPy (consistente en todo el proyecto). Incluir: descripción, args, returns, raises.
- Documentar comportamiento esperado, tipos y valores especiales (e.g., encodings, límites).

Ejemplo (Google style) con type hints:
````python
"""Gestión del diccionario (lectura/escritura, búsqueda, import/export)."""

from typing import List, Dict, Optional
import json
from datetime import datetime
import uuid

def load_dictionary(path: str) -> List[Dict]:
    """Cargar diccionario desde JSON.

    Args:
        path: Ruta al archivo JSON del diccionario.

    Returns:
        Lista de entradas del diccionario (cada entrada es un dict).
    
    Raises:
        FileNotFoundError: Si el archivo no existe.
        json.JSONDecodeError: Si el archivo no contiene JSON válido.
    """
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def add_entry(dictionary: List[Dict], es: str, qu: str, tags: Optional[List[str]] = None) -> Dict:
    """Agregar una entrada nueva al diccionario y devolverla.

    Args:
        dictionary: Lista en memoria del diccionario.
        es: Texto en español.
        qu: Texto en kichwa.
        tags: Lista opcional de etiquetas.

    Returns:
        El objeto de entrada creado con id, created y updated.
    """
    entry = {
        "id": str(uuid.uuid4()),
        "es": es.strip(),
        "qu": qu.strip(),
        "tags": tags or [],
        "created": datetime.utcnow().isoformat() + "Z",
        "updated": datetime.utcnow().isoformat() + "Z",
    }
    dictionary.append(entry)
    return entry
````

## Formato y herramientas recomendadas
- Formateo: black (configurar en pyproject.toml).
- Import ordering: isort.
- Linters: ruff o flake8 + mypy para tipado.
- Tests: pytest.
- Pre-commit hooks para formateo/linters.

Ejemplo mínimo pyproject.toml:
````toml
[tool.black]
line-length = 88

[tool.isort]
profile = "black"

[tool.ruff]
line-length = 88
select = ["E","F","W","B","C"]
ignore = ["E203"]
````

## Tests y cobertura
- Carpeta tests/ con pruebas unitarias aisladas.
- Fixtures para crear diccionarios de prueba en tmp_path.
- Ejecutar: venv\Scripts\activate && pytest -q
Ejemplo test:
````python
from src.asistentekichwa.dictionary import add_entry

def test_add_entry_creates_id_and_timestamps():
    d = []
    e = add_entry(d, "agua", "yaku")
    assert "id" in e
    assert e["es"] == "agua"
    assert len(d) == 1
````

## Logging y manejo de errores
- Usar logging.getLogger(__name__) por módulo.
- Excepciones explícitas y errores con mensajes claros; capturar en endpoints HTTP y devolver JSON { "error": msg } con código HTTP apropiado.

Ejemplo de logger:
````python
import logging
logger = logging.getLogger(__name__)

def some_endpoint(...):
    try:
        ...
    except ValueError as exc:
        logger.exception("Error procesando X")
        raise
````

## CI y calidad
- Pipeline básico (GitHub Actions) que ejecuta: install, lint, format check, type check, pytest.
- Usar badges en README para build / coverage.

## Documentación
- Mantener README con pasos de instalación y ejemplos de uso.
- Documentación de API: OpenAPI/Swagger o al menos un /docs generado (mkdocs o Sphinx).

## Resumen rápido
- Estructura modular, docstrings consistentes (Google/Numpy), type hints, black/isort/ruff, pytest y logging.
- Automatizar checks con pre-commit y CI para garantizar estilo y calidad.

# Despliegue y operaciones (producción, variables env, ffmpeg, backups)

## 1. Entorno de producción — recomendaciones generales
- Ejecutar la app detrás de un servidor WSGI en producción (no el servidor de desarrollo de Flask).
  - Windows: usar Waitress (simple y estable).
  - Linux: usar Gunicorn + supervisor/systemd o uWSGI.
- Usar un reverse proxy (NGINX/Traefik/IIS) para:
  - Terminar TLS (HTTPS).
  - Servir archivos estáticos (static/) eficientemente.
  - Manejo de cabeceras, timeouts y logging.
- No exponer Flask directamente a Internet; bind localhost y dejar al reverse proxy recibir tráfico público.

## 2. Variables de entorno críticas
- FLASK_APP=app.py
- FLASK_ENV=production
- SECRET_KEY=valor_largo_y_aleatorio
- DATA_DIR=path\a\data
- AUDIO_DIR=path\a\static\audio
- UPLOAD_FOLDER=path\a\static\uploads
- MAX_CONTENT_LENGTH=16777216
- HOST=127.0.0.1
- PORT=5000
- FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe (o vacío si ffmpeg está en PATH)
- TTS_PROVIDER=gtts
- LOG_LEVEL=INFO
- BACKUP_RETENTION=30  (número de backups a conservar)
- HEALTHCHECK_TOKEN=secret_token (si se usan endpoints de healthcheck)

Cargar con python-dotenv en inicio o definir en servicio/ci.

## 3. ffmpeg — instalación y verificación (Windows)
- Descargar build de https://www.gyan.dev/ffmpeg/builds/ o https://ffmpeg.org/download.html.
- Extraer en C:\ffmpeg y confirmar existencia de C:\ffmpeg\bin\ffmpeg.exe.
- Añadir C:\ffmpeg\bin al PATH (Set-ExecutionPolicy no requerido):
  - PowerShell (ejecutar como admin una vez):
    setx PATH "$($env:Path);C:\ffmpeg\bin"
- Verificar:
  - En PowerShell: ffmpeg -version
- Alternativa: especificar FFMPEG_PATH en .env si no se añade al PATH.

## 4. Ejecutar en Windows con Waitress (ejemplo)
- Instalar:
  pip install waitress
- Ejecutar:
```powershell
```powershell
waitress-serve --port=5000 --call 'app:create_app'
```
```
(Ajustar si la app exporta create_app o usar: waitress-serve --port=5000 app:app)

## 5. Ejecutar como servicio en Windows (opciones)
- NSSM (Non-Sucking Service Manager) para crear servicio que ejecute el comando Waitress o python app.py.
- Task Scheduler — crear tarea que inicie en arranque y reinicie si falla.
- Ejemplo NSSM: nssm install asistente_kichwa "C:\path\to\venv\Scripts\python.exe" "C:\... \venv\Scripts\waitress-serve" --args.

## 6. Backups — política y script de rotación (Windows PowerShell)
- Crear backup antes y después de operaciones destructivas (import, restore).
- Convención de nombre: dictionary_es_qu_v{v}_{YYYYMMDD_HHMMSS}_{action}.json
- Retención: conservar N backups (p. ej. 30).
- Script PowerShell (crea backup y rota dejando N últimos):
```powershell
```powershell
# Backup simple y rotación
$DataDir = "C:\Users\Lab Escuela 6\Desktop\asistente_kichwa\data"
$BackupsDir = Join-Path $DataDir "backups"
$Src = Join-Path $DataDir "dictionary_es_qu.json"
$Now = (Get-Date).ToString("yyyyMMdd_HHmmss")
$Dest = Join-Path $BackupsDir ("dictionary_es_qu_v1_${Now}_autosave.json")
New-Item -ItemType Directory -Path $BackupsDir -Force | Out-Null
Copy-Item -Path $Src -Destination $Dest -Force
# Rotación: conservar últimos N
$Retention = 30
$files = Get-ChildItem -Path $BackupsDir -Filter "dictionary_es_qu_*.json" | Sort-Object LastWriteTime -Descending
if ($files.Count -gt $Retention) {
  $files[$Retention..($files.Count-1)] | Remove-Item -Force
}
Write-Output "Backup creado: $Dest"
```
```

## 7. Backups atómicos en código (recomendación)
- Guardar en temp, fsync/flush si es posible, luego renombrar (atomic rename).
- Hacer copia previa (presave) antes de import masivo y postsave después.

## 8. Monitoring, logs y healthchecks
- Logs: stdout + fichero rotado (logrotate en Linux, Scheduled Task/Windows Event en Windows).
- Exponer endpoint /health o /api/meta protegido por token para checks.
- Integrar un monitor simple (UptimeRobot) que llame al healthcheck.
- Alertas básicas: fallos de proceso, errores 5xx recurrentes, disco lleno.

## 9. Seguridad y operación
- Mantener SECRET_KEY fuerte y fuera de repositorio.
- Deshabilitar FLASK_DEBUG en producción.
- Habilitar CORS selectivo si la UI y la API están separadas.
- Limitar tamaños de upload: MAX_CONTENT_LENGTH.
- Rate limiting para endpoints sensibles (tts, translate, import).
- Control de acceso para operaciones destructivas (import/restore) — proteger por autenticación simple o token.

## 10. Actualizaciones y despliegue continuo
- Para Windows: desplegar paquete, instalar venv, reiniciar servicio NSSM/Task Scheduler.
- Para Linux: usar CI que empuje release, ejecutar systemd restart, ejecutar migraciones/backups previos.
- Blue/green o despliegue con un proxy para minimizar downtime (opcional en infra más compleja).

## 11. Ejemplo systemd (Linux)
- Archivo unit simple:
```ini
```ini
[Unit]
Description=Asistente Kichwa
After=network.target

[Service]
User=www-data
WorkingDirectory=/srv/asistente_kichwa
EnvironmentFile=/srv/asistente_kichwa/.env
ExecStart=/srv/asistente_kichwa/venv/bin/gunicorn -w 3 -b 127.0.0.1:8000 app:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
```
# Apéndice: comandos útiles, referencias, contactos

## Comandos útiles (Windows — PowerShell / CMD)
- Ir al proyecto:
```powershell
```powershell
cd "C:\Users\Lab Escuela 6\Desktop\asistente_kichwa"
```
```

- Crear y activar venv (PowerShell / CMD):
```powershell
```powershell
python -m venv venv
Activate.ps1    # PowerShell
venv\Scripts\activate          # CMD
```
```

- Instalar dependencias:
```powershell
```powershell
pip install -r requirements.txt
```
```

- Verificar ffmpeg:
```powershell
```powershell
ffmpeg -version
# o si usas ruta explícita:
ffmpeg.exe -version
```
```

- Ejecutar app (desarrollo):
```powershell
```powershell
python app.py
# o
set FLASK_APP=app.py
set FLASK_ENV=development
flask run --host=127.0.0.1 --port=5000
```
```

- Ejecutar con Waitress (producción Windows):
```powershell
```powershell
pip install waitress
waitress-serve --port=5000 app:app
```
```

- Ejecutar tests:
```powershell
```powershell
venv\Scripts\activate
pytest -q
```
```

- Formatear / lint:
```powershell
```powershell
# black/isort/ruff
black .
isort .
ruff .
```
```

- Crear backup manual (PowerShell, rápida):
```powershell
```powershell
$now=(Get-Date).ToString("yyyyMMdd_HHmmss"); Copy-Item data\dictionary_es_qu.json data\backups\dictionary_es_qu_$now.json
```
```

- Curl ejemplos API
  - Traducir:
```bash
```bash
curl -X POST http://127.0.0.1:5000/api/translate -H "Content-Type: application/json" -d '{"text":"Hola"}'
```
```
  - TTS:
```bash
```bash
curl -X POST http://127.0.0.1:5000/api/tts -H "Content-Type: application/json" -d '{"text":"Hola","lang":"es"}'
```
```
  - Import CSV (multipart):
```bash
```bash
curl -X POST http://127.0.0.1:5000/api/dictionary/import -F "file=@base_dictionary.csv" -F "preview=true"
```
```

- Restaurar backup via API:
```bash
```bash
curl -X POST http://127.0.0.1:5000/api/history/restore -H "Content-Type: application/json" -d '{"backup":"data/backups/archivo.json"}'
```
```

## Referencias rápidas
- Flask: https://flask.palletsprojects.com/
- gTTS: https://pypi.org/project/gTTS/
- SpeechRecognition: https://pypi.org/project/SpeechRecognition/
- googletrans (4.0.0-rc1): https://pypi.org/project/googletrans/
- pydub: https://pydub.com/
- FFmpeg: https://ffmpeg.org/
- Waitress (Windows WSGI): https://docs.pylonsproject.org/projects/waitress/
- NSSM (servicio Windows): https://nssm.cc/
- Black / isort / ruff / pytest: documentación en PyPI/GitHub
- OpenAPI / Swagger: https://swagger.io/