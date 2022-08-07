"""
curl -L -X POST 'https://koreacentral.api.cognitive.microsoft.com/speechtotext/v3.0/transcriptions' -H 'Content-Type: application/json' -H 'Accept: application/json' -H 'Ocp-Apim-Subscription-Key: 18c20da6bd3447238718e3a5738a5ea1' --data-raw '{
    "contentUrls": [
      "https://www2.cs.uic.edu/~i101/SoundFiles/preamble.wav",
    ],
    "properties": {
      "diarizationEnabled": false,
      "wordLevelTimestampsEnabled": true,
      "punctuationMode": "DictatedAndAutomatic",
      "profanityFilterMode": "Masked"
    },
    "locale": "en-US",
    "displayName": "Transcription of file using default model for en-US"
  }'
"""