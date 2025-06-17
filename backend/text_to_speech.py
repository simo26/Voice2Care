import edge_tts  # Libreria per sintetizzare voce in testo usando Microsoft Edge TTS (neural voice)
from pydub import AudioSegment  # Libreria per manipolare file audio
from datetime import datetime  
import os 
import random 

# Elenco delle voci disponibili per la sintesi in italiano
voci = [
    "it-IT-ElsaNeural",
    "it-IT-IsabellaNeural",
    "it-IT-DiegoNeural"
]

# Funzione asincrona per sintetizzare testo in audio .wav con voce casuale
async def synthesize_text_to_wav(text: str, output_dir: str = "audio") -> str:
    os.makedirs(output_dir, exist_ok=True)  # Creo la directory di output se non esiste
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Timestamp per il nome del file audio
    filename = f"discorso_{timestamp}.wav"  # Nome del file audio risultante
    file_path = os.path.join(output_dir, filename)  # Percorso completo del file audio

    voice = random.choice(voci)  # Selezione casuale di una voce italiana
    communicate = edge_tts.Communicate(text, voice=voice)  # Istanzio l'oggetto per la sintesi vocale tramite Microsoft Edge TTS
    await communicate.save(file_path)  # Esegue la sintesi e salva il file audio

    return file_path  # Ritorno del percorso del file audio generato

# Funzione per aggiungere rumore di fondo a una traccia vocale
def add_noise(voice_path, noise_path, output_path, noise_db=-20):
    voice = AudioSegment.from_file(voice_path)  # Carica l'audio della voce
    noise = AudioSegment.from_file(noise_path)  # Carica il rumore da sovrapporre

    # Se il rumore è più corto della voce, lo ripete fino a raggiungere la durata necessaria
    if len(noise) < len(voice):
        loops = (len(voice) // len(noise)) + 1
        noise *= loops  # Ripeti il rumore per coprire tutta la durata

    noise = noise - abs(noise_db)  # Abbassa il volume del rumore di -20 dB
    noise = noise[:len(voice)]  # Tronca il rumore alla lunghezza esatta della voce

    combined = voice.overlay(noise)  # Sovrappone la voce con il rumore
    combined = combined.set_frame_rate(16000)  # Imposta la frequenza di campionamento a 16kHz per non eccedere il payload di Whisper 
    combined.export(output_path, format="wav")  # Esporta l'audio combinato come file WAV
