# Rimaykuna — Asistente Kichwa ↔ Español

Aplicación web para traducir entre Kichwa y Español con soporte de voz, un diccionario editable y una sección de estudio con flashcards y quizzes. Diseñada para cursos, universidades y comunidades que enseñan/aprenden Kichwa.

![Logo de la aplicación](./static/img/logo.png)

## Características

- Traducción bidireccional texto ↔ texto con heurísticas para Kichwa y fallback a traductor externo.
- Diccionario local editable: agregar, editar, eliminar, importar (CSV) y exportar (CSV/JSON).
- Estudio: flashcards y cuestionarios generados a partir del diccionario.
- Audio: síntesis de voz (TTS) para escuchar resultados y tarjetas.
- Backups automáticos, historial de cambios y metadatos de diccionario.

## Requisitos

- Python 3.10+ recomendado.
- Navegador moderno con Web Audio API.
- Micrófono (opcional) para entrada de voz.
- Para mayor compatibilidad de audio local: `ffmpeg` instalado y en el PATH del sistema.

Puedes verificar `ffmpeg` en la app: `GET /api/ffmpeg`.

Nota: ahora la app incluye un modo de transcripción gratuito en el navegador usando Web Speech API (no requiere ffmpeg ni claves). Ver detalles abajo.

## Instalación y ejecución

1) Clona el repositorio y entra al directorio del proyecto:
```bash
git clone https://github.com/Jorge-Doicela/asistente_kichwa.git
cd asistente_kichwa
```

2) Crea y activa un entorno virtual:
```powershell
# Windows (si es necesario, habilita scripts en PowerShell):
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3) Instala dependencias:
```bash
pip install -r requirements.txt
```

4) Ejecuta la aplicación en desarrollo:
```bash
python app.py
```

5) Abre el navegador en `http://127.0.0.1:5000`.

## Configuración (opcional)

Transcripción remota (fallback si falla la conversión local):

- `OPENAI_API_KEY`: clave de API para transcripción remota.
- `TRANSCRIBE_PROVIDER`: por ahora `openai` (valor por defecto `openai`).

Ejemplos para definir la variable en Windows:
```powershell
# PowerShell (misma terminal donde arrancas la app)
$env:OPENAI_API_KEY = 'sk-xxxxx'
python .\app.py
```
```cmd
:: CMD clásico (misma ventana)
set OPENAI_API_KEY=sk-xxxxx
python app.py
```

Notas:
- gTTS no soporta voces Kichwa; se usa español como aproximación cuando `lang` es Kichwa.
- Para usar micrófono en el navegador, abre la app en `http://127.0.0.1:5000` o `http://localhost` (contexto seguro) y concede el permiso.

### Cómo obtener y gestionar acceso a la API (OpenAI Whisper)

1) Crear cuenta y obtener clave
- Crea o inicia sesión en tu cuenta de OpenAI.
- Genera una API key desde la sección de API keys del panel de control.
- Copia la clave (formato similar a `sk-...`). Guárdala de forma segura.

2) Establecer la clave en cada dispositivo
- La app lee `OPENAI_API_KEY` del entorno. Debes configurarla en el dispositivo donde se ejecuta el servidor.

Windows
- PowerShell (por sesión):
```powershell
$env:OPENAI_API_KEY = 'sk-xxxxx'
python .\app.py
```
- CMD (por sesión):
```cmd
set OPENAI_API_KEY=sk-xxxxx
python app.py
```
- Permanente (todas las sesiones): Panel de Control → Sistema → Configuración avanzada del sistema → Variables de entorno → Nueva variable de usuario/sistema `OPENAI_API_KEY` con tu clave. Cierra y abre terminal para que tome efecto.

Linux/macOS
- Por sesión:
```bash
export OPENAI_API_KEY=sk-xxxxx
python app.py
```
- Permanente: agrega a tu archivo de perfil (`~/.bashrc`, `~/.zshrc`):
```bash
export OPENAI_API_KEY=sk-xxxxx
```
Luego abre una nueva terminal.

3) Verificar que la app ve la clave
- Inicia la app desde la misma terminal donde definiste la variable y prueba grabar. Si no detecta la clave, revisa que ejecutaste `python app.py` en la misma sesión.

