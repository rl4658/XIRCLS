# sentiment/views.py
from django.shortcuts import render

def voice_vosk_view(request):
    """Render the voice recording page that uses Vosk API on the server."""
    return render(request, 'voice_vosk.html')
