# Rimaykuna — Asistente Kichwa ↔ Español

Aplicación web para traducir entre Kichwa y Español con soporte de voz, un diccionario editable y una sección de estudio con flashcards y quizzes. Ideal para cursos, universidades y comunidades que enseñan/aprenden Kichwa.

![Logo de la aplicación](./static/img/logo.png)

## 🌟 Qué incluye

- **Traducción bidireccional** (texto y voz) con heurísticas para Kichwa y fallback a traductor externo.
- **Diccionario local** editable: agregar/editar/eliminar, importar CSV y exportar.
- **Estudio**: flashcards y preguntas de opción múltiple usando el mismo diccionario.
- **Audio**: síntesis de voz (TTS) para escuchar resultados y tarjetas.
- **Backups y metadatos** del diccionario automáticamente.

## 🚀 Inicio rápido

1) Clona y entra al proyecto:
```bash
git clone https://github.com/Jorge-Doicela/asistente_kichwa.git
cd asistente_kichwa
```

2) Crea y activa un entorno virtual:
```powershell
# Windows (habilitar scripts en PowerShell si es necesario):
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

4) Ejecuta la aplicación:
```bash
python app.py
```

5) Abre en el navegador:
- `http://127.0.0.1:5000`

## 🧭 Secciones principales

- **Traductor (Inicio)**: entrada por texto o audio, detección de idioma básica y TTS.
- **Diccionario** (`/diccionario`): buscar, ordenar, paginar y gestionar términos. Importa CSV (formato: `español,kichwa`) y exporta CSV/JSON. Consulta metadatos, historial y backups.
- **Estudiar** (`/estudiar`):
  - Flashcards: `ES → QU` o `QU → ES` con botones para mostrar respuesta y escuchar pronunciación.
  - Quiz: preguntas con opciones (generadas a partir del diccionario).

## 🛠 Requisitos y notas

- Micrófono para funciones de voz (opcional).
- Navegador moderno con Web Audio API.
- Para procesar audios en más formatos localmente, se recomienda instalar `ffmpeg` y añadirlo al PATH del sistema.

### Si no tienes ffmpeg (fallback opcional)

La app puede intentar transcripción remota si la conversión local falla. Configura una clave y variable de entorno:

- `OPENAI_API_KEY`: tu clave de API.
- `TRANSCRIBE_PROVIDER='openai'` (opcional, por defecto `openai`).

Ejemplo en PowerShell:
```powershell
$env:OPENAI_API_KEY = 'sk-xxxxx'
python .\app.py
```

Nota: la voz Kichwa no está soportada por gTTS; el sistema hace fallback a voz en español para reproducir palabras Kichwa.

## 📚 API (resumen)

- `POST /translate` — Traducción texto a texto.
- `POST /transcribe` — Transcripción de audio (archivo o grabación).
- `POST /text-to-speech` — Síntesis de voz (devuelve URL de MP3).
- Diccionario REST:
  - `GET /api/dictionary` — Obtener diccionario.
  - `POST /api/dictionary/add` — Agregar término.
  - `POST /api/dictionary/update` — Actualizar/renombrar término.
  - `POST /api/dictionary/delete` — Eliminar término.
  - `POST /api/dictionary/import` — Importar CSV.
  - `GET /api/dictionary/export?format=json|csv` — Exportar.
  - `GET /api/dictionary/meta|history|backups` y `POST /api/dictionary/restore`.
- Estudio:
  - `GET /api/study/flashcards?dir=es2qu|qu2es&limit=30`
  - `GET /api/study/quiz?dir=es2qu|qu2es&limit=10&options=4`

## 🗂 Estructura del proyecto

```
asistente_kichwa/
├── app.py                 # App Flask y endpoints
├── data/                  # Diccionario, backups, historial
├── static/                # CSS, JS, imágenes, audio generado
├── templates/             # Vistas: index, diccionario, estudiar
├── requirements.txt       # Dependencias
└── README.md              # Este documento
```

## 🔎 Solución de problemas

- "No se escucha audio" (TTS): verifica que el navegador permita reproducir audio y el volumen. Para Kichwa, se usa voz española como fallback.
- Importación CSV falla: asegúrate de formato `español,kichwa` y codificación UTF-8 (o intenta Latin-1). El import aplica actualizaciones en masa y registra historial.
- ffmpeg no encontrado: instala desde `https://ffmpeg.org` y agrega su binario al PATH. En Windows, descarga “essentials” y añade la carpeta `/bin`.
- Transcripción remota: confirma que `OPENAI_API_KEY` esté configurada en la misma terminal donde ejecutas `python app.py`.

## 📄 Licencia y uso

Este proyecto está destinado a fines educativos y de apoyo a comunidades Kichwa. Ajusta la licencia según tus necesidades institucionales (añádela si corresponde).

## 👤 Créditos y contacto

- Desarrollado por: Jorge Doicela
- GitHub: [@Jorge-Doicela](https://github.com/Jorge-Doicela)
- Reportar problemas: Issues del repositorio
