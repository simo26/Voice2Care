from datetime import datetime  # Gestione di date 
from io import BytesIO  # Buffer in memoria per creare file senza salvarli su disco
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer  # Per costruire PDF
from reportlab.lib.pagesizes import A4  # Formato pagina A4 per PDF
from reportlab.lib.styles import getSampleStyleSheet  # Stili predefiniti per formattazione testo nel pdf


# Dizionario che definisce i campi attesi in ogni sezione del referto
expected_fields = {
    "chiamata_ps": ["data", "luogo_intervento", "condizione_riferita", "ora_chiamata", "ora_arrivo_ps", "codice_uscita"],
    "autorita_presenti": ["carabinieri", "polizia_municipale", "polizia_stradale", "vigili_del_fuoco", "guardia_medica", "altra_ambulanza"],
    "dati_paziente": ["nome", "cognome", "sesso", "eta", "data_nascita", "luogo_nascita", "residenza"],
    "parametri_vitali": ["pressione", "battito", "saturazione", "coscienza", "cute", "respiro"],
    "provvedimenti": ["respiro", "circolo", "immobilizzazione", "altro", "farmaci"]
}



def genera_pdf(referto, paziente=None):
    """
    Genera un PDF del referto clinico a partire dai dati forniti.
    referto: dizionario con i dati del referto.
    paziente: dizionario opzionale con dati del paziente.
    Restituisce un buffer BytesIO contenente il PDF.
    """
    buffer = BytesIO()  # Creo un buffer in memoria dove scrivere il PDF
    # Configuro il documento PDF con margini e formato A4
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()  # Carico gli stili base predefiniti per i paragrafi
    elements = []  # Lista di elementi (paragrafi, spazi) che comporranno il PDF

    def aggiungi_paragrafo(testo, stile="Normal", spazio=6):
        # Aggiunge un paragrafo con testo formattato e uno spazio dopo di esso
        elements.append(Paragraph(testo, styles[stile]))  
        elements.append(Spacer(1, spazio))  

    # Funzione interna che aggiunge al PDF una sezione di dati formattata
    def format_section(title, section_key):
        
        # Se la sezione è "dati_paziente", uso i dati passati esplicitamente
        if section_key == "dati_paziente":
            data = paziente or {}
        else:
            # Per le altre sezioni prendo i dati dal referto (se presenti)
            data = referto.get(section_key, {})

        # Aggiungo il titolo della sezione con stile Heading4 
        aggiungi_paragrafo(f"{title}:", "Heading4", spazio=4)

        #per "autorita_presenti" mostro solo quelle con valore True
        if section_key == "autorita_presenti":
            # Trovo tutte le chiavi attive (True) tra quelle attese
            true_keys = [k for k in expected_fields[section_key] if data.get(k) is True]
            if true_keys:
                # Le formatto come stringa separata da virgole, sostituendo underscore e capitalizzando
                formatted = ", ".join(k.replace("_", " ").capitalize() for k in true_keys)
                aggiungi_paragrafo(formatted)  # Aggiungo la stringa formattata al PDF
            else:
                # Se nessuna autorità presente
                aggiungi_paragrafo("Nessuna autorità presente")
        else:
            # Per tutte le altre sezioni, ciclo su tutti i campi attesi
            for field in expected_fields[section_key]:
                val = clean_value(data.get(field))  # Pulisce e formatta il valore
                # Aggiungo il campo e valore formattato in grassetto nel PDF
                aggiungi_paragrafo(f"<b>{field.replace('_', ' ').capitalize()}</b>: {val}")


    #Inizio costruzione contenuto PDF 
    elements.append(Paragraph("Referto Clinico Voice2Care", styles['Title']))  # Titolo principale
    elements.append(Spacer(1, 12))  # Spazio 

    format_section("Dati Paziente", "dati_paziente")  # Aggiungo i dati paziente

    aggiungi_paragrafo("Dati dichiarati da:", "Heading4", spazio=4)  # Titolo sezione
    aggiungi_paragrafo(clean_value(referto.get("dati_dichiarati_da", "N/A")))  # Dati dichiarati da

    # Aggiungo tutte le altre sezioni del referto
    format_section("Chiamata Pronto Soccorso", "chiamata_ps")
    format_section("Autorità Presenti", "autorita_presenti")
    format_section("Parametri Vitali", "parametri_vitali")
    format_section("Provvedimenti", "provvedimenti")

    # Sezione annotazioni: se presente, la mostro, altrimenti testo di default
    annotazioni = referto.get("annotazioni", "")
    aggiungi_paragrafo("Annotazioni:", "Heading4", spazio=4)
    aggiungi_paragrafo(annotazioni if annotazioni else "Non sono presenti annotazioni.")

    # Se presente la sezione decesso, la aggiungo al PDF
    deceduto = referto.get("decesso", {})
    if deceduto.get("decesso"):  # Controlla flag decesso True
        aggiungi_paragrafo("Decesso:", "Heading4", spazio=4)
        # Aggiungo ora del decesso, se presente, altrimenti N/A
        aggiungi_paragrafo(f"Deceduto alle ore: {deceduto.get('ora_decesso', 'N/A')}")

    doc.build(elements)  # Compila il PDF con tutti gli elementi accumulati
    buffer.seek(0)  # Riporta il puntatore all’inizio del buffer per lettura
    return buffer  # Ritorna il buffer contenente il PDF



