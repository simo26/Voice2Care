from typing import Optional  # Usata per dichiarare campi opzionali nei modelli 
from pydantic import BaseModel, ValidationError  # BaseModel per creare strutture dati validate (modelli Pydantic); ValidationError gestisce errori di validazione
from langchain.output_parsers import PydanticOutputParser  # Parser che consente di mappare l'output generato da un LLM su un modello Pydantic
import google.generativeai as genai  # Libreria di Google per accedere ai modelli della famiglia Gemini
from datetime import date 
from enum import Enum 
import os

# Per caricare le variabili d'ambiente dal file .env
from dotenv import load_dotenv  

# Carica le variabili dal file .env
load_dotenv()

# Leggi la varibile di ambiente dell'API Key per Gemini 
API_KEY_GEMINI = os.getenv("API_KEY_GEMINI")



#ENUM per valori limitati del sesso
class SessoEnum(str, Enum):
    M = "M"  # Maschio
    F = "F"  # Femmina

# --- Modelli Pydantic per strutturare e validare i dati clinici ---

# Codice colore di uscita dal pronto soccorso
class CodiceUscita(BaseModel):
    B: Optional[bool] = False  # Bianco
    V: Optional[bool] = False  # Verde
    G: Optional[bool] = False  # Giallo
    R: Optional[bool] = False  # Rosso

# Dati relativi alla chiamata al pronto soccorso
class ChiamataPS(BaseModel):
    data: Optional[date] = None
    ora_chiamata: Optional[str] = None
    ora_arrivo_ps: Optional[str] = None
    luogo_intervento: Optional[str] = None
    condizione_riferita: Optional[str] = None
    codice_uscita: Optional[CodiceUscita] = None

# Autorità presenti sul luogo dell'intervento
class AutoritaPresenti(BaseModel):
    carabinieri: Optional[bool] = False
    polizia_stradale: Optional[bool] = False
    polizia_municipale: Optional[bool] = False
    vigili_del_fuoco: Optional[bool] = False
    guardia_medica: Optional[bool] = False
    altra_ambulanza: Optional[bool] = False