4) Buenas prácticas
- No compartas tu API key ni la subas a repositorios.
- Si vas a distribuir la app a otras máquinas, no hardcodees la clave; indica a cada usuario cómo definir `OPENAI_API_KEY` en su sistema.
- Si despliegas en un servidor, configura la variable en el servicio (por ejemplo, archivo `.service` de systemd o variables del hosting).

## Transcripción de voz: modos y orden de fallback

La app prioriza no requerir instalación de ffmpeg ni claves:

1) Web Speech API (gratis, en el navegador)
- Si el navegador soporta `SpeechRecognition`/`webkitSpeechRecognition`, la transcripción se hace localmente.
- Recomendado: Chrome/Edge. Firefox no la soporta.
- Idiomas configurados: `es-EC` para español y `qu-EC` para Kichwa. Algunos navegadores podrían no reconocer bien `qu-EC`.

2) API remota (si hay `OPENAI_API_KEY`)
- Si no hay Web Speech API o esta falla, el servidor intenta transcripción remota con OpenAI (sin necesidad de ffmpeg).

3) Flujo local con conversión (requiere ffmpeg)
- Si lo anterior falla y tienes `ffmpeg` en PATH, el servidor convierte a WAV y usa reconocimiento local.

## Uso de la aplicación

- Inicio (Traductor): ingresa texto o usa micrófono, la app detecta idioma (heurística) y traduce; puedes reproducir el resultado con TTS.
- Diccionario (`/diccionario`): busca, ordena, pagina, agrega/edita/elimina términos. Importa CSV (`español,kichwa`) y exporta CSV/JSON. Consulta metadatos, historial y backups.
- Estudiar (`/estudiar`): practica con flashcards (ES→QU / QU→ES) o quizzes de opción múltiple.

Consejos para micrófono
- Si ves "Permiso denegado", haz clic en el candado de la barra de direcciones y permite el micrófono.
- Si aparece "contexto inseguro", usa `http://127.0.0.1:5000` o `http://localhost:5000`.
- Cierra aplicaciones que estén usando el micrófono (Zoom, Teams, etc.).

## API (resumen con ejemplos)

Traducción
```bash
curl -s -X POST http://127.0.0.1:5000/translate \
  -H 'Content-Type: application/json' \
  -d '{"text":"hola", "src":"es", "dest":"qu"}'
```

Transcripción (archivo)
```bash
curl -s -X POST http://127.0.0.1:5000/transcribe \
  -F 'file=@audio.wav' -F 'lang=es'
```

Texto a voz (TTS)
```bash
curl -s -X POST http://127.0.0.1:5000/text-to-speech \
  -H 'Content-Type: application/json' \
  -d '{"text":"alli puncha", "lang":"qu-EC"}'
```

Diccionario
- Obtener: `GET /api/dictionary`
- Agregar: `POST /api/dictionary/add` `{ spanish, kichwa }`
- Actualizar/renombrar: `POST /api/dictionary/update` `{ spanish, spanish_new?, kichwa }`
- Eliminar: `POST /api/dictionary/delete` `{ spanish }`
- Importar CSV: `POST /api/dictionary/import` (multipart/form-data con `file`)
- Exportar: `GET /api/dictionary/export?format=json|csv`
- Metadatos: `GET /api/dictionary/meta`
- Historial: `GET /api/dictionary/history?limit=200`
- Backups: `GET /api/dictionary/backups`
- Restaurar: `POST /api/dictionary/restore` `{ file }`

Estudio
- Flashcards: `GET /api/study/flashcards?dir=es2qu|qu2es&limit=20`
- Quiz: `GET /api/study/quiz?dir=es2qu|qu2es&limit=10&options=4`

## Formatos de datos

Importación CSV
- Formato esperado (sin encabezados): `español,kichwa`
- Codificación preferida: UTF-8 (la app intenta fallback a Latin-1)
- Duplicados dentro del archivo se omiten; actualiza si la clave en español ya existe con valor distinto.

Exportación
- JSON: `{ "dictionary": { "espanol": "kichwa", ... } }`
- CSV: pares `espanol,kichwa` ordenados por español.

Backups
- Se crean automáticamente antes y después de cambios masivos (incluye metadatos: versión, entradas, timestamps).

## Reglas para añadir palabras (UI, API y CSV)

