# transcription/transcribe_with_speaker_labels_hf.py

import os
import tempfile
import warnings

from decouple import config
from dotenv import load_dotenv
from pydub import AudioSegment
from pyannote.audio import Pipeline as PyannotePipeline
from transformers import pipeline as hf_pipeline
import torch  # needed to check for GPU availability

# ─────────────────────────────────────────────────────────────────────────────
# SUPPRESS NON-CRITICAL WARNINGS
# ─────────────────────────────────────────────────────────────────────────────
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# LOAD ENVIRONMENT VARIABLES (for HUGGINGFACE_TOKEN if needed)
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION: CHOOSE MODEL NAMES & CHUNK DURATION
# ─────────────────────────────────────────────────────────────────────────────
#
# Whisper variants (in increasing size/accuracy):
#   - "openai/whisper-tiny.en"   (fastest on English audio)
#   - "openai/whisper-small"     (balanced speed + accuracy)
#   - "openai/whisper-base"      (more accurate, slower)
#
# Default to "openai/whisper-small". Swap as needed.
ASR_MODEL = "openai/whisper-small"

# How many seconds per internal Whisper chunk
CHUNK_LENGTH_SECONDS = 60

# Pyannote speaker‐diarization pipeline name
DIARIZATION_MODEL = "pyannote/speaker-diarization"

# ─────────────────────────────────────────────────────────────────────────────
# AUTH TOKEN (for gated HF + Pyannote models)
# ─────────────────────────────────────────────────────────────────────────────
HF_TOKEN = config("HUGGINGFACE_TOKEN", default=None)

# ─────────────────────────────────────────────────────────────────────────────
# DETECT GPU AVAILABILITY AND SET DEVICE INDEX
# ─────────────────────────────────────────────────────────────────────────────
# If a CUDA‐capable GPU is present, device_index = 0; otherwise -1 (CPU).
DEVICE_INDEX = 0 if torch.cuda.is_available() else -1

# ─────────────────────────────────────────────────────────────────────────────
# PRELOAD HEAVY MODELS AT MODULE LOAD
# ─────────────────────────────────────────────────────────────────────────────

# 1) Pyannote diarization pipeline
diarizer = PyannotePipeline.from_pretrained(
    DIARIZATION_MODEL,
    use_auth_token=HF_TOKEN
)

# 2) Whisper ASR pipeline (chunk_length_s controls how we internally batch)
asr = hf_pipeline(
    "automatic-speech-recognition",
    model=ASR_MODEL,
    chunk_length_s=CHUNK_LENGTH_SECONDS,
    device=DEVICE_INDEX,      # 0 if GPU is available, else -1 (CPU)
    trust_remote_code=True
)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN FUNCTION: TRANSCRIBE WITH SPEAKER LABELS
# ─────────────────────────────────────────────────────────────────────────────

def transcribe_with_speaker_labels(mp3_path: str) -> list[dict]:
    """
    1) Convert MP3 → WAV (mono, 16 kHz).
    2) Run Pyannote diarization on the full WAV to get speaker segments.
    3) For each speaker segment:
         a) Slice out that time interval from the full audio.
         b) Export it to a temp WAV file.
         c) Run Whisper (chunked) on that slice → get text.
         d) Append { "speaker", "start", "end", "text" } if text is non-empty.
    4) Clean up temp files.
    5) Return a list of speaker‐labeled segments.
    """

    # ─────────────────────────────────────────────────────────────────────────
    # 1) CONVERT MP3 → WAV (mono, 16 kHz)
    # ─────────────────────────────────────────────────────────────────────────
    tmp_wav_handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    try:
        audio = AudioSegment.from_file(mp3_path, format="mp3")
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(tmp_wav_handle.name, format="wav")
    except Exception as e:
        tmp_wav_handle.close()
        os.remove(tmp_wav_handle.name)
        raise RuntimeError(f"[Transcription] Failed converting MP3 to WAV: {e}")
    finally:
        tmp_wav_handle.close()

    wav_path = tmp_wav_handle.name

    # ─────────────────────────────────────────────────────────────────────────
    # 2) RUN PYANNOTE DIARIZATION ON THE FULL WAV
    # ─────────────────────────────────────────────────────────────────────────
    diarization = diarizer(wav_path)

    # ─────────────────────────────────────────────────────────────────────────
    # 3) LOAD FULL WAV INTO PYDUB FOR SLICING
    # ─────────────────────────────────────────────────────────────────────────
    try:
        full_audio = AudioSegment.from_wav(wav_path)
    except Exception as e:
        os.remove(wav_path)
        raise RuntimeError(f"[Transcription] Failed loading WAV into pydub: {e}")

    segments = []

    # 3a) Iterate over each speaker segment
    for segment, _, speaker_label in diarization.itertracks(yield_label=True):
        st, et = segment.start, segment.end  # floats in seconds
        start_ms = int(st * 1000)
        end_ms   = int(et * 1000)

        # 3b) Slice that portion out of the full audio
        slice_audio = full_audio[start_ms:end_ms]

        # 3c) Export slice to its own temp WAV
        tmp_slice_handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        try:
            slice_audio.export(tmp_slice_handle.name, format="wav")
        except Exception as e:
            tmp_slice_handle.close()
            os.remove(tmp_slice_handle.name)
            continue  # skip this segment on failure
        finally:
            tmp_slice_handle.close()

        slice_path = tmp_slice_handle.name

        # 3d) Run Whisper (chunked) on that slice
        try:
            result = asr(slice_path)
            text = result.get("text", "").strip()
        except Exception:
            text = ""

        # 3e) Record if non-empty
        if text:
            segments.append({
                "speaker": speaker_label,
                "start": st,
                "end": et,
                "text": text
            })

        # 3f) Clean up the slice WAV
        try:
            os.remove(slice_path)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # 4) CLEAN UP MAIN WAV FILE
    # ─────────────────────────────────────────────────────────────────────────
    try:
        os.remove(wav_path)
    except Exception:
        pass

    return segments
