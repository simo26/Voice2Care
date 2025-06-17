#moduli standard
from datetime import date, datetime
import os
import tempfile
import shutil
import time
import traceback
import base64
import json

#moduli fastapi
from fastapi import FastAPI, UploadFile, File

#librerie esterne
from faster_whisper import WhisperModel
import torch
import redis

#moduli locali
from backend.llm_parser_api import extract_json_from_transcription
from backend.llm_generator import generate_doctor_speech
from backend.text_to_speech import synthesize_text_to_wav, add_noise


#     CONFIGURAZIONE REDIS

# Inizializzo il client Redis
# Redis viene utilizzato per notificare in tempo reale eventuali "codici rossi" (emergenze mediche critiche)
r = redis.Redis(
    host='localhost',  # Host del server Redis
    port=6379,         # Porta di default per Redis
    db=0               # Database Redis selezionato
)

# Funzione per serializzare oggetti `date` e `datetime` in JSON
def serialize_dates(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()  # es. "YYYY-MM-DD"
    raise TypeError(f"Tipo non serializzabile: {type(obj)}")

# Funzione per pubblicare un evento su Redis se il codice d’urgenza è "R" (rosso)
def notify_red_code(structured_data):
    code = structured_data.get("chiamata_ps", {}).get("codice_uscita") or {}
    if code.get("R"):
        try:
            # Verifica se la connessione Redis è attiva
            if not r.ping():
                print("[Redis] Connessione non attiva, sistema di notifiche non attivo.")
                return

            # Serializza i dati e pubblica sul canale Redis
            serialized = json.dumps(structured_data, default=serialize_dates)
            r.publish("codice_rosso", serialized)

        except redis.ConnectionError as e:
            print(f"[Redis ERROR] Connessione fallita: {e}")
            return  # Interrompe la funzione senza notificare nulla


#  CONFIGURAZIONE MODELLI E PATH

# Base path del progetto
BASE_DIR = os.path.dirname(__file__)

# Path del file audio di rumore da aggiungere
path_noise = os.path.join(BASE_DIR, "audio", "noise.wav")

# Determina il device disponibile: CUDA (GPU) o CPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# Se uso la GPU, uso float16 per maggiore velocità, altrimenti int8 per CPU
compute_type = "float16" if device == "cuda" else "int8"

# Inizializza il modello FasterWhisper
# Uso il modello "medium" per bilanciare qualità e uso di memoria
model = WhisperModel("medium", device=device, compute_type=compute_type)


# CREAZIONE APP FASTAPI
app = FastAPI()

# Informazioni sul dispositivo in uso
print("Verifica CUDA")
print("CUDA disponibile:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Dispositivo:", torch.cuda.get_device_name(0))
else:
    print("CUDA non disponibile")


#ENDPOINT /transcribe/
#riceve un file audio caricato dall’utente e restituisce la trascrizione e dati strutturati in json, 
# evuntalmente notificando via Redis in caso di emergenza medica (codice rosso)
@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    # Salva temporaneamente il file audio ricevuto
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        shutil.copyfileobj(file.file, temp_audio_file)
        temp_audio_path = temp_audio_file.name

    try:
        start_time = time.time()

        # Trascrizione con FasterWhisper
        segments, info = model.transcribe(temp_audio_path)
        transcription = "".join(s.text for s in segments)

        # Estrazione JSON da trascrizione
        structured_data = extract_json_from_transcription(transcription)

        # Notifica codice rosso (se presente)
        notify_red_code(structured_data)

        print("tempo impiegato per la trascrizione:", time.time() - start_time)
        print("trascrizione:", transcription)
        print("structured_data:", structured_data, "\n")

        return {
            "transcription": transcription.strip(),
            "language": info.language,
            "structured_data": structured_data
        }

    finally:
        # Rimuove il file temporaneo
        os.remove(temp_audio_path)


#  ENDPOINT /generate_synthetic/
#genera un discorso medico fittizio, lo trasforma in audio sintetico, vi aggiunge rumore ambientale, lo trascrive 
# e restituisce testo, audio e dati strutturati, evuntalmente notificando via Redis in caso di emergenza medica (codice rosso)
@app.post("/generate_synthetic/")
async def generate_synthetic():
    try:
        # Genera un testo medico simulato
        testo_originale = generate_doctor_speech()
        print("Testo generato:", testo_originale)

        # Sintetizza audio dal testo
        path_audio = await synthesize_text_to_wav(testo_originale)

        # Aggiunge rumore di fondo all'audio sintetico
        add_noise(path_audio, path_noise, path_audio, noise_db=-2)
        print("Dimensione file audio (MB):", os.path.getsize(path_audio) / 1e6)

        # Trascrive l’audio con FasterWhisper
        segments, info = model.transcribe(path_audio)
        testo_trascritto = "".join(s.text for s in segments)

        # Estrae dati strutturati dal testo trascritto
        structured_data = extract_json_from_transcription(testo_trascritto)

        # Notifica codice rosso (se presente)
        notify_red_code(structured_data)

        # Codifica audio in base64 per risposta JSON
        with open(path_audio, "rb") as audio_file:
            audio_bytes = audio_file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        return {
            "text_original": testo_originale,
            "transcription": testo_trascritto,
            "structured_data": structured_data,
            "audio_base64": audio_b64
        }

    except Exception as e:
        traceback.print_exc()
        return {"errore": str(e)}
