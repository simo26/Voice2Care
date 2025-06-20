import redis
import json
import requests
import os

# Per caricare le variabili d'ambiente dal file .env
from dotenv import load_dotenv  

# Carica le variabili dal file .env
load_dotenv()

# Leggi la varibile di ambiente del Token di autorizzazione per il provider Hugging Face
CHAT_ID = os.getenv("CHAT_ID")


BOT_TOKEN = "7935276594:AAHNX091qdRxR4W9kYyqi7G8H_Y_5f5ADsE"
CHAT_IDS = [CHAT_ID] #metti l'id della tua chat: invia un messaggio al bot @CodiceRossoBot ed estrapola chat id https://api.telegram.org/bot7935276594:AAHNX091qdRxR4W9kYyqi7G8H_Y_5f5ADsE/getUpdates

r = redis.Redis(
    host = 'localhost',
    port = 6379,
    db = 0
)
sub = r.pubsub()
sub.subscribe("codice_rosso")

print("in attesa di codice rosso")

def send_tg(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        try:
            data = {"chat_id": chat_id, "text":msg}
            requests.post(url, data = data)
        except Exception as e:
            print(f"errore invio: {e}")

for message in sub.listen():
    if message["type"] == "message":
        try:
            data = json.loads(message["data"])
            nome = data.get("paziente", {}).get("nome", "Sconosciuto")
            cognome = data.get("paziente", {}).get("cognome", "")
            luogo = data.get("chiamata_ps", {}).get("luogo_intervento", "ignoto")

            testo = f"CODICE ROSSO\n Paziente: {nome} {cognome}\n Luogo Intervento:{luogo}"
            print("invio alert Telegram:", testo)
            send_tg(testo)
        except Exception as e:
            print("Errore parsing/invio:", e)
