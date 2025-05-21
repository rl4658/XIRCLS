# transcription/transcribe_with_speaker_labels_hf.py

"""
This module provides a function to transcribe an MP3 file with speaker diarization.
The MP3 file is expected to be downloaded locally by the Django view before calling this function.
"""

import warnings
# Suppress non-critical warnings
warnings.filterwarnings('ignore')

# Try copy strategy for SpeechBrain cache on Windows
try:
    from speechbrain.utils.fetching import set_local_strategy
    set_local_strategy("copy")
except ImportError:
    pass

import os
import tempfile
from pydub import AudioSegment
from decouple import config
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env
load_dotenv(find_dotenv())

from pyannote.audio import Pipeline as PyannotePipeline
from transformers import pipeline

# Hugging Face token for gated models
HF_TOKEN = config('HUGGINGFACE_TOKEN')


def transcribe_with_speaker_labels(
    mp3_path: str,
    asr_model: str = "openai/whisper-base",
    diarization_model: str = "pyannote/speaker-diarization",
    chunk_length_s: float = 30.0,
) -> list[dict]:
    """
    Transcribe an MP3 via speaker diarization + ASR.
    The mp3_path file is downloaded by the Django view.

    Returns:
        List of {speaker, start, end, text} dicts.
    """
    print(f"[Transcriber] Starting transcription for {mp3_path}")

    # 1) Convert MP3 → WAV, mono 16kHz
    print("[Transcriber] Converting MP3 to WAV...")
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    audio = AudioSegment.from_file(mp3_path, format="mp3")
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(tmp_wav.name, format="wav")
    tmp_wav.close()  # release file handle so others can access

    # 2) Speaker diarization
    print("[Transcriber] Running speaker diarization...")
    diarizer = PyannotePipeline.from_pretrained(
        diarization_model,
        use_auth_token=HF_TOKEN
    )
    diarization = diarizer(tmp_wav.name)

    # 3) ASR pipeline (Whisper)
    print("[Transcriber] Running ASR (Whisper) transcription...")
    asr = pipeline(
        "automatic-speech-recognition",
        model=asr_model,
        chunk_length_s=chunk_length_s,
        return_timestamps="word",
        device=-1,
        trust_remote_code=True
    )
    asr_result = asr(tmp_wav.name)
    chunks = asr_result.get("chunks", [])

    # 4) Align words to speaker segments
    print("[Transcriber] Aligning words to speaker segments...")
    segments = []
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        st, et = segment.start, segment.end
        words = []
        for w in chunks:
            ts = w.get("timestamp")
            if (
                isinstance(ts, (list, tuple)) and
                ts[0] is not None and ts[1] is not None and
                ts[0] >= st and ts[1] <= et
            ):
                words.append(w.get("text", ""))
        text = "".join(words).strip()
        if text:
            segments.append({
                "speaker": speaker,
                "start": st,
                "end": et,
                "text": text
            })

    # Cleanup
    print(f"[Transcriber] Cleaning up temp file {tmp_wav.name}")
    try:
        os.remove(tmp_wav.name)
    except PermissionError:
        print(f"[Transcriber] Warning: could not delete temp file {tmp_wav.name}")

    print("[Transcriber] Transcription complete.")
    return segments
