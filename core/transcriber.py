import os
import time
import requests
from pydub import AudioSegment
import whisper
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Sarvam's sync STT API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small") or "small"
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"

_model = None


def load_model():
    global _model  

    if _model is None: 
        model_name = os.getenv("WHISPER_MODEL", "small") or "small"
        print(f"Loading Whisper model: {model_name} ...")
        _model = whisper.load_model(model_name) 
        print("Whisper model loaded.")
    return _model 


def transcribe_chunk_whisper(chunk_path: str) -> str:
    model = load_model()  
    result = model.transcribe(chunk_path, task="transcribe")  
    return result["text"]  


def _send_to_sarvam(piece_path: str, session: requests.Session = None, max_retries: int = 3) -> str:
    """Send one <= 30s WAV file to Sarvam and return the English transcript."""
    api_key = (os.getenv("SARVAM_API_KEY") or "").strip("'\" ")
    model = (os.getenv("SARVAM_STT_MODEL") or "saaras:v3").strip("'\" ")

    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    headers = {"api-subscription-key": api_key}
    requester = session or requests

    for attempt in range(1, max_retries + 1):
        try:
            with open(piece_path, "rb") as f:
                files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
                data = {
                    "model": model,
                    "mode": "translate",
                    "with_diarization": "false",
                }
                response = requester.post(
                    SARVAM_STT_URL,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=(15, 60),
                )

            if response.status_code == 200:
                return response.json().get("transcript", "")

            # If rate limited or transient server error, retry with backoff
            if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                print(f"  [Warning] Sarvam returned {response.status_code}, retrying in {attempt * 2}s...")
                time.sleep(2 * attempt)
                continue

            print(f"\n[Error] Sarvam returned {response.status_code}")
            print(f"Response body: {response.text}\n")
            response.raise_for_status()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < max_retries:
                print(f"  [Warning] Connection issue on attempt {attempt}/{max_retries}, retrying in {attempt * 2}s...")
                time.sleep(2 * attempt)
            else:
                raise e

    return ""


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API only accepts <= 30s audio. We split this chunk into
    25-second pieces, send each separately, and join the transcripts.
    """
    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    session = requests.Session()

    try:
        for i, start in enumerate(range(0, len(audio), piece_ms)):
            piece = audio[start: start + piece_ms]
            piece_path = f"{chunk_path}_sv_{i}.wav"
            piece.export(piece_path, format="wav")

            try:
                print(f"  -> Sarvam piece {i + 1}/{total_pieces} ...")
                transcript_piece = _send_to_sarvam(piece_path, session=session)
                if transcript_piece:
                    full_text += transcript_piece + " "
            finally:
                if os.path.exists(piece_path):
                    os.remove(piece_path)
    finally:
        session.close()

    return full_text.strip()


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route one chunk to Whisper or Sarvam depending on language choice.
    - english  -> Whisper (local model)
    - hinglish -> Sarvam (translates to English while transcribing)
    """
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)
    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:
    full_transcript = "" 

    engine = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"
    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):  
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk(chunk, language=language)  
        full_transcript += text + " "  

    print("Transcription complete.")
    return full_transcript.strip()