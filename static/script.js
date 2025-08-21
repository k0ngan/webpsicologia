const audioInput = document.getElementById('audioInput');
const uploadAudioButton = document.getElementById('uploadAudioButton');
const uploadAudioStatus = document.getElementById('uploadAudioStatus');

const videoInput = document.getElementById('videoInput');
const uploadVideoButton = document.getElementById('uploadVideoButton');
const uploadVideoStatus = document.getElementById('uploadVideoStatus');

const videoAudioInput = document.getElementById('videoAudioInput');
const uploadVideoAudioButton = document.getElementById('uploadVideoAudioButton');
const uploadVideoAudioStatus = document.getElementById('uploadVideoAudioStatus');

const startSharingButton = document.getElementById('startSharing');
const stopSharingButton = document.getElementById('stopSharing');
const startRecordingButton = document.getElementById('startRecording');
const stopRecordingButton = document.getElementById('stopRecording');
const videoPlayer = document.getElementById('videoPlayer');

let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];

// Función centralizada para la subida de archivos
function uploadFile(fileInput, uploadButton, uploadStatus, upload_type) {
    const files = fileInput.files;
    if (files.length === 0) {
        uploadStatus.textContent = 'Por favor, selecciona uno o más archivos.';
        uploadStatus.className = 'error';
        return;
    }

    if (files.length > 50) {
        uploadStatus.textContent = 'Puedes subir un máximo de 50 archivos a la vez.';
        uploadStatus.className = 'error';
        return;
    }

    uploadStatus.textContent = 'Iniciando subida...';
    uploadStatus.className = 'pending';
    uploadButton.disabled = true;

    let filesUploaded = 0;
    const totalFiles = files.length;

    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('upload_type', upload_type); // Enviar el tipo de carga

        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                uploadStatus.textContent = `Subiendo ${file.name}: ${percentComplete}% (${filesUploaded}/${totalFiles})`;
                uploadStatus.className = 'pending';
            }
        });

        xhr.addEventListener('load', () => {
            filesUploaded++;
            if (xhr.status === 200) {
                uploadStatus.textContent = `¡Archivo ${file.name} subido con éxito!`;
                uploadStatus.className = 'success';
            } else {
                uploadStatus.textContent = `Error al subir el archivo ${file.name}.`;
                uploadStatus.className = 'error';
            }
            if (filesUploaded === totalFiles) {
                uploadButton.disabled = false;
            }
        });

        xhr.addEventListener('error', () => {
            filesUploaded++;
            uploadStatus.textContent = `Error de red al subir el archivo ${file.name}.`;
            uploadStatus.className = 'error';
            if (filesUploaded === totalFiles) {
                uploadButton.disabled = false;
            }
        });

        xhr.open('POST', '/upload');
        xhr.send(formData);
    }
}

// Asignar la función a cada botón de subida
uploadAudioButton.addEventListener('click', () => uploadFile(audioInput, uploadAudioButton, uploadAudioStatus, 'audio'));
uploadVideoButton.addEventListener('click', () => uploadFile(videoInput, uploadVideoButton, uploadVideoStatus, 'video'));
uploadVideoAudioButton.addEventListener('click', () => uploadFile(videoAudioInput, uploadVideoAudioButton, uploadVideoAudioStatus, 'video-audio'));

// --- Manejo de la captura de pantalla y grabación ---
startSharingButton.addEventListener('click', async () => {
    try {
        mediaStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
        videoPlayer.srcObject = mediaStream;
        startSharingButton.style.display = 'none';
        stopSharingButton.style.display = 'inline';
        startRecordingButton.style.display = 'inline';
    } catch (error) {
        console.error('Error al compartir la pantalla:', error);
        alert('No se pudo compartir la pantalla. Por favor, revisa los permisos.');
    }
});

stopSharingButton.addEventListener('click', () => {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        videoPlayer.srcObject = null;
        startSharingButton.style.display = 'inline';
        stopSharingButton.style.display = 'none';
        startRecordingButton.style.display = 'none';
        stopRecordingButton.style.display = 'none';
        
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
    }
});

startRecordingButton.addEventListener('click', () => {
    if (!mediaStream) {
        alert('Por favor, primero inicia la transmisión de pantalla.');
        return;
    }

    recordedChunks = [];
    
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType: 'video/webm; codecs=vp9' });

    mediaRecorder.ondataavailable = event => {
        if (event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };

    mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunks, {
            type: 'video/webm'
        });
        
        const formData = new FormData();
        formData.append('file', blob, 'grabacion-pantalla.webm');
        formData.append('upload_type', 'video-audio'); // Etiqueta para el backend
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                console.log('Grabación enviada al servidor con éxito!');
            } else {
                console.error('Error al enviar la grabación al servidor.');
            }
        })
        .catch(error => {
            console.error('Error de red al enviar la grabación:', error);
        });
    };

    mediaRecorder.start();
    console.log('Grabación iniciada...');
    startRecordingButton.style.display = 'none';
    stopRecordingButton.style.display = 'inline';
});

stopRecordingButton.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        console.log('Grabación detenida.');
        startRecordingButton.style.display = 'inline';
        stopRecordingButton.style.display = 'none';
    }
});