Este sistema aplica reglas coherentes al agregar/editar/importar para mantener la calidad del diccionario:

- Clave en español
  - Se guarda en minúsculas y con espacios tal cual fueron escritos (se usa como clave única).
  - En la UI y API (`/api/dictionary/add|update`) se hace `trim()` y `lower()` al español.

- Valor en Kichwa
  - Se guarda tal como se escribe (sin forzar a minúsculas). Se recomienda usar `ñ` cuando corresponda y guiones `-` para separar morfemas/sufijos (ej. `mikuy-pak`).
  - La búsqueda/heurística normaliza tildes (las quita) pero conserva `ñ`.

- Coincidencias y traducción
  - Español → Kichwa: se priorizan coincidencias por frases más largas; se usa normalización (tildes fuera, `ñ` preservada) y guiones normalizados a uno.
  - Kichwa → Español: se tokeniza el texto en morfemas y se intentan sustituciones por tokens exactos normalizados. Usar guiones en el Kichwa ayuda a mejorar la segmentación.

- Importación CSV (`/api/dictionary/import`)
  - Formato: sin cabecera; cada fila `español,kichwa` (2 columnas mínimas). UTF-8 preferido (hay fallback a Latin-1). Se elimina BOM si existe.
  - Filas inválidas (vacías, con menos de 2 columnas, o con español/kichwa vacío) se omiten.
  - Duplicados dentro del mismo archivo (misma pareja `español,kichwa`) se omiten y se cuentan como `skipped_duplicates`.
  - Si la clave en español ya existe:
    - Si el valor es idéntico, se marca como duplicado y se omite.
    - Si el valor es distinto, se ACTUALIZA y se registra en el historial como `bulk-update`.
  - Si la clave en español no existe, se AGREGA y se registra como `bulk-add`.

- Edición/renombrado (`/api/dictionary/update`)
  - Puedes cambiar el Kichwa y opcionalmente renombrar la clave en español (`spanish_new`).
  - Se registra historial y se incrementa versión/meta.

- Buenas prácticas de modelado
  - Evita múltiples significados en un solo valor. Si necesitas variantes, puedes crear varias entradas con desambiguadores en español: `banco (dinero)`, `banco (asiento)`.
  - Usa guiones para morfemas/sufijos frecuentes en Kichwa. Ejemplos de sufijos que el sistema considera en la segmentación: `-mi`, `-shi`, `-ka`, `-ta`, `-n`, `-pak`, `-sapa`, `-kuna`.
  - Evita tildes en Kichwa (la normalización ya las quita en coincidencias); sí usa `ñ` cuando corresponda.

Cada operación que cambia el diccionario crea backup y actualiza metadatos (versión, conteo, última actualización) automáticamente.

## Estructura del proyecto

```
asistente_kichwa/
├── app.py                 # App Flask y endpoints
├── data/                  # Diccionario, backups, historial, meta
├── static/                # CSS, JS, imágenes, audio generado
├── templates/             # Vistas: index, diccionario, estudiar
├── requirements.txt       # Dependencias
└── README.md              # Este documento
```

## Solución de problemas

- TTS sin audio: verifica permisos de reproducción en el navegador y volumen del sistema. Para Kichwa se usa voz española.
- Importación CSV no avanza: confirma formato `espanol,kichwa`, codificación UTF-8/Latin-1 y que el archivo no esté vacío. Revisa consola del navegador y respuesta de `/api/dictionary/import`.
- ffmpeg no encontrado: instala desde `https://ffmpeg.org` y añade la carpeta `bin` al PATH. Endpoints de verificación: `GET /api/ffmpeg`.
- Transcripción remota: exporta `OPENAI_API_KEY` en la misma sesión donde ejecutas `python app.py`.

## Despliegue

- Modo producción: ejecuta la app detrás de un servidor WSGI (por ejemplo, Gunicorn) y un proxy inverso (Nginx). Configura variables de entorno y persiste la carpeta `data/` para no perder el diccionario ni los backups.
- Archivos estáticos: servir con cache control adecuado (versionado básico por nombre de archivo).

## Licencia y reconocimiento

Este proyecto es de código abierto (open source) y está destinado a fines educativos.

Autor: Jorge Doicela — GitHub: https://github.com/Jorge-Doicela
