# 🩺 Voice2Care — Trascrizione, Analisi e Simulazione di Referti Medici

Voice2Care è un'applicazione full-stack progettata per generare e gestire referti clinici tramite trascrizione vocale o simulazione automatica. 
Il progetto include un backend in FastAPI (con due modalità: API Hugging Face o modello locale faster-whisper) e un frontend in Streamlit.

---

🧠 Funzionalità principali

🎙️ Trascrizione vocale con Whisper (API o locale)
🧾 Estrazione automatica di JSON strutturato dai referti
🩺 Generazione simulata di discorsi medici
🔊 Sintesi vocale e aggiunta di rumore ambientale
🧠 Analisi NLP dei testi generati
🚨 Notifica "codice rosso" in tempo reale tramite Redis (es. integrazione Telegram)

---

## ⚙️ Installazione (VS Code Terminal)

### 1. Clonare il repository

git clone https://github.com/tuo-username/voice2care.git
cd voice2care

### 2. Crea un ambiente virtuale Python

Assicurati di usare Python 3.11 per il corretto funzionamento dei driver MongoDB

python3.11 -m venv .venv
source .venv/bin/activate  # (Linux/macOS)
.venv\Scripts\activate     # (Windows)

### 3. Installa le dipendenze

pip install -r requirements.txt

⚠️ Nota importante:
Il pacchetto av (richiesto da modello di faster-whisper) necessita di:

-FFmpeg installato sul sistema
-Strumenti di sviluppo: pkg-config, build-essential, Cython, gcc, ecc.

macOS

brew install ffmpeg
brew install pkg-config
pip install cython

Windows

1.Scarica FFmpeg e aggiungilo al PATH.
2.Installa il compilatore Visual C++ tramite Build Tools for Visual Studio
3.Installa Cython:

pip install cython


### 4. Configura le variabili d'ambiente

Crea un file .env partendo da quello di esempio .env.example fornito nel repository:

cp .env.example .env

Compila i valori mancanti (come HF_TOKEN, API_KEY_GEMINI, ecc.).


###5. ⚙️ Avvio del Backend

Hai due opzioni per avviare il backend FastAPI:

🔁 Opzione 1 — API Hugging Face (whisper-large-v3-turbo)
Usa questa modalità se vuoi evitare l’uso locale di modelli pesanti.

uvicorn backend.main_whisper_api:app --reload

⚡ Opzione 2 — Faster-Whisper (modello locale)
Usa questa modalità se hai risorse computazionali adeguate (es. GPU).

uvicorn backend.main_whisper_model:app --reload

Verifica che torch.cuda.is_available() sia True per sfruttare la GPU.

###6. 🎛️ Avvio del Frontend (Streamlit)

Lancia l’interfaccia utente:

streamlit run app.py



