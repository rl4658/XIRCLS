# transcription/transcribe_with_speaker_labels_hf.py

import os
import tempfile
from pydub import AudioSegment
from decouple import config
from pyannote.audio import Pipeline as PyannotePipeline
from transformers import pipeline

# Load your Hugging Face token from environment
HF_TOKEN = config('HUGGINGFACE_TOKEN')


def transcribe_with_speaker_labels(
    mp3_path: str,
    asr_model: str = "openai/whisper-base",
    diarization_model: str = "pyannote/speaker-diarization",
    chunk_length_s: float = 30.0,
) -> list[dict]:
    """
    Transcribe an audio file via Hugging Face's Whisper ASR and Pyannote speaker diarization.

    Returns:
        A list of dicts with keys: speaker, start, end, text.
    """

    # 1) Convert MP3 → WAV, mono 16 kHz
    audio = AudioSegment.from_file(mp3_path, format="mp3")
    audio = audio.set_frame_rate(16000).set_channels(1)
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    audio.export(tmp_wav.name, format="wav")

    # 2) Run speaker diarization using Pyannote-Audio
    diarizer = PyannotePipeline.from_pretrained(
        diarization_model,
        use_auth_token=HF_TOKEN
    )
    diarization = diarizer(tmp_wav.name)  # pyannote.core.Annotation

    # 3) Run ASR (Whisper) with word timestamps
    asr = pipeline(
        "automatic-speech-recognition",
        model=asr_model,
        chunk_length_s=chunk_length_s,
        return_timestamps="word",
        device=-1,          # change to 0 if using GPU
        trust_remote_code=True,
        use_auth_token=HF_TOKEN
    )
    asr_result = asr(tmp_wav.name)
    chunks = asr_result.get("chunks", [])

    # 4) Align words to speaker segments
    segments = []
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        st, et = segment.start, segment.end
        words = [
            w["text"] for w in chunks
            if w["timestamp"][0] >= st and w["timestamp"][1] <= et
        ]
        text = "".join(words).strip()
        if text:
            segments.append({
                "speaker": speaker,
                "start": st,
                "end": et,
                "text": text
            })

    # Cleanup temporary file
    os.remove(tmp_wav.name)

    return segments
