import streamlit as st  # Framework Streamlit per la creazione di interfacce web interattive
import requests  # Per effettuare richieste HTTP 
import base64  # Per codifica/decodifica dati in Base64 
from pymongo import MongoClient  # Per connettersi a MongoDB
from pymongo.server_api import ServerApi  # Per specificare la versione dell’API del server MongoDB
from streamlit_modal import Modal  # Per gestire finestre modali (popup) in Streamlit
import pandas as pd  # Per manipolazione dati in formato tabellare
import matplotlib.pyplot as plt  # Per generare grafici statici
import altair as alt  # Per creare grafici interattivi in Streamlit
from passlib.hash import bcrypt  # Per la cifratura delle password
import time as t  # modulo time
from datetime import datetime, date, time  #Per gestire date e orari
import os

from utilities import genera_pdf, clean_value  # Funzioni personalizzate per generazione PDF e pulizia dati

from dotenv import load_dotenv  # Per caricare le variabili d'ambiente dal file .env

# Carica le variabili dal file .env
load_dotenv()

# Leggi la varibile di ambiente dell'API Key per Gemini 
DB_PASSWORD = os.getenv("DB_PASSWORD")

#Collegamento al database MongoDB Atlas

# URI di connessione a MongoDB Atlas (contiene username, password, host, e opzioni)
uri = f"mongodb+srv://alessia00m:{DB_PASSWORD}@cluster0.7if8c41.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Crea un client MongoDB specificando l'API del server
client = MongoClient(uri, server_api=ServerApi('1'))

# Seleziona il database "dati_clinici"
db = client["Voice2Care"]

# Seleziona la collezione "pazienti" (documenti relativi ai pazienti)
pazienti_collection = db["pazienti"]

# Seleziona la collezione "interventi" (documenti relativi a interventi clinici o di emergenza)
interventi_collection = db["referti_ps"]



#Inizializzo MODALE Streamlit per visualizzare dati del referto
modal = Modal(title="Dettagli Referto", key="modal")



# Dizionario che definisce i campi attesi per ogni sezione del referto clinico,
# utilizzato per guidare la visualizzazione strutturata e coerente dei dati nell’interfaccia utente
expected_fields = {
    "chiamata_ps": ["data", "luogo_intervento", "condizione_riferita", "ora_chiamata", "ora_arrivo_ps", "codice_uscita"],
    "autorita_presenti": ["carabinieri", "polizia_municipale", "polizia_stradale", "vigili_del_fuoco", "guardia_medica", "altra_ambulanza"],
    "dati_paziente": ["nome", "cognome", "sesso", "eta", "data_nascita", "luogo_nascita", "residenza"],
    "parametri_vitali": ["pressione", "battito", "saturazione", "coscienza", "cute", "respiro"],
    "provvedimenti": ["respiro", "circolo", "immobilizzazione", "altro", "farmaci"]
}



# Funzione per la visualizzazione delle sezioni del referto clinico all'interno della modale.
def render_section(title, data_dict, expected_keys=None, cols_per_row=2):
    st.markdown(f"### {title.replace('_', ' ').capitalize()}")

    # Se la sezione è "Autorità Presenti", si vuole mostrare solo le chiavi il cui valore è True
    if "Autorità Presenti" in title:
        # Costruisci una lista delle chiavi in expected_keys che hanno valore True in data_dict
        true_keys = [k for k in expected_keys if data_dict.get(k) is True]
        # Se ci sono chiavi True, le stampo tutte insieme separate da virgola, con la prima lettera maiuscola e underscore sostituiti da spazio
        if true_keys:
            st.markdown(", ".join([k.replace('_', ' ').capitalize() for k in true_keys]))
        else:
            # Se nessuna autorità è presente
            st.markdown("Nessuna autorità presente")
        # Termino la funzione
        return

    # Se expected_keys non è stato fornito, usa tutte le chiavi presenti in data_dict
    if expected_keys is None:
        expected_keys = list(data_dict.keys())

    # Prepara un nuovo dizionario per contenere i valori puliti da visualizzare
    display_dict = {}
    # Per ogni chiave prevista, recupero il valore dal dizionario dati e lo pulisce tramite clean_value
    for key in expected_keys:
        val = data_dict.get(key, None)
        display_dict[key] = clean_value(val)

    # Lista delle chiavi da visualizzare
    keys = list(display_dict.keys())
    # Itera sulle chiavi a blocchi della dimensione del numero di colonne per riga
    for i in range(0, len(keys), cols_per_row):
        # Creo le colonne Streamlit in cui visualizzare i dati
        cols = st.columns(cols_per_row)
        # Per ogni colonna 
        for j in range(cols_per_row):
            # Controllo che non si superi il numero totale di chiavi
            if i + j < len(keys):
                key = keys[i + j]
                val = display_dict[key]
                # Visualizza la chiave (formattata con la prima lettera maiuscola e underscore sostituiti da spazio) e il valore corrispondente in markdown all’interno della colonna
                cols[j].markdown(f"**{key.replace('_', ' ').capitalize()}**: {val}")





