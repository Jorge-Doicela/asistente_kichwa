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

Ejemplo (PowerShell):
```powershell
$env:OPENAI_API_KEY = 'sk-xxxxx'
python .\app.py
```

Nota sobre TTS: gTTS no soporta voces Kichwa; se usa español como aproximación cuando `lang` es Kichwa.

## Uso de la aplicación

- Inicio (Traductor): ingresa texto o usa micrófono, la app detecta idioma (heurística) y traduce; puedes reproducir el resultado con TTS.
- Diccionario (`/diccionario`): busca, ordena, pagina, agrega/edita/elimina términos. Importa CSV (`español,kichwa`) y exporta CSV/JSON. Consulta metadatos, historial y backups.
- Estudiar (`/estudiar`): practica con flashcards (ES→QU / QU→ES) o quizzes de opción múltiple.

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
