# 📦 Import delle librerie necessarie
import time                 # Per misurare il tempo di esecuzione
import base64              # (non usata qui, ma utile per codificare dati binari come l'audio)
import requests            # Per inviare richieste HTTP (POST verso FastAPI)
import asyncio             # Per eseguire funzioni asincrone (necessario per synthesize_text_to_wav)

from pymongo import MongoClient                      # Per connettersi a MongoDB
from pymongo.server_api import ServerApi             # Per usare la Server API v1 di MongoDB

from concurrent.futures import ThreadPoolExecutor    # Per eseguire più thread in parallelo

# Import dei moduli personalizzati dal backend
from backend.llm_generator import generate_doctor_speech         # Genera un testo medico fittizio
from backend.text_to_speech import synthesize_text_to_wav        # Converte il testo in audio .wav

# 🔧 Configurazione
thread_number = 2  # Numero di thread/utenti da simulare
fastAPI_url = "http://localhost:8000/transcribe/"  # Endpoint FastAPI che riceve audio e restituisce trascrizione e dati strutturati

# 🔐 Connessione a MongoDB Atlas (⚠️ la password dovrebbe essere protetta in un file .env)
uri = "mongodb+srv://alessia00m:Password1234@cluster0.7if8c41.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))   # Crea client MongoDB
db = client["dati_clinici"]                            # Seleziona il database
collection = db["referti_ps"]                          # Seleziona la collezione dei referti

# 🧵 Funzione eseguita da ciascun thread
def thread_user(i):
    try:
        print(f"Thread {i} sta generando il referto")
        
        # 🧠 Genera un testo medico fittizio tramite LLM
        text = generate_doctor_speech()

        # 🗣️ Converte il testo in audio sintetico (.wav), funzione asincrona eseguita con asyncio
        path_audio = asyncio.run(synthesize_text_to_wav(text))

        print(f"Referto {i} generato, invio audio a /transcribe")

        # 📤 Invia l'audio a FastAPI per trascrizione
        with open(path_audio, "rb") as audio_file:
            files = {"file": ("audio.wav", audio_file, "audio/wav")}
            response = requests.post(fastAPI_url, files=files)

        # ✅ Se la risposta è valida (HTTP 200), processa il risultato
        if response.status_code == 200:
            result = response.json()
            referto = result.get("structured_data", {})

            # 💾 Se il referto è strutturato correttamente, lo salva in MongoDB
            if referto and "errore" not in referto:
                collection.insert_one(referto)
                print(f"Referto {i} salvato")

        else:
            # ❌ Se c'è stato un errore HTTP, lo segnala
            print(f"Thread {i}, errore http {response.status_code} - {response.text}")

    except Exception as e:
        # ❗ Gestione degli errori imprevisti
        print(f"Thread {i}: Errore durante la simulazione - {e}")

# 🚀 Avvio della simulazione multithread
if __name__ == "__main__":
    print(f"Simulazione di {thread_number} thread")
    start = time.time()  # ⏱ Inizio misurazione tempo

    # 🧵 Avvia un pool di thread concorrenti che eseguono thread_user
    with ThreadPoolExecutor(max_workers=thread_number) as executor:
        executor.map(thread_user, range(1, thread_number + 1))

    elapsed_time = time.time() - start  # ⏱ Fine misurazione tempo
    print(f"Simulazione completata, tempo impiegato {elapsed_time}s")
