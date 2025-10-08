# Asistente de Traducción Kichwa-Español

Aplicación web interactiva para traducción bidireccional entre Kichwa y Español, con soporte para entrada por voz, texto y archivos de audio.

![Logo de la aplicación](./static/img/logo.png)

## 🌟 Características Principales

- **Traducción Bidireccional**
  - Traducción instantánea Kichwa - Español
  - Diccionario local incorporado
  - Sistema de traducción fallback

- **Múltiples Métodos de Entrada**
  - 🎤 Grabación de voz en tiempo real
  - ⌨️ Entrada de texto manual
  - 📁 Subida de archivos de audio

- **Funciones Avanzadas**
  - 🔊 Síntesis de voz (TTS) para escuchar traducciones
  - 💾 Almacenamiento y gestión de archivos de audio
  - 📊 Panel de administración con estadísticas
  - 📚 Importación/exportación de diccionario

## 🛠️ Requisitos

  - Web Speech API
  - MediaRecorder API
  - Web Audio API
- Micrófono (para funciones de voz)

## Fallback sin ffmpeg (opcional)

Si no puedes instalar `ffmpeg`, la aplicación usa una API de transcripción remota. Para ello necesitas una clave de API y configurar una variable de entorno:

- Establece la variable `OPENAI_API_KEY` con tu clave.
- Opcionalmente, define `TRANSCRIBE_PROVIDER='openai'` (valor por defecto).

Ejemplo en PowerShell:

```powershell
$env:OPENAI_API_KEY = 'sk-xxxxx'
# Luego inicia la app en la misma terminal
python .\app.py
```

La app enviará el archivo de audio directamente a la API de transcripción y usará la respuesta si la conversión local falla.
- Tener descargado https://ffmpeg.org/ y añadido al path la carpeta 
  (ffmpeg-release-essentials.zip o .7z última versión)

## 📦 Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Jorge-Doicela/asistente_kichwa.git
   cd asistente_kichwa
   ```

2. **Crear entorno virtual**
   ```powershell
   # Windows
   (Es necesario tener activado la ejecución de scipts en powershell)
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

5. **Acceder a la aplicación**
   - Abre http://127.0.0.1:5000 en tu navegador

## 💡 Guía de Uso

### Traducción por Voz
1. Selecciona el idioma de entrada (Español/Kichwa)
2. Mantén presionado el botón de grabación
3. Habla claramente al micrófono
4. Suelta el botón para procesar
5. La traducción aparecerá automáticamente

### Traducción de Texto
1. Escribe o pega el texto en el área de entrada
2. Selecciona el idioma de origen
3. Haz clic en "Traducir" o presiona Enter
4. Usa el botón 🔊 para escuchar la traducción

### Procesamiento de Audio
1. Selecciona el archivo(s) de audio
2. Elige el idioma del audio
3. Haz clic en "Subir y Procesar"
4. Espera la traducción automática

## ⚙️ API REST

### Endpoints Principales

#### POST /translate
Traduce texto entre Kichwa y Español.
```json
{
  "text": "Texto a traducir",
  "src": "es",
  "dest": "qu"
}
```

#### POST /transcribe
Procesa archivos de audio y extrae texto.
```json
{
  "audio": "archivo_audio.mp3",
  "lang": "es"
}
```

#### POST /text-to-speech
Genera audio a partir de texto.
```json
{
  "text": "Texto para generar audio",
  "lang": "qu"
}
```

## ✨ Créditos

Desarrollado por Jorge Doicela.

## 📞 Contacto

- **Desarrollador**: Jorge Doicela
- **GitHub**: [@Jorge-Doicela](https://github.com/Jorge-Doicela)
- **Reportar Problemas**: [Issues](https://github.com/Jorge-Doicela/asistente_kichwa/issues)
