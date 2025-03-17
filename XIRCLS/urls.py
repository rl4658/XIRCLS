# XIRCLS/urls.py
from django.contrib import admin
from django.urls import path
from sentiment.api_views import SentimentAnalysisAPIView
from sentiment.voice_api_views import VoiceVoskAPIView
from sentiment.views import voice_vosk_view  # New view to render the recording page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/sentiment/', SentimentAnalysisAPIView.as_view(), name='api_sentiment'),
    # New API endpoint for Vosk-based transcription
    path('api/voice-vosk/', VoiceVoskAPIView.as_view(), name='api_voice_vosk'),
    # New page for recording voice and showing transcription
    path('voice/', voice_vosk_view, name='voice_vosk'),
]