#LOGIN UTENTE
if "utente" not in st.session_state: #se l'utente non è ancora loggato, si va al form di login
    st.title("🔐 Login Voice2Care")
    email = st.text_input("Email") #campo input della mail 
    password = st.text_input("Password", type="password") #campo input password

    if st.button("Accedi"): #se viene cliccato il tasto accedi si cerca nel database "utenti" la mail inserita
        utenti = db["operatori_sanitari"]
        user = utenti.find_one({"email": email})
        if user and bcrypt.verify(password, user["password_hash"]): #se l'utente esiste e la password coincide con l'hash salvato nel database
            st.session_state["utente"] = user #viene salvato l'utente nella sessione e si passa alla pagina principale
            st.success("Accesso riuscito. Benvenuto!")
            st.rerun()
        else: #altrimenti dai warning di credenziali errate
            st.error("Credenziali errate.")
    st.stop()



#CONFIGURAZIONE PAGINA WEB
st.set_page_config(page_title="Voice2Care", layout="wide", page_icon = "https://raw.githubusercontent.com/alessiamanna/big_data_project/refs/heads/main/health-8.png")
st.sidebar.title("Voice2Care Dashboard")

if "utente" in st.session_state:
    st.sidebar.markdown(f"Loggato come: {st.session_state['utente']['nome']} {st.session_state['utente']['cognome']}") #prendi nome e cognome dell'utente della sessione
    if st.sidebar.button("🔓 Logout"): #esci 
        st.session_state.clear()
        st.rerun()
else:
    st.sidebar.warning("⚠️ Utente non loggato")



#SIDEBAR DI NAVIGAZIONE
st.sidebar.markdown("<h2 style='font-size: 24px; margin-top: 15px;'>🔍 Navigazione</h2>", unsafe_allow_html=True)
page = st.sidebar.radio(label="a", options=["Home", "Nuovo Referto", "Visualizza Referti", "Analitiche Avanzate"], label_visibility="collapsed")



#SEZIONE "HOME"
if page == "Home":
    st.title("Voice2Care 🩺")
    st.markdown("""
    Benvenuto nella dashboard **Voice2Care**, uno strumento progettato per supportare i medici nella gestione dei referti clinici.

    Tramite questa interfaccia potrai:
    
    - 📄 **Nuovo Referto**: generare un referto a partire da una registrazione vocale del medico, oppure – a fini didattici – simulare un'audio con informazioni cliniche e trasformarlo in un referto strutturato, memorizzabile nel database *dati clinici*.
    - 📂 **Visualizza Referti**: consultare i referti archiviati, applicare filtri, visualizzarne i dettagli e scaricare un PDF strutturato.
    - 📊 **Analitiche Avanzate**: esplorare statistiche aggregate sui referti tramite grafici, come la distribuzione dei codici di uscita o l'andamento degli interventi nel tempo.

    La piattaforma combina funzionalità AI di trascrizione e generazione con strumenti per l'analisi e l'archiviazione sicura dei dati.

    Il progetto è consultabile al seguente link: 
    """)



