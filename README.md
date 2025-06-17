# 🩺 Voice2Care — Trascrizione, Analisi e Simulazione di Referti Medici

Nel settore sanitario, specialmente in situazioni di emergenza, il personale medico è spesso costretto a trascrivere manualmente note cliniche — un’attività:

- ⏱️ Lenta e dispendiosa in termini di tempo
- ⚠️ Soggetta a errori umani
- 🔗 Non integrata nei flussi digitali moderni

**Voice2Care** è un'applicazione full-stack progettata per automatizzare e semplificare la generazione, l’analisi e la gestione dei referti clinici, attraverso l’utilizzo di tecnologie moderne di speech-to-text, intelligenza artificiale generativa (LLM) e interfacce web interattive.

Il sistema consente al personale sanitario di:

- 🎙️ Trascrivere automaticamente note cliniche dettate a voce
- 🧾 Estrarre strutture dati cliniche (in formato JSON) da testi non strutturati
- 🖥️ Visualizzare, modificare e validare i referti attraverso una dashboard user-friendly
- 🔊 Generare in voce naturale i referti clinici simutali, tramite supporto per sintesi vocale e simulazione di ambienti reali con rumore di fondo
- 📄 Generare automaticamente PDF strutturati dei referti pronti per l’archiviazione o la stampa
- 🚨 Ricevere notifiche in tempo reale in caso di criticità (es. codice rosso)
- 📊 Visualizzare analitiche e statistiche aggregate sui dati clinici


Tutto ciò avviene in un ambiente modulare e scalabile, costruito su:

- 🧠 Backend in FastAPI, che gestisce la logica di business, la trascrizione e l’interazione con i modelli LLM
- 🖥️ Frontend in Streamlit, che fornisce una dashboard interattiva e facile da usare
- 🗂️ Database MongoDB, per l’archiviazione efficiente e strutturata dei dati clinici

Voice2Care nasce dunque per ridurre il carico cognitivo del personale sanitario, minimizzare gli errori legati alla documentazione manuale e aumentare l'efficienza operativa, con un focus particolare su contesti ad alta criticità come il Pronto Soccorso.

## ⚙️ Installazione (Terminale VS Code)

### 1. Clona il repository

```bash
git clone https://github.com/simo26/voice2care.git
cd voice2care
```
### 2. Creazione ed attivazione di un ambiente virtuale Python

Assicurati di usare Python 3.11 per il corretto funzionamento dei driver MongoDB di Atlas

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # (Linux/macOS)
.venv\Scripts\activate     # (Windows)
```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

⚠️ Nota importante:
Il pacchetto av (richiesto da modello di faster-whisper) necessita di:

- FFmpeg installato sul sistema
- Strumenti di sviluppo: pkg-config, build-essential, Cython, gcc, ecc.

macOS:

```bash
brew install ffmpeg
brew install pkg-config
pip install cython
```

Windows:

1.Scarica FFmpeg e aggiungilo al PATH.
2.Installa il compilatore Visual C++ tramite Build Tools for Visual Studio
3.Installa Cython:

```bash
pip install cython
```

### 4. Configura le variabili d'ambiente

Crea un file `.env` partendo da quello di esempio `.env.example` fornito nel repository:

```bash
cp .env.example .env  # Su macOS
copy .env.example .env  # Su Windows (cmd)
```

Compila i valori mancanti (come HF_TOKEN, API_KEY_GEMINI, ecc.).

### 5. ⚙️ Avvio del Backend

Hai due opzioni per avviare il backend FastAPI:

🔁 **Opzione 1 — API Hugging Face (whisper-large-v3-turbo)**  
Usa questa modalità se vuoi evitare l’uso locale di modelli pesanti.

```bash
uvicorn backend.main_whisper_api:app --reload
```

⚡ **Opzione 2 — Faster-Whisper (modello locale)**
Usa questa modalità se hai risorse computazionali adeguate (es. GPU).

```bash
uvicorn backend.main_whisper_model:app --reload
```

Verifica che torch.cuda.is_available() sia True per sfruttare la GPU.

### 6. 🎛️ Avvio del Frontend (Streamlit)

Lancia l’interfaccia utente:

```bash
streamlit run app.py
```



