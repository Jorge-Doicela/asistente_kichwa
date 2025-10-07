# Asistente Kichwa

Estructura mínima de la aplicación web con Flask.

Requisitos

- Python 3.8+
- Las dependencias aparecen en `requirements.txt`.

Instalación y uso (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5000 en tu navegador.

Probando el endpoint /speak

1. Inicia la aplicación:

```powershell
python app.py
```

2. En la interfaz principal escribe texto y pulsa "Generar audio". El frontend hará POST a `/speak` y reproducirá el MP3 devuelto.

3. También puedes probar con curl (PowerShell):

```powershell
curl -Method POST -ContentType 'application/json' -Body '{"text":"Hola desde Kichwa"}' http://127.0.0.1:5000/speak
```

Esto devolverá un JSON con la clave `url`, p. ej. { "url": "/static/audio/abcd1234.mp3" }.

Notas

- El servidor usa `gTTS` para generar el MP3. `gTTS` debe estar instalado (ya aparece en `requirements.txt`).
- Los archivos se guardan en `static/audio/`.
- Si usas un entorno virtual en Windows PowerShell, activa con `.`\`venv\Scripts\Activate.ps1`.

Recomendaciones siguientes:

- Añadir validación de idioma y parámetros de voz.
- Limpiar archivos antiguos en `static/audio/` según políticas de retención.
- Añadir tests unitarios para el endpoint `/speak`.
