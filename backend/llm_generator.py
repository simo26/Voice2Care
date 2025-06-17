from datetime import datetime, timedelta
import random
import os
from faker import Faker  # Libreria per generare dati fittizi realistici (es. nomi, indirizzi, date)
import google.generativeai as genai  # Libreria ufficiale per interagire con i modelli Google Gemini
from dotenv import load_dotenv  # Per caricare le variabili d'ambiente dal file .env

# Carica le variabili dal file .env
load_dotenv()

# Leggi la varibile di ambiente dell'API Key per Gemini 
API_KEY_GEMINI = os.getenv("API_KEY_GEMINI")


# Inizializzazione di Faker con localizzazione italiana
fake = Faker("it_IT")



# Funzione che genera un referto vocale fittizio, come se fosse dettato da un medico
def generate_doctor_speech() -> str: 
    # DATI ANAGRAFICI FITTIZI
    nome = fake.first_name()  # Nome del paziente
    cognome = fake.last_name()  # Cognome del paziente
    data_nascita = fake.date_of_birth(minimum_age=6, maximum_age=90).strftime("%Y-%m-%d")  # Data di nascita formattata
    eta = 2025 - int(data_nascita[:4])  # Età calcolata in base all'anno di nascita
    luogo_nascita = fake.city()  # Città di nascita
    residenza = f"{fake.city()}, {fake.street_name()} {fake.building_number()}"  # Indirizzo di residenza
    dati_dichiarati_da = random.choice(["Paziente", "Familiare", "Personale sanitario", "Non identificato"])  # Fonte dei dati anagrafici

    # TEMPI E DETTAGLI DELL’INTERVENTO 
    inizio_finestra_data_chiamata = datetime.now() - timedelta(days=365 * 10)  # Limite inferiore: 10 anni fa
    finestra_data_chiamata = fake.date_time_between(start_date=inizio_finestra_data_chiamata, end_date=datetime.now())  # Data chiamata casuale
    data_chiamata = finestra_data_chiamata.strftime("%Y-%m-%d")  # Estrae la data in formato stringa
    ora_chiamata_dt = finestra_data_chiamata  # Salvo oggetto datetime per utilizzarlo successivamente
    ora_chiamata = ora_chiamata_dt.isoformat()  # Formattazione ISO dell'orario di chiamata

    ritardo = timedelta(minutes=random.randint(15, 40))  # Ritardo casuale tra chiamata e arrivo compreso tra i 15 e 40 min
    ora_arrivo_ps_dt = ora_chiamata_dt + ritardo  # Calcola orario di arrivo al pronto soccorso
    ora_arrivo_ps = ora_arrivo_ps_dt.isoformat()  # Formattazione ISO dell'orario di arrivo

    luogo_intervento = fake.address()  # Indirizzo fittizio dell'intervento
    codice_uscita_lettera = random.choice(["B", "V", "G", "R"])  # Colore Codice di uscira

    # Autorità presenti durante l'intervento (da 0 a 3 scelte casuali)
    autorita = random.sample([
        "carabinieri", "polizia_stradale", "polizia_municipale",
        "vigili_del_fuoco", "guardia_medica", "altra_ambulanza"
    ], k=random.randint(0, 3))



    #PROMPT PER IL MODELLO GEMINI
    # Contiene tutte le informazioni sopra generate e chiede al modello di completare il referto clinico
    prompt = f"""
    Il paziente si chiama {nome} {cognome}. Deduci il sesso corretto in base al nome e usalo correttamente nel referto.
    Data di nascita: {data_nascita}, età: {eta} anni. Luogo di nascita: {luogo_nascita}. Residenza: {residenza}.
    I dati anagrafici del paziente sono stati dichiarati da: {dati_dichiarati_da}.

    La chiamata è avvenuta il giorno {data_chiamata} alle {ora_chiamata}. Il luogo dell’intervento è: {luogo_intervento}.
    Il paziente è arrivato in pronto soccorso alle {ora_arrivo_ps}.
    Il codice d’uscita attribuito all’intervento è di tipo '{codice_uscita_lettera}'.
    Durante l'intervento erano presenti le seguenti autorità: {', '.join(autorita) if autorita else "nessuna"}.

    Ora completa il referto vocale con queste informazioni che devi valutare e descrivere tu, in modo tale che siano coerenti:
    - Condizione del paziente o da terzi al momento della chiamata.
    - Stato di coscienza (sveglio, stimolo verbale, dolore, incosciente).
    - Stato della cute (normale, pallida, cianotica, sudata).
    - Respiro (normale, tachipnoico, bradipnoico, assente).
    - Parametri vitali (pressione arteriosa, battito, saturazione).
    - Provvedimenti adottati sul respiro (ossigeno lt/min, aspirazione, ventilazione e simili), sul circolo (accesso venoso, emostasi e simili), sull’immobilizzazione (collare, steccobenda, e simili).
    - Eventuali farmaci somministrati e interventi aggiuntivi.
    - Se il paziente è deceduto, indica l’orario e il contesto del decesso.
    - Se necessario, aggiungi annotazioni e valutazioni finali sintetiche, che NON includano incongruenze temporali sulle date degli eventi.
    - Non scordare di includere nel discorso tutte le informazioni fornite.

    Scrivi come se un medico stesse dettando un referto vocale, utilizzando linguaggio medico fluido, senza fare un elenco e senza essere troppo prolisso (contesto di emergenza, sii sintetico), no codici JSON.
    """


    #CONFIGURAZIONE ED ESECUZIONE DEL MODELLO GEMINI

    # Configura l’accesso alle API Gemini con la chiave API
    genai.configure(api_key = API_KEY_GEMINI)
    
    # Istanzia il modello "gemini-1.5-flash", ottimizzato per risposte rapide e coerenti
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Generazione del contenuto basato sul prompt costruito
    response = model.generate_content(prompt)

    # Ritorno il testo generato, ripulito da eventuali spazi bianchi iniziali/finali
    return response.text.strip()
