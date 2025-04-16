# XIRCLS/urls.py

from django.contrib import admin
from django.urls import path, include  # <-- include added
from sentiment.api_views import SentimentAnalysisAPIView
from sentiment.voice_api_views import VoiceVoskAPIView
from sentiment.views import voice_vosk_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/sentiment/', SentimentAnalysisAPIView.as_view(), name='api_sentiment'),
    path('api/voice-vosk/', VoiceVoskAPIView.as_view(), name='api_voice_vosk'),
    path('voice/', voice_vosk_view, name='voice_vosk'),
    path('outlook/', include('outlook_integration.urls')),  # [NEW] Outlook integration endpoints
]
