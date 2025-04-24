# transcription/transcribe_with_speaker_labels_hf.py

import os
import tempfile
from pydub import AudioSegment
from transformers import pipeline

def transcribe_with_speaker_labels(
    mp3_path: str,
    asr_model: str = "openai/whisper-base",
    diarization_model: str = "pyannote/speaker-diarization",
    chunk_length_s: float = 30.0,
) -> list[dict]:
    """
    Transcribe an MP3 via HF ASR + speaker diarization pipelines.
    Returns a list of {"speaker","start","end","text"} dicts.
    """

    # 1) Convert MP3 → WAV, mono 16 kHz
    audio = AudioSegment.from_file(mp3_path, format="mp3")
    audio = audio.set_frame_rate(16000).set_channels(1)
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    audio.export(tmp_wav.name, format="wav")

    # 2) Run speaker diarization
    diarizer = pipeline(
        "speaker-diarization",
        model=diarization_model,
        trust_remote_code=True
    )
    diarization = diarizer(tmp_wav.name)
    # diarization: list of {"start":float,"end":float,"label":str}

    # 3) Run ASR (Whisper) with word timestamps
    asr = pipeline(
        "automatic-speech-recognition",
        model=asr_model,
        chunk_length_s=chunk_length_s,
        return_timestamps="word",
        device=-1,  # CPU; change to 0 for GPU
        trust_remote_code=True
    )
    result = asr(tmp_wav.name)
    chunks = result.get("chunks", [])
    # chunks: list of {"text":str,"timestamp":[start,end]}

    # 4) Align words → speakers
    segments = []
    for turn in diarization:
        st, et, speaker = turn["start"], turn["end"], turn["label"]
        words = [
            w["text"] for w in chunks
            if w["timestamp"][0] >= st and w["timestamp"][1] <= et
        ]
        text = "".join(words).strip()
        if text:
            segments.append({
                "speaker": speaker,
                "start":    st,
                "end":      et,
                "text":     text
            })

    # cleanup
    os.remove(tmp_wav.name)
    return segments
