from django.shortcuts import render

# Create your views here.
# sentiment/views.py
from django.shortcuts import render

def voice_recognition_view(request):
    """
    Render the voice recognition page that uses the Web Speech API.
    """
    return render(request, 'voice.html')
