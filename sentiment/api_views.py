# sentiment/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SentimentSerializer

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax

# Load the pre-trained RoBERTa model and tokenizer locally
MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)

class SentimentAnalysisAPIView(APIView):
    """
    API endpoint that receives text via POST and returns sentiment scores.
    """
    def post(self, request, format=None):
        # The input is validated using a serializer
        serializer = SentimentSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            # The validated text is tokenized using a pre-trained tokenizer provided by 
            # the Hugging Face Transformers library
            encoded_text = tokenizer(text, return_tensors='pt')
            # The tokenized text is passed to a pre-trained sentiment analysis model 
            # (a RoBERTa model fine-tuned for sentiment analysis) from Hugging Face
            output = model(**encoded_text)
            scores = output[0][0].detach().numpy()
            # use SciPy’s softmax function to transform the model’s raw output scores 
            # into a normalized probability distribution across sentiment classes.
            scores = softmax(scores)
            # {"text": "HI!"}
            result = {
                'text': text,
                'neg': scores[0].item(),
                'neu': scores[1].item(),
                'pos': scores[2].item()
            }
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