#SEZIONE "NUOVO REFERTO"
elif page == "Nuovo Referto":
    st.header("📁 Nuovo Referto")

    # Inizializzo lo stato per tracciare l'opzione corrente
    if "last_option" not in st.session_state:
        st.session_state["last_option"] = None

    # Radio button per upload o generazione sintesi vocale
    option = st.radio("Modalità di inserimento", ["Carica Audio", "Genera Referto Sintetico"])

    # Se è cambiata la modalità, si resetta il form del referto
    if st.session_state["last_option"] != option:
        st.session_state["last_option"] = option
        st.session_state.pop("structured_data", None)


    if option == "Carica Audio": #opzione per la generazione del referto traomite caricamento del file audio
        uploaded_file = st.file_uploader("Carica un file audio", type=["wav", "mp3", "m4a", "ogg"])
        if uploaded_file and st.button("Trascrivi Audio"):
            with st.spinner("Trascrizione in corso..."):
                files = {"file": ("audio.wav", uploaded_file.read(), "audio/wav")}
                response = requests.post("http://localhost:8000/transcribe/", files=files) #fai la post alla trascrizione
                if response.status_code == 200: #se la post va a buon fine 
                    data = response.json() #restituisce un dizionario python, quindi posso trattare data come un normale dict
                    st.session_state["structured_data"] = data["structured_data"] #salvo lo stato della sessione
                    st.success("Trascrizione completata!")
                else:
                    st.error("Errore nella trascrizione.")

    elif option == "Genera Referto Sintetico": #opzione per la generazione del referto automatica che dà il via alla sintesi vocale
        if st.button("Genera Referto Automatico"):
            with st.spinner("Generazione e trascrizione..."):
                response = requests.post("http://localhost:8000/generate_synthetic/") #fai la post alla generazione dell'audio sintetico
                if response.status_code == 200:
                    data = response.json()
                    st.session_state["structured_data"] = data["structured_data"]
                    st.audio(base64.b64decode(data["audio_base64"]), format="audio/wav") #per riprodurre nella GUI l'audio generato
                    st.success("Referto generato con successo!")
                else:
                    st.error("Errore nella generazione del referto.")

    if "structured_data" in st.session_state: #verifica se c'è uno structured_data (quindi il json) già salvato
        st.subheader("📝 Modifica Referto Estratto")
        d = st.session_state["structured_data"]

        #definizione di tutti i campi di testo e le checkbox necessarie per implementare l'interfaccia in modo tale che sia quanto più fedele possibile al foglio di ps 
        st.markdown("### Chiamata e Arrivo in PS")

        chiamata_ps = d.get("chiamata_ps") or {}
        # recupero il valore della data di chiamata, convertentendolo se necessario, settando come valore default la data odierna
        data_raw = chiamata_ps.get("data", "")
        if isinstance(data_raw, str):
            try:
                default_date = datetime.strptime(data_raw, "%Y-%m-%d").date()
            except ValueError:
                default_date = date.today()
        elif isinstance(data_raw, date):
            default_date = data_raw
        else:
            default_date = date.today()

        col1, col2 = st.columns(2)
        with col1:
            #widget per la data
            data_chiamata = st.date_input("Data", value=default_date)
        with col2:
            ora_chiamata = st.text_input("Ora Chiamata", value=chiamata_ps.get("ora_chiamata", ""))

        col3, col4 = st.columns(2)
        with col3:
            ora_arrivo_ps = st.text_input("Ora Arrivo PS", value=chiamata_ps.get("ora_arrivo_ps", ""))
        with col4:
            luogo_intervento = st.text_input("Luogo Intervento", value=chiamata_ps.get("luogo_intervento", ""))

        condizione_riferita = st.text_input("Condizione Riferita", value=chiamata_ps.get("condizione_riferita", ""))
        opzioni_codice = {
            "B": "Codice B",
            "V": "Codice V",
            "G": "Codice G",
            "R": "Codice R"
        }

        codice_uscita = (chiamata_ps or {}).get("codice_uscita") or {}
        valore_corrente = next((k for k, v in codice_uscita.items() if v), None)


        # Radio button verticale per modificare il codice di uscita
        scelta = st.radio("codice uscita", list(opzioni_codice.keys()),
                    format_func=lambda x: opzioni_codice[x],
                    index=list(opzioni_codice.keys()).index(valore_corrente) if valore_corrente else 0,
                    horizontal=True
                    )

        #imposta il dizionario di uscita con solo la chiave selezionata a True
        codice_uscita = {k: (k == scelta) for k in opzioni_codice}

        st.markdown("<br>", unsafe_allow_html=True)  # riga vuota

        st.markdown("### Autorità Presenti")
        col1, col2, col3 = st.columns(3)

        autorita = d.get("autorita_presenti") or {} 

        with col1:
            carabinieri = st.checkbox("Carabinieri", value=autorita.get("carabinieri", False))
            polizia_municipale = st.checkbox("Polizia Municipale", value=autorita.get("polizia_municipale", False))

        with col2:
            polizia_stradale = st.checkbox("Polizia Stradale", value=autorita.get("polizia_stradale", False))
            vigili_del_fuoco = st.checkbox("Vigili del Fuoco", value=autorita.get("vigili_del_fuoco", False))

        with col3:
            guardia_medica = st.checkbox("Guardia Medica", value=autorita.get("guardia_medica", False))
            altra_ambulanza = st.checkbox("Altra Ambulanza", value=autorita.get("altra_ambulanza", False))


        st.markdown("<br>", unsafe_allow_html=True)  # riga vuota


        paziente = d.get("paziente") or {}
        data_nascita_raw = paziente.get("data_nascita", "")
        if isinstance(data_nascita_raw, str):
            try:
                default_date_nascita = datetime.strptime(data_nascita_raw, "%Y-%m-%d").date()
            except ValueError:
                default_date_nascita = date.today()
        elif isinstance(data_nascita_raw, date):
            default_date_nascita = data_nascita_raw
        else:
            default_date_nascita = date.today()

        st.markdown("### Dati Paziente")
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome", value=paziente.get("nome", ""))
        with col2:
            cognome = st.text_input("Cognome", value=paziente.get("cognome", ""))

        col3, col4, col5 = st.columns(3)
        with col3:
            sesso_val = paziente.get("sesso")
            if sesso_val in ["M", "F"]: 
                sesso = st.selectbox("Sesso", ["M", "F"], index=0 if sesso_val == 'M' else 1)
            else:
                sesso = st.selectbox("Sesso", ["M", "F"]) #va selezionato manualmente se manca nel json, di default è M
        with col4:
            età = st.number_input("Età", value=paziente.get("eta", 0))
        with col5:
            #widget per la data
            data_nascita = st.date_input("Data di Nascita", value=default_date_nascita)

        luogo_nascita = st.text_input("Luogo di Nascita", value=paziente.get("luogo_nascita", ""))
        residenza = st.text_input("Residenza", value=paziente.get("residenza", ""))
        dichiarati_da = st.text_input("Dati Dichiarati da", value=paziente.get("dati_dichiarati_da", ""))


        st.markdown("<br>", unsafe_allow_html=True)  # riga vuota

        st.markdown("### Decesso")

        col1, col2, col3, col4 = st.columns([1, 1, 1, 1]) 

        
        with col1:
            decesso = st.checkbox("Paziente Deceduto", value=d.get("decesso", {}).get("decesso", False))

        # Logica per svuotare ora_decesso se il checkbox non è selezionato
        if not decesso:
            ora_decesso_val = ""
        else:
            ora_decesso_val = d.get("decesso", {}).get("ora_decesso", "")

        with col2:
            ora_decesso = st.text_input(
                "Ora del Decesso",
                value=ora_decesso_val,
                disabled=not decesso
            )

        st.markdown("<br>", unsafe_allow_html=True)  # riga vuota

        parametri_vitali = d.get("parametri_vitali") or {}
        st.markdown("### Parametri Vitali")
        col1, col2, col3 = st.columns([1, 1, 1])  
        with col1:
            pressione = st.text_input("Pressione", value=parametri_vitali.get("pressione", ""))
        with col2:
            battito = st.number_input("Battito", value=parametri_vitali.get("battito", 0))
        with col3:
            saturazione = st.number_input("Saturazione", value=parametri_vitali.get("saturazione", 0))

        col_coscienza, col_cute, col_respiro = st.columns(3)

        coscienza_data = parametri_vitali.get("coscienza") or {}
        with col_coscienza:
            st.markdown("##### Coscienza")
            coscienza = {
                "sveglio": st.checkbox("Sveglio", value=coscienza_data.get("sveglio", False)),
                "risponde_a_stimolo_verbale": st.checkbox("Risponde a stimolo verbale", value=coscienza_data.get("risponde_a_stimolo_verbale", False)),
                "risponde_a_dolore": st.checkbox("Risponde a dolore", value=coscienza_data.get("risponde_a_dolore", False)),
                "incosciente": st.checkbox("Incosciente", value=coscienza_data.get("incosciente", False))
            }

        cute_data = parametri_vitali.get("cute") or {}
        with col_cute:
            st.markdown("##### Cute")
            cute = {
                "normale": st.checkbox("Cute normale", value=cute_data.get("normale", False)),
                "pallida": st.checkbox("Cute pallida", value=cute_data.get("pallida", False)),
                "cianotica": st.checkbox("Cute cianotica", value=cute_data.get("cianotica", False)),
                "sudata": st.checkbox("Cute sudata", value=cute_data.get("sudata", False))
            }


        respiro_dato = parametri_vitali.get("respiro") or {}
        with col_respiro:
            st.markdown("##### Respiro")
            respiro = {
                "normale": st.checkbox("Respiro normale", value=respiro_dato.get("normale", False)),
                "tachipnoico": st.checkbox("Tachipnoico", value=respiro_dato.get("tachipnoico", False)),
                "bradipnoico": st.checkbox("Bradipnoico", value=respiro_dato.get("bradipnoico", False)),
                "assente": st.checkbox("Assente", value=respiro_dato.get("assente", False))
            }

        st.markdown("<br>", unsafe_allow_html=True)  # riga vuota


        #Sezione provvedimenti
        st.markdown("### Provvedimenti")

        
        st.markdown("##### Respiro")

        provvedimenti = d.get("provvedimenti") or {}
        respiro_prov = provvedimenti.get("respiro") or {}

        respiro_provvedimenti = {
            "aspirazione": st.checkbox("Aspirazione", value=respiro_prov.get("aspirazione", False)),
            "cannula_orofaringea": st.checkbox("Cannula Orofaringea", value=respiro_prov.get("cannula_orofaringea", False)),
            "monitor_spo2": st.checkbox("Monitor SpO2", value=respiro_prov.get("monitor_spo2", False)),
            "ventilazione": st.checkbox("Ventilazione", value=respiro_prov.get("ventilazione", False)),
            "incubazione": st.checkbox("Incubazione", value=respiro_prov.get("incubazione", False))
        }

        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        with col1:
            respiro_provvedimenti["ossigeno"] = st.checkbox("Ossigeno", value=respiro_prov.get("ossigeno", False))
        with col2:
            respiro_provvedimenti["ossigeno_lt_min"] = st.number_input("Ossigeno (lt/min)", value=respiro_prov.get("ossigeno_lt_min", 0))



        st.markdown("<br>", unsafe_allow_html=True)  # riga vuota

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.markdown("##### Circolo")

            provvedimenti = d.get("provvedimenti") or {}
            circolo = provvedimenti.get("circolo") or {}
            circolo_provvedimenti = {
                    "hematosi" : st.checkbox("Ematosi", value = circolo.get("hematosi", False)), 
                    "accesso_venoso" : st.checkbox("Accesso Venoso", value = circolo.get("accesso_venoso", False)),
                    "monitor_ecg" : st.checkbox("Monitor ECG", value = circolo.get("monitor_ecg", False)), 
                    "monitor_nibp" : st.checkbox("Monitor NIBP", value = circolo.get("monitor_nibp", False))
            } 

        with col2:
            st.markdown("##### Immobilizzazione")

            provvedimenti = d.get("provvedimenti") or {}
            immobilizzazione = provvedimenti.get("immobilizzazione") or {}
            
            immobilizzazione_provvedimenti = {
                    "collare_cervicale" : st.checkbox("Collare Cervicale", value = immobilizzazione.get("collare_cervicale", False)),
                    "barella_cucchiaio" : st.checkbox("Barrella a Cucchiaio", value = immobilizzazione.get("barella_cucchiaio", False)),
                    "tavola_spinale" : st.checkbox("Tavola Spinale", value = immobilizzazione.get("tavola_spinale", False)),
                    "steccobenda" : st.checkbox("Steccobenda", value = immobilizzazione.get("steccobenda", False)),
                    
            }
        
        altro = st.text_input("Altro", value=provvedimenti.get("altro", ""))
        farmaci = st.text_input("Farmaci", value=provvedimenti.get("farmaci", ""))

        st.markdown("<br>", unsafe_allow_html=True)  # riga vuota

        #sezione annotazioni
        st.markdown("#### Annotazioni")
        annotazioni = st.text_area("Annotazioni", value=d.get("annotazioni", ""))


        #qui costruisco il dizionario contenente tutti i dati del referto clinico. Li vado poi a salvare nel db 
        paziente_data = {
            "nome": nome,
            "cognome": cognome,
            "sesso": sesso,
            "data_nascita": datetime.combine(data_nascita, time.min),
            "eta": età,
            "residenza": residenza,
            "luogo_nascita": luogo_nascita
        }

        paziente_esistente = pazienti_collection.find_one({
            "nome": nome,
            "cognome": cognome,
            "data_nascita": datetime.combine(data_nascita, time.min)
        })
        if paziente_esistente:
            paziente_id = paziente_esistente["_id"]
        else:
            paziente_id = pazienti_collection.insert_one(paziente_data).inserted_id

        # Dati dell'intervento (referenziando il paziente)
        intervento_data = {
            "paziente_id": paziente_id,
            "dati_dichiarati_da": dichiarati_da,
            "chiamata_ps": {
                "data": datetime.combine(data_chiamata, time.min),
                "luogo_intervento": luogo_intervento,
                "condizione_riferita": condizione_riferita,
                "ora_chiamata": ora_chiamata,
                "ora_arrivo_ps": ora_arrivo_ps,
                "codice_uscita": codice_uscita
            },
            "autorita_presenti": {
                "carabinieri": carabinieri,
                "polizia_municipale": polizia_municipale,
                "polizia_stradale": polizia_stradale,
                "vigili_del_fuoco": vigili_del_fuoco,
                "guardia_medica": guardia_medica,
                "altra_ambulanza": altra_ambulanza
            },
            "parametri_vitali": {
                "pressione": pressione,
                "battito": battito,
                "saturazione": saturazione,
                "coscienza": coscienza,
                "cute": cute,
                "respiro": respiro
            },
            "provvedimenti": {
                "respiro": respiro_provvedimenti,
                "circolo": circolo_provvedimenti,
                "immobilizzazione": immobilizzazione_provvedimenti,
                "altro": altro,
                "farmaci": farmaci
            },
            "annotazioni": annotazioni,
            "decesso": {
                "decesso": decesso,
                "ora_decesso": ora_decesso if ora_decesso else None
            },
            "medico_curante": {
                "medico_id": st.session_state["utente"]["_id"],
                "medico_nome": f"{st.session_state['utente']['nome']} {st.session_state['utente']['cognome']}"
            }
        }

        if st.button("💾 Salva nel Database"):
            try:
                result = interventi_collection.insert_one(intervento_data)
                st.success(f"Intervento salvato con ID: {result.inserted_id}")
                t.sleep(1.5)  # ⏱️ Attendi 1.5 secondo per mostrare il messaggio
                del st.session_state["structured_data"]  # Rimuove i dati per nascondere il form in seguito al salvataggio
                st.rerun()  # Ricarica la pagina per aggiornare l'interfaccia
            except Exception as e:
                st.error(f"Errore salvataggio: {e}")