# Anagrafica del paziente
class Paziente(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    sesso: SessoEnum  # Deve essere 'M' o 'F'
    eta: Optional[int] = 0
    data_nascita: Optional[date] = None
    luogo_nascita: Optional[str] = None
    residenza: Optional[str] = None

# Eventuale decesso del paziente
class Decesso(BaseModel):
    decesso: Optional[bool] = False
    ora_decesso: Optional[str] = None  # Stringa in formato orario

# Stato di coscienza del paziente
class Coscienza(BaseModel):
    sveglio: Optional[bool] = False
    risponde_a_stimolo_verbale: Optional[bool] = False
    risponde_a_dolore: Optional[bool] = False
    incosciente: Optional[bool] = False

# Stato della cute
class Cute(BaseModel):
    normale: Optional[bool] = False
    pallida: Optional[bool] = False
    cianotica: Optional[bool] = False
    sudata: Optional[bool] = False

# Parametri respiratori
class RespiroParam(BaseModel):
    normale: Optional[bool] = False
    tachipnoico: Optional[bool] = False
    bradipnoico: Optional[bool] = False
    assente: Optional[bool] = False

# Parametri vitali complessivi
class ParametriVital(BaseModel):
    coscienza: Coscienza = Coscienza()
    cute: Cute = Cute()
    respiro: RespiroParam = RespiroParam()
    pressione: Optional[str] = None
    battito: Optional[int] = 0
    saturazione: Optional[int] = 0

# Interventi sul respiro
class RespiroProvvedimenti(BaseModel):
    aspirazione: Optional[bool] = False
    cannula_orofaringea: Optional[bool] = False
    monitor_spo2: Optional[bool] = False
    ossigeno: Optional[bool] = False
    ossigeno_lt_min: Optional[int] = 0
    ventilazione: Optional[bool] = False
    incubazione: Optional[bool] = False

# Interventi sul circolo
class CircoloProvvedimenti(BaseModel):
    hematosi: Optional[bool] = False
    accesso_venoso: Optional[bool] = False
    monitor_ecg: Optional[bool] = False
    monitor_nibp: Optional[bool] = False

# Interventi di immobilizzazione
class ImmobilizzazioneProvvedimenti(BaseModel):
    collare_cervicale: Optional[bool] = False
    barella_cucchiaio: Optional[bool] = False
    tavola_spinale: Optional[bool] = False
    steccobenda: Optional[bool] = False

# Provvedimenti sanitari totali
class Provvedimenti(BaseModel):
    respiro: RespiroProvvedimenti = RespiroProvvedimenti()
    circolo: CircoloProvvedimenti = CircoloProvvedimenti()
    immobilizzazione: ImmobilizzazioneProvvedimenti = ImmobilizzazioneProvvedimenti()
    altro: Optional[str] = None
    farmaci: Optional[str] = None

# Modello complessivo del referto clinico
class RefertoClinico(BaseModel):
    dati_dichiarati_da: Optional[str] = None
    chiamata_ps: Optional[ChiamataPS]
    autorita_presenti: Optional[AutoritaPresenti]
    paziente: Optional[Paziente]
    decesso: Optional[Decesso]
    parametri_vitali: Optional[ParametriVital]
    provvedimenti: Optional[Provvedimenti]
    annotazioni: Optional[str] = None



# Funzione di estrazione tramite modello Gemini 
def extract_json_from_transcription(transcription: str) -> dict:
    # Parser di output basato sul modello RefertoClinico di Pydantic
    parser = PydanticOutputParser(pydantic_object=RefertoClinico)
    format_instructions = parser.get_format_instructions()

    # Prompt per Gemini finalizzato a guidare il modello nel generare un JSON corretto e validabile
    prompt = (
        f"{transcription.strip()}\n\n"
        "Agisci come un assistente clinico per la gestione di casi di emergenza.\n"
        "Il tuo compito è estrarre dati clinici strutturati a partire da una breve descrizione testuale, che simula una trascrizione vocale in pronto soccorso\n"
        "Ti verrà quindi fornito un testo che descrive un caso clinico, per cui dovrai:\n"
        "- Utilizzare una terminologia medica corretta\n"
        "- Correggere eventuali errori grammaticali o di trascrizione\n"
        "- Calcolare l'età dalla data di nascita e dalla data della chiamata, se l'età non è esplicitamente indicata\n"
        "- Non confondere il luogo di nascita con la data di nascita\n"
        "- Assicurati di estrarre nome e cognome del paziente, se presenti nel testo\n"
        "- Assicurati di estrarre il sesso corretto del paziente\n"
        "- Se nel testo sono presenti interventi medici (come ventilazione, ossigeno, barella, steccobende, farmaci, monitoraggi), riempi appropriatamente il campo 'provvedimenti' e i sottocampi:\n"
        "  'respiro', 'circolo', 'immobilizzazione', 'farmaci', 'altro'\n"
        "- Se ci sono informazioni aggiuntive sullo stato generale del paziente, mettile nel campo 'annotazioni'\n"
        "- Se il codice di uscita è mancante, ricavalo in base alla gravità del caso (bianco, verde, giallo, rosso)\n"
        "Restituisci solo un oggetto JSON valido. Inizia con `{` e non aggiungere testo descrittivo o spiegazioni.\n"
        f"{format_instructions}\n"
    )

    try:
        # Configura l'API Gemini con la tua chiave 
        genai.configure(api_key=API_KEY_GEMINI)
        model = genai.GenerativeModel("gemini-1.5-flash")  # Uso il modello Gemini Flash
        response = model.generate_content(prompt)  # Invoco il modello con il prompt di guida
        output_raw = response.text.strip()  # Output in formato JSON

        try:
            # Validazione dell'output in oggetto Pydantic ed eventuale ritorno nel caso di parsing andato a buon fine
            parsed = parser.parse(output_raw)
            return parsed.dict()
        except ValidationError as e:
            # Se l'output non è compatibile con il modello Pydantic
            return {
                "errore": "Validazione fallita",
                "dettagli": str(e),
                "output_raw": output_raw
            }
        except Exception as e:
            # In caso di errore generico durante il parsing
            return {
                "errore": "Parsing generico fallito",
                "dettagli": str(e),
                "output_raw": output_raw
            }

    except Exception as e:
        # In caso di errore nella chiamata al modello generativo
        return {
            "errore": f"Errore nella chiamata API: {str(e)}"
        }
