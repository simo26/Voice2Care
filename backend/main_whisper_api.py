# Moduli standard
from datetime import date, datetime
import os
import tempfile
import shutil
import time
import traceback
import base64
import json
import requests

# Moduli FastAPI
from fastapi import FastAPI, UploadFile, File

# Librerie esterne
import redis

# Per caricare le variabili d'ambiente dal file .env
from dotenv import load_dotenv  

# Moduli locali
from backend.llm_parser import extract_json_from_transcription
from backend.llm_generator import generate_doctor_speech
from backend.text_to_speech import synthesize_text_to_wav, add_noise


# Carica le variabili dal file .env
load_dotenv()

# Leggi la varibile di ambiente del Token di autorizzazione per il provider Hugging Face
HF_TOKEN = os.getenv("HF_TOKEN")


# CONFIGURAZIONE REDIS

# Inizializzo il client Redis
# Redis viene utilizzato qui per notificare in tempo reale eventuali "codici rossi" (emergenze mediche critiche)
r = redis.Redis(
    host='localhost',  # Host del server Redis (localhost)
    port=6379,         # Porta di default per Redis
    db=0               # Database Redis selezionato (0 è predefinito)
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
            print("[Redis] Connessione attiva, sistema di notifiche attivo.")
            serialized = json.dumps(structured_data, default=serialize_dates)
            r.publish("codice_rosso", serialized)

        except redis.ConnectionError as e:
            print(f"[Redis ERROR] Connessione fallita: {e}")
            return  # Interrompe la funzione senza notificare nulla




# Base path del progetto
BASE_DIR = os.path.dirname(__file__)

# Path del file audio di rumore da aggiungere
path_noise = os.path.join(BASE_DIR, "audio", "noise.wav")


# CONFIGURAZIONE WHISPER API

# Endpoint Hugging Face per Whisper
API_URL = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo"

# Token di autorizzazione per il provider hf-inference
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
}


# CREAZIONE DELL'APP FASTAPI
app = FastAPI()


# funzione per chiamata al modello Whisper via API
def query(filename):
    try:
        #Invia un file audio a Whisper (API Hugging Face) e ritorna la trascrizione 
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File non trovato: {filename}")
        with open(filename, "rb") as f:
            data = f.read()
        response = requests.post(
            API_URL,
            headers={"Content-Type": "audio/wav", **headers},
            data=data
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Errore nella richiesta HTTP: {e}")
    except Exception as e:
        raise Exception(f"Errore durante la trascrizione con Whisper: {e}")


# ENDPOINT /transcribe/
#riceve un file audio caricato dall’utente e restituisce la trascrizione e dati strutturati in json, 
# evuntalmente notificando via Redis in caso di emergenza medica (codice rosso)
@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    # Salva il file ricevuto temporaneamente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        shutil.copyfileobj(file.file, temp_audio_file)
        temp_audio_path = temp_audio_file.name

    try:
        start_time = time.time()

        # Trascrive l'audio con Whisper
        output_whisper = query(temp_audio_path)
        transcription = output_whisper["text"]

        # Estrae dati strutturati dal testo trascritto
        structured_data = extract_json_from_transcription(transcription)

        # Notifica eventuale codice rosso a Redis
        notify_red_code(structured_data)

        # Log di performance e output
        print("tempo impiegato per la trascrizione:", time.time() - start_time)
        print("trascrizione:", transcription)
        print("structured_data:", structured_data, "\n")

        # Risposta JSON
        return {
            "transcription": transcription,
            "structured_data": structured_data
        }

    finally:
        # Elimina il file temporaneo
        os.remove(temp_audio_path)



# ENDPOINT /generate_synthetic/
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

        # Trascrive l’audio sintetico con Whisper
        output_whisper = query(path_audio)
        testo_trascritto = output_whisper["text"]

        # Estrae dati strutturati dal testo trascritto
        structured_data = extract_json_from_transcription(testo_trascritto)
        # Notifica eventuale codice rosso a Redis
        notify_red_code(structured_data)

        # Codifica l’audio in base64 per inviarlo nel JSON
        with open(path_audio, "rb") as audio_file:
            audio_bytes = audio_file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Risposta JSON
        return {
            "text_original": testo_originale,
            "transcription": testo_trascritto,
            "structured_data": structured_data,
            "audio_base64": audio_b64
        }

    except Exception as e:
        traceback.print_exc()  # Log dettagliato in caso di errore
        return {"errore": str(e)}
