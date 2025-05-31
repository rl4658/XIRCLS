# XIRCLS

> **AI‑powered sentiment & voice analysis platform with Outlook meeting transcription — built with Django, DRF, Whisper, Vosk & PyAnnote.**

---

## Table of Contents

1. [Features](#features)
2. [Architecture Overview](#architecture-overview)
3. [Getting Started](#getting-started)

   * [Prerequisites](#prerequisites)
   * [Installation](#installation)
   * [Environment Variables](#environment-variables)
   * [Database Migration](#database-migration)
   * [Running the Dev Server](#running-the-development-server)
4. [Usage](#usage)

   * [Sentiment Analysis API](#sentiment-analysis-api)
   * [Voice Recognition API (Vosk)](#voice-recognition-api-vosks)
   * [Outlook Integration Dashboard](#outlook-integration-dashboard)
5. [Project Structure](#project-structure)
6. [Running Tests](#running-tests)
7. [Contributing](#contributing)
8. [License](#license)

---

## Features

| Module                                                                                                                                | Highlights                                                                            |
| ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **Sentiment (REST API)**                                                                                                              | • RoBERTa‑based sentiment model from *cardiffnlp/twitter‑roberta‑base‑sentiment*      |
| • `/api/sentiment/` POST endpoint returns **neg/neu/pos** scores                                                                      |                                                                                       |
| **Voice API (Vosk)**                                                                                                                  | • On‑device speech recognition with the bundled US English Vosk model                 |
| • Accepts WebM, converts to 16 kHz mono WAV, returns plain text                                                                       |                                                                                       |
| **Outlook Integration**                                                                                                               | • OAuth 2 flow via `O365` SDK                                                         |
| • Fetches next 30 days of calendar events                                                                                             |                                                                                       |
| • Scans OneDrive **Recordings** folder and enables one‑click **speaker‑aware** transcription using Whisper ASR + PyAnnote diarization |                                                                                       |
| **Front‑End Templates**                                                                                                               | Minimal responsive HTML dashboards for login, meeting overview & transcription viewer |

---

## Architecture Overview

```
│  Django 5.1.6 (ASGI/W   SGI)
│
├── sentiment                (DRF API, RoBERTa)
├── outlook_integration      (O365, templates)
├── transcription            (HF Whisper + PyAnnote)
├── vosk_model/              (offline ASR model)
└── db.sqlite3               (default SQLite dev DB)
```

**Tech Stack:** Django 5 · Django REST Framework · Vosk · Hugging Face Transformers · PyAnnote · pydub · O365 SDK · FFmpeg.

---

## Getting Started

### Prerequisites

* **Python 3.11 or 3.12**
* **FFmpeg** (for audio conversion)
* Git, virtualenv/venv

### Installation

```bash
# 1. Clone repository
$ git clone https://github.com/ray-xircls/xircls.git
$ cd xircls

# 2. Create & activate virtual environment
$ python -m venv .venv
$ source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
$ pip install --upgrade pip
$ pip install -r requirements.txt   # or see requirements snippet below
```

<details>
<summary>Minimal requirements.txt</summary>

```
Django==5.1.6
 djangorestframework
 transformers
 scipy
 vosk
 pydub
 O365
 python-decouple
 python-dotenv
 pyannote.audio
 speechbrain  # for HF gated models cache helper
```

</details>

### Environment Variables

Create a **.env** file at the repo root:

```
# Django
DJANGO_SECRET_KEY="change‑me‑in‑prod"

# Microsoft Graph (Azure AD app)
O365_CLIENT_ID=<your‑app‑id>
O365_CLIENT_SECRET=<your‑secret>

# Hugging Face (for diarization pipeline)
HUGGINGFACE_TOKEN=<optional for gated models>
```

### Database Migration

```bash
$ python manage.py migrate
```

### Running the Development Server

```bash
$ python manage.py runserver
# Visit http://127.0.0.1:8000/
```

---

## Usage

### Sentiment Analysis API

```bash
curl -X POST http://127.0.0.1:8000/api/sentiment/ \
     -H "Content-Type: application/json" \
     -d '{"text": "I love XIRCLS!"}'
```

Response:

```json
{
  "text": "I love XIRCLS!",
  "neg": 0.02,
  "neu": 0.17,
  "pos": 0.81
}
```

### Voice Recognition API (Vosk)

*Open* `http://127.0.0.1:8000/voice/` in a modern browser → record speech → server returns live transcript via `/api/voice-vosk/`.

### Outlook Integration Dashboard

1. Navigate to `http://127.0.0.1:8000/outlook/`
2. Sign in with your Microsoft 365 account.
3. View upcoming meetings and OneDrive recordings.
4. Click **Transcribe** → Whisper + diarization → readable transcript per speaker.

> **Note:** your Azure AD app’s redirect URI **must** match `REDIRECT_URI` in `outlook_integration/views.py` (default: `http://localhost:8000/outlook/callback/`).

---

## Project Structure

```
├── XIRCLS/                  # Django project settings/urls
├── outlook_integration/     # Outlook app (views, templates)
├── sentiment/               # Sentiment API app
├── transcription/           # Speaker‑aware transcription helper
├── vosk_model/              # Pre‑downloaded Vosk US model (~50 MB)
├── manage.py                # Django CLI
└── README.md
```

---

## Running Tests

```bash
$ python manage.py runserver
```

---

## Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.
Make sure `black` and `isort` pass pre‑commit hooks and include relevant tests.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

* [CardiffNLP](https://github.com/cardiffnlp) for the RoBERTa sentiment model.
* [Vosk Speech Recognition](https://alphacephei.com/vosk).
* [PyAnnote](https://github.com/pyannote/pyannote-audio) for diarization.
* [OpenAI Whisper](https://github.com/openai/whisper) for ASR.
