from django.test import TestCase

# Create your tests here.
# sentiment/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

class SentimentAPITest(APITestCase):
    def test_sentiment_api(self):
        url = reverse('api_sentiment')
        data = {'text': 'I love this product!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the response contains sentiment scores
        self.assertIn('neg', response.data)
        self.assertIn('neu', response.data)
        self.assertIn('pos', response.data)
