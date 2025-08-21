import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename

# --- Configuración de Flask ---
app = Flask(__name__)

# Define los directorios para cada tipo de archivo
UPLOAD_FOLDER = 'uploads'
VIDEO_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, 'audio')
VIDEO_AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos-audios')

# Asegúrate de que los directorios existan
if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)
if not os.path.exists(VIDEO_AUDIO_FOLDER):
    os.makedirs(VIDEO_AUDIO_FOLDER)

# Extensiones permitidas para cada tipo
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No se encontró el archivo'}), 400
    
    file = request.files['file']
    upload_type = request.form.get('upload_type')

    if file.filename == '':
        return jsonify({'message': 'No se seleccionó ningún archivo'}), 400
    
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower()
    
    # Determina la carpeta de destino basada en el tipo de subida
    target_folder = None
    if upload_type == 'audio':
        if file_ext in ALLOWED_AUDIO_EXTENSIONS:
            target_folder = AUDIO_FOLDER
    elif upload_type == 'video':
        if file_ext in ALLOWED_VIDEO_EXTENSIONS:
            target_folder = VIDEO_FOLDER
    elif upload_type == 'video-audio':
        # Esta es la ruta para las grabaciones de pantalla
        if file_ext in ALLOWED_VIDEO_EXTENSIONS:
            target_folder = VIDEO_AUDIO_FOLDER
    
    if target_folder:
        filepath = os.path.join(target_folder, filename)
        file.save(filepath)
        print(f"Archivo guardado en: {filepath}")
        
        # Simular un resultado de procesamiento para la nueva página
        result_message = f"El archivo '{filename}' se ha procesado con éxito y se ha guardado en la carpeta '{os.path.basename(target_folder)}'."
        
        # Redirigir a la página de resultados con el mensaje
        return redirect(url_for('results', message=result_message))
    else:
        return jsonify({'message': 'Tipo de archivo no permitido o tipo de subida incorrecto'}), 400

@app.route('/results')
def results():
    message = request.args.get('message', 'No hay resultados para mostrar.')
    return render_template('results.html', result_message=message)
    
if __name__ == '__main__':
    app.run(debug=True)