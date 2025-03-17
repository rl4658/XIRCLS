# sentiment/voice_api_views.py
import os
import subprocess
import wave
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from vosk import Model, KaldiRecognizer

# Determine project root from current file location (assuming sentiment/ is inside your project)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'vosk_model')  # Make sure your Vosk model is extracted here

if not os.path.exists(MODEL_PATH):
    raise Exception("Vosk model not found. Please download and extract a model to the 'vosk_model' folder.")

# Load the Vosk model (this might take a few seconds)
vosk_model = Model(MODEL_PATH)

class VoiceVoskAPIView(APIView):
    """
    API endpoint that receives an audio file (WebM) via POST, converts it to WAV,
    processes it with Vosk, and returns the recognized text.
    """
    def post(self, request, format=None):
        if 'audio' not in request.FILES:
            return Response({"error": "No audio file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        audio_file = request.FILES['audio']
        # Save the uploaded file temporarily
        temp_webm_path = 'temp_audio.webm'
        with open(temp_webm_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)
        
        # Convert the WebM file to a WAV file using ffmpeg
        temp_wav_path = 'temp_audio.wav'
        try:
            # ffmpeg command to convert: input -> 16kHz, mono, 16-bit PCM WAV
            cmd = ['ffmpeg', '-y', '-i', temp_webm_path, '-ar', '16000', '-ac', '1', '-f', 'wav', temp_wav_path]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            os.remove(temp_webm_path)
            return Response({"error": "Error converting audio file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Open the WAV file and process with Vosk
        try:
            wf = wave.open(temp_wav_path, 'rb')
        except Exception as e:
            os.remove(temp_webm_path)
            os.remove(temp_wav_path)
            return Response({"error": f"Error processing WAV file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure the WAV file is in the correct format (mono, 16-bit)
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            wf.close()
            os.remove(temp_webm_path)
            os.remove(temp_wav_path)
            return Response({"error": "Audio file must be mono PCM WAV (16-bit)."}, status=status.HTTP_400_BAD_REQUEST)
        
        rec = KaldiRecognizer(vosk_model, wf.getframerate())
        rec.SetWords(True)
        
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                results.append(res.get("text", ""))
        final_res = json.loads(rec.FinalResult())
        results.append(final_res.get("text", ""))
        
        wf.close()
        os.remove(temp_webm_path)
        os.remove(temp_wav_path)
        
        recognized_text = " ".join(results).strip()
        return Response({"recognized_text": recognized_text}, status=status.HTTP_200_OK)