def clean_value(value):
    """
    Funzione ricorsiva per pulire e formattare valori di vario tipo in stringhe leggibili:
    - None => "N/A"
    - datetime => formato dd/mm/yyyy
    - dict con date MongoDB => convertite in data leggibile
    - dizionari con campi speciali (es. ossigeno) => formattati in modo personalizzato
    - booleani => "True" o "N/A"
    - liste => valori separati da virgola
    - altri tipi => conversione a stringa
    """
    if value is None:
        return "N/A"  # Valore mancante

    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")  # Data in formato leggibile

    if isinstance(value, dict):
        # Gestione caso data in formato MongoDB {"$date"}
        if "$date" in value:
            millis = None
            # Se il valore è in "$numberLong"
            if isinstance(value["$date"], dict) and "$numberLong" in value["$date"]:
                millis = int(value["$date"]["$numberLong"])
            elif isinstance(value["$date"], int):
                millis = value["$date"]
            if millis:
                dt = datetime.utcfromtimestamp(millis / 1000)  # Conversione da millisecondi a datetime
                return dt.strftime("%d/%m/%Y")

        # Caso speciale per dizionario con campo "ossigeno" e "ossigeno_lt_min"
        if "ossigeno" in value and "ossigeno_lt_min" in value:
            ossigeno_attivo = value.get("ossigeno", False)
            parts = []
            for k, v in value.items():
                # Se ossigeno non attivo, salto la visualizzazione dei litri al minuto
                if k == "ossigeno_lt_min" and not ossigeno_attivo:
                    continue
                if isinstance(v, bool):
                    if v:
                        parts.append(k.replace("_", " "))  # Mostro chiavi True
                else:
                    val_str = clean_value(v)  # Ricorsione per formattare valori interni
                    parts.append(f"{k.replace('_', ' ')}: {val_str}")
            return ", ".join(parts) if parts else "N/A"

        # Caso generico per dizionari
        parts = []
        for k, v in value.items():
            if isinstance(v, bool):
                if v:
                    parts.append(k.replace("_", " "))  # Mostro solo chiavi True
            else:
                val_str = clean_value(v)  # Ricorsione per eventuali valori annidati
                parts.append(f"{k.replace('_', ' ')}: {val_str}")
        return ", ".join(parts) if parts else "N/A"

    if isinstance(value, bool):
        return "True" if value else "N/A"  # Booleani come stringhe leggibili

    if isinstance(value, list):
        return ", ".join(str(x) for x in value) if value else "N/A"  # Liste come stringa separata da virgole

    return str(value)  # Conversione finale a stringa per tutti gli altri casi