#SEZIONE "VISUALIZZA REFERTI"
elif page == "Visualizza Referti":
    st.header("📋 Referti Salvati")

    st.markdown("Filtri disponibili:")

    # Filtro per ottenere referti associati al medico corrente
    solo_miei = st.checkbox("Visualizza solo i miei referti")

    query = {}
    if solo_miei:
        query["medico_curante.medico_id"] = st.session_state["utente"]["_id"]

    # Filtro per cognome paziente
    cognome_paziente = st.text_input("Cognome Paziente")
    if cognome_paziente:
        matching_pazienti = list(pazienti_collection.find({
        "cognome": {"$regex": f"^{cognome_paziente}", "$options": "i"}
    }))

        matching_ids = [p["_id"] for p in matching_pazienti]
        if matching_ids: #se gli id corrispondono
            query["paziente_id"] = {"$in": matching_ids}
        else:
            query["paziente_id"] = {"$in": []}


    # Filtro per data (in `chiamata_ps.data`)
    data_visita = st.text_input("Data intervento (formato: AAAA-MM-GG)")
    if data_visita:
        try:
            data_obj = datetime.strptime(data_visita, "%Y-%m-%d").date()
            start = datetime.combine(data_obj, time.min)  # 00:00
            end = datetime.combine(data_obj, time.max)   # 23:59:59.999999
            query["chiamata_ps.data"] = {"$gte": start, "$lt": end}
        except ValueError:
            st.warning("Formato data non valido. Usa AAAA-MM-GG.")

    st.markdown("---")
    results = list(interventi_collection.find(query).sort("_id", -1))
    
    
    # Mostra i referti risultanti
    if results:
        for idx, r in enumerate(results):
            # Layout
            left_col, right_col = st.columns([6, 3]) 

            paziente = pazienti_collection.find_one({"_id":r["paziente_id"]}) or {}
            paziente.pop("_id", None)
            with left_col:
                st.markdown(f"### Referto di {paziente.get('nome', 'N/A')} {paziente.get('cognome', '')}")
            with right_col:
                b1, b2, b3 = st.columns(3)
                with b2:
                    if st.button("👁️ View", key=f"view_{idx}"):
                        st.session_state["selected_referto"] = r
                        modal.open()
                with b3:
                    if st.button("✏️ Edit", key=f"edit_{idx}"):
                        st.session_state["selected_referto"] = r
                        st.session_state["action"] = "edit"
                        st.experimental_rerun()
                with b3:
                    st.download_button(
                        label="📄 PDF",
                        data=genera_pdf(r, paziente),
                        file_name=f"referto_{paziente.get('cognome', 'unknown')}.pdf",
                        mime="application/pdf",
                        key=f"pdf_download_{idx}"
                    )


            #Dettagli del referto mostrati in anteprima
            st.markdown(f"🕒 Ora PS: **{r.get('chiamata_ps', {}).get('ora_arrivo_ps', '-') }** | 📍 Luogo: **{r.get('chiamata_ps', {}).get('luogo_intervento', '-') }**")
            st.markdown(f"👨‍⚕️ Medico: {r.get('medico_curante', {}).get('medico_nome', 'Sconosciuto')}")
            st.markdown(f"🩺 Condizione Riferita: *{r.get('chiamata_ps', {}).get('condizione_riferita', '')}*")
            st.markdown("---")
        
    else:
        st.markdown("### ❌ Nessun risultato trovato con i filtri selezionati.")



    # Se la modale viene aperta tramite il bottone VIEW
    if modal.is_open():
        with modal.container():
            r = st.session_state.get("selected_referto")
            if r:
                # Recupero il paziente referenziato tramite paziente_id
                paziente = pazienti_collection.find_one({"_id": r["paziente_id"]}) or {}
                paziente.pop("_id", None)  # Rimuovi _id per evitare problemi di visualizzazione

                # Sezioni del referto
                render_section("🚑 Chiamata PS", r.get("chiamata_ps", {}), expected_fields["chiamata_ps"])
                st.markdown("<br>", unsafe_allow_html=True)

                render_section("👮 Autorità Presenti", r.get("autorita_presenti", {}), expected_fields["autorita_presenti"])
                st.markdown("<br>", unsafe_allow_html=True)

                render_section("🧑 Dati Paziente", paziente, expected_fields["dati_paziente"])
                st.markdown("<br>", unsafe_allow_html=True)
                dichiarati_da = r.get("dati_dichiarati_da")
                st.markdown("### 👤 Dati dichiarati da")
                st.markdown(f"{dichiarati_da}" if dichiarati_da else "N/A")
                st.markdown("<br>", unsafe_allow_html=True)

                render_section("❤️ Parametri Vitali", r.get("parametri_vitali", {}), expected_fields["parametri_vitali"])
                st.markdown("<br>", unsafe_allow_html=True)
                
                provvedimenti = r.get("provvedimenti", {})

                render_section("💊 Provvedimenti", provvedimenti, expected_fields["provvedimenti"])

                st.markdown("<br>", unsafe_allow_html=True)
                # Annotazioni
                annotazioni = r.get("annotazioni", "")
                st.markdown("### 📝 Annotazioni")
                st.markdown(annotazioni or "Non sono presenti annotazioni.")
                st.markdown("<br>", unsafe_allow_html=True)

                # Decesso
                decesso = r.get("decesso", {})
                if decesso.get("decesso"):
                    st.warning(f"⚠️ Deceduto alle ore: {decesso.get('ora_decesso', 'N/A')}")
                    st.markdown("<br>", unsafe_allow_html=True)

            # Bottone per chiudere
            if st.button("❌ Chiudi", key="close_modal"):
                modal.close()
                st.experimental_rerun()




#SEZIONE ANALITICHE
elif page == "Analitiche Avanzate":
    query_option = st.selectbox(
        "Scegli una query",
        [
            "Distribuzione codici di uscita",
            "Numero referti per medico curante",
            "Grafico provvedimenti adottati",
            "Andamento del numero di interventi per anno",
            "Percentuale decessi rispetto agli interventi"
        ]
   )


    if query_option == "Distribuzione codici di uscita":
        codici = {"B": 0, "V": 0, "G": 0, "R": 0}
        for doc in interventi_collection.find({},{"chiamata_ps.codice_uscita": 1}):
            uscita = (doc.get("chiamata_ps") or {}).get("codice_uscita") or {}
            if uscita.get("B"): codici["B"] += 1
            if uscita.get("V"): codici["V"] += 1
            if uscita.get("G"): codici["G"] += 1
            if uscita.get("R"): codici["R"] += 1

        df = pd.DataFrame({
            "Codice": list(codici.keys()),
            "Conteggio": list(codici.values())
        })

        # Mappa colori personalizzata
        color_scale = alt.Scale(
            domain=["B", "V", "G", "R"],
            range=["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]
        )

        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("Codice:N", sort=["B","V","G","R"]),
                y="Conteggio:Q",
                color=alt.Color("Codice:N", scale=color_scale, legend=None)
            )
            .properties(
                title="Distribuzione codici di uscita",
                width=500,
                height=400
            )
        )

        st.altair_chart(chart, use_container_width=True)


    if query_option == "Numero referti per medico curante":
        risultati = list(interventi_collection.aggregate([
            {
                "$group": {
                    "_id": "$medico_curante.medico_id",
                    "numero_referti": {"$sum": 1},
                    "medico_nome": {"$first": "$medico_curante.medico_nome"}
                }
            }
        ]))

        df = pd.DataFrame(risultati)
        df = df.rename(columns={"_id": "Medico ID", "numero_referti": "Numero referti", "medico_nome": "Medico curante"})

        # Grafico con Altair
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('Medico curante:N', axis=alt.Axis(labelAngle=0)),  # etichette orizzontali
            y='Numero referti:Q'
        ).properties(title="Numero referti per medico curante", width=600, height=400)

        st.altair_chart(chart, use_container_width=True)

    if query_option == "Grafico provvedimenti adottati":
        #faccio una pipeline per contare tutti i provvedimenti per tipo. 
        query = [
        {
            "$facet": {
                "Ossigeno": [
                    {"$match": {"provvedimenti.respiro.ossigeno": True}},
                    {"$count": "count"}
                ],
                "Ventilazione": [
                    {"$match": {"provvedimenti.respiro.ventilazione": True}},
                    {"$count": "count"}
                ],
                "Aspirazione": [
                    {"$match": {"provvedimenti.respiro.aspirazione": True}},
                    {"$count": "count"}
                ],
                "AccessoVenoso": [
                    {"$match": {"provvedimenti.circolo.accesso_venoso": True}},
                    {"$count": "count"}
                ],
                "MonitorECG": [
                    {"$match": {"provvedimenti.circolo.monitor_ecg": True}},
                    {"$count": "count"}
                ],
                "Hematosi": [
                    {"$match": {"provvedimenti.circolo.hematosi": True}},
                    {"$count": "count"}
                ],
                "Collare": [
                    {"$match": {"provvedimenti.immobilizzazione.collare_cervicale": True}},
                    {"$count": "count"}
                ],
                "Steccobenda": [
                    {"$match": {"provvedimenti.immobilizzazione.steccobenda": True}},
                    {"$count": "count"}
                ],
                "Barella": [
                    {"$match": {"provvedimenti.immobilizzazione.barella_cucchiaio": True}},
                    {"$count": "count"}
                ],
                "TavolaSpinale": [
                    {"$match": {"provvedimenti.immobilizzazione.tavola_spinale": True}},
                    {"$count": "count"}
                ],
                "Farmaci": [
                    {"$match": {"provvedimenti.farmaci": {"$exists": True, "$ne": None, "$ne": ""}}}, #qui considero solo se esiste il campo e se è diverso da None/campo vuoto, come faccio anche per i farmaci
                    {"$count": "count"}
                ],
                "Altro": [
                    {"$match": {"provvedimenti.altro": {"$exists": True, "$ne": None, "$ne": ""}}},
                    {"$count": "count"}
                ]
            }
        }
    ]

        result = list(interventi_collection.aggregate(query))[0]

        #con facet ottengo una lista di documenti, quindi accedo al primo dizionario nella lista, accedo al campo count e mi prendo il valore se c'è altrimenti conto 0
        provvedimenti = {
            "Ossigeno": result["Ossigeno"][0]["count"] if result["Ossigeno"] else 0,
            "Ventilazione": result["Ventilazione"][0]["count"] if result["Ventilazione"] else 0,
            "Aspirazione": result["Aspirazione"][0]["count"] if result["Aspirazione"] else 0,
            "Accesso Venoso": result["AccessoVenoso"][0]["count"] if result["AccessoVenoso"] else 0,
            "Monitor ECG": result["MonitorECG"][0]["count"] if result["MonitorECG"] else 0,
            "Hematosi": result["Hematosi"][0]["count"] if result["Hematosi"] else 0,
            "Collare": result["Collare"][0]["count"] if result["Collare"] else 0,
            "Steccobenda": result["Steccobenda"][0]["count"] if result["Steccobenda"] else 0,
            "Barella": result["Barella"][0]["count"] if result["Barella"] else 0,
            "Tavola Spinale": result["TavolaSpinale"][0]["count"] if result["TavolaSpinale"] else 0,
            "Farmaci": result["Farmaci"][0]["count"] if result["Farmaci"] else 0,
            "Altro": result["Altro"][0]["count"] if result["Altro"] else 0
        }

        #considero soltanto i campi che hanno un valore diverso da 0
        provvedimenti_not_null = {k: v for k, v in provvedimenti.items() if v > 0}

        labels = list(provvedimenti_not_null.keys())
        sizes = list(provvedimenti_not_null.values())
        
        #mostro i risultati su un piechart
        fig, ax = plt.subplots()
        ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            textprops={"fontsize": 10}
        )
        ax.axis("equal")
        ax.set_title("Provvedimenti adottati")
        #mostro la figura col titolo
        #TODO: vedi come cambiare i colori
        st.pyplot(fig)

    if query_option == "Andamento del numero di interventi per anno":
        st.subheader("📈 Andamento del numero di interventi per anno")

        pipeline = [
            {
                "$match": {
                    "chiamata_ps.data": { "$type": "date" }  # solo oggetti BSON Date
                }
            },
            {
                "$project": {
                    "anno": { "$year": { "$toDate": "$chiamata_ps.data" } }
                }
            },
            {
                "$group": {
                    "_id": "$anno",
                    "conteggio": { "$sum": 1 }
                }
            },
            {
                "$sort": { "_id": 1 }  # ordina per anno crescente
            }
        ]

        risultati = list(interventi_collection.aggregate(pipeline))

        if not risultati:
            st.warning("Nessun dato disponibile.")
        else:
            anni = [str(ris["_id"]) for ris in risultati]
            conteggi = [ris["conteggio"] for ris in risultati]

            df = pd.DataFrame({
                "Anno": anni,
                "Numero Interventi": conteggi
            })

            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X("Anno:N", title="Anno"),
                y=alt.Y("Numero Interventi:Q", title="Numero Interventi", scale=alt.Scale(domainMin=1)),
                tooltip=["Anno", "Numero Interventi"]
            ).properties(
                width=700,
                height=400,
                title="Andamento del numero di interventi per anno"
            )

            st.altair_chart(chart, use_container_width=True)

        
    if query_option == "Percentuale decessi rispetto agli interventi":
        totale_interventi = interventi_collection.count_documents({})
        decessi_count = interventi_collection.count_documents({"decesso.decesso": True})

        if totale_interventi == 0:
            st.warning("Nessun dato disponibile.")
        else:
            percentuale_decessi = (decessi_count / totale_interventi) * 100

            st.subheader("📊 Percentuale decessi rispetto al totale interventi")
            st.markdown(f"**Totale interventi:** {totale_interventi}")
            st.markdown(f"**Interventi con decesso:** {decessi_count}")
            st.markdown(f"**Percentuale decessi:** {percentuale_decessi:.2f}%")

            # Grafico a torta
            labels = ["Sopravvivenze", "Decessi"]
            sizes = [totale_interventi - decessi_count, decessi_count]
            colors = ["#4CAF50", "#F44336"]  # verde sopravvivenze, rosso decessi

            fig, ax = plt.subplots()
            ax.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=90,
                colors=colors,
                textprops={"fontsize": 12}
            )
            ax.axis("equal")
            ax.set_title("Decessi vs Sopravvivenze")

            st.pyplot(fig)
