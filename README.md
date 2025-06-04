# XIRCLS

> **AI-powered sentiment & voice analysis platform with Outlook meeting transcription and actionable task extraction — built with Django, DRF, Whisper, Vosk, PyAnnote & spaCy.**

---

## Table of Contents

1. [Features](#features)
2. [Architecture Overview](#architecture‐overview)
3. [Getting Started](#getting‐started)

   * [Prerequisites](#prerequisites)
   * [Installation](#installation)
   * [spaCy Setup](#spacy‐setup)
   * [Environment Variables](#environment‐variables)
   * [Database Migration](#database‐migration)
   * [Running the Dev Server](#running‐the‐development‐server)
4. [Usage](#usage)

   * [Sentiment Analysis API](#sentiment‐analysis‐api)
   * [Voice Recognition API (Vosk)](#voice‐recognition‐api‐vosks)
   * [Outlook Integration Dashboard & Transcription](#outlook‐integration‐dashboard‐transcription)
   * [Task Extraction](#task‐extraction)
5. [Project Structure](#project‐structure)
6. [Running Tests](#running‐tests)
7. [Contributing](#contributing)
8. [License](#license)
9. [Acknowledgements](#acknowledgements)

---

## Features

| Module                                                                                                                                | Highlights                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Sentiment (REST API)**                                                                                                              | • RoBERTa-based sentiment model from *cardiffnlp/twitter-roberta-base-sentiment*                              |
|                                                                                                                                       | • `/api/sentiment/` POST endpoint returns **neg/neu/pos** scores                                              |
| **Voice API (Vosk)**                                                                                                                  | • On-device speech recognition with the bundled US English Vosk model                                         |
|                                                                                                                                       | • Accepts WebM, converts to 16 kHz mono WAV, returns plain text                                               |
| **Outlook Integration & Transcription**                                                                                               | • OAuth 2 flow via `O365` SDK                                                                                 |
|                                                                                                                                       | • Fetches next 30 days of calendar events                                                                     |
|                                                                                                                                       | • Scans OneDrive **Recordings** folder and enables one-click **speaker-aware** transcription using Whisper ASR + PyAnnote diarization |
| **Task Extraction**                                                                                                                   | • Uses spaCy to identify actionable tasks from meeting transcripts and displays them alongside the transcript |
| **Front-End Templates**                                                                                                               | Minimal responsive HTML dashboards for login, meeting overview, transcription viewer, and task list           |

---

## Architecture Overview

```
│  Django 5.1.6 (ASGI/W SGI)
│
├── sentiment                  (DRF API, RoBERTa)
├── outlook_integration        (O365, templates, spaCy task extraction)
├── transcription              (HF Whisper + PyAnnote)
├── vosk_model/                (offline ASR model)
└── db.sqlite3                 (default SQLite dev DB)
```

**Tech Stack:**
Django 5 · Django REST Framework · Vosk · Hugging Face Transformers · PyAnnote · pydub · spaCy · O365 SDK · FFmpeg.

---

## Getting Started

### Prerequisites

* **Python 3.11 or 3.12**
* **FFmpeg** (for audio conversion)
* Git, virtualenv/venv

---

### Installation

1. **Clone the repository**

   ```bash
   git clone git@github.com:ray-xircls/xircls.git
   cd xircls
   ```

2. **Create & activate a Python virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

<details>
<summary>Minimal <code>requirements.txt</code></summary>

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
speechbrain        # for HF gated models cache helper
spacy              # for task extraction
```

</details>

---

### spaCy Setup

1. **Install spaCy** (if not already in your `requirements.txt`):

   ```bash
   pip install spacy
   ```

2. **Download the English model** (`en_core_web_sm`):

   ```bash
   python -m spacy download en_core_web_sm
   ```

This equips your app to run rule-based task extraction on each meeting transcript.

---

### Environment Variables

Create a file named `.env` at the repository root with these entries:

```
# Django
DJANGO_SECRET_KEY="change-me-in-prod"

# Microsoft Graph (Azure AD app)
O365_CLIENT_ID=<your-app-id>
O365_CLIENT_SECRET=<your-secret>

# Hugging Face (for diarization pipeline, optional)
HUGGINGFACE_TOKEN=<optional for gated models>
```

---

### Database Migration

Run Django migrations:

```bash
python manage.py migrate
```

---

### Running the Development Server

Start the Django dev server:

```bash
python manage.py runserver
```

Then open your browser to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## Usage

### Sentiment Analysis API

Send a `POST` request with JSON `{ "text": "..." }` to `/api/sentiment/`.

```bash
curl -X POST http://127.0.0.1:8000/api/sentiment/ \
     -H "Content-Type: application/json" \
     -d '{"text": "I love XIRCLS!"}'
```

**Response:**

```json
{
  "text": "I love XIRCLS!",
  "neg": 0.02,
  "neu": 0.17,
  "pos": 0.81
}
```

---

### Voice Recognition API (Vosk)

Visit [http://127.0.0.1:8000/voice/](http://127.0.0.1:8000/voice/) in a modern browser.

* **Start Recording** → speak into your microphone
* **Stop Recording** → server converts WebM → WAV → processes with Vosk → returns recognized text.

---

### Outlook Integration Dashboard & Transcription

1. **Navigate to** [http://127.0.0.1:8000/outlook/](http://127.0.0.1:8000/outlook/)
2. **Login with Outlook** (OAuth 2 via `O365` SDK)
3. **Dashboard**:

   * Shows your next 30 days of calendar events
   * Lists OneDrive “Recordings” folder items (MP3/WebM meeting recordings)
   * Click **Transcribe** next to a recording → Django will:

     1. Download the recording from OneDrive
     2. Run speaker-aware transcription using Whisper + PyAnnote
     3. Join all segments into a full transcript string
     4. Extract actionable tasks with spaCy
     5. Render **transcription.html** with both the per‐speaker transcript and a list of extracted tasks

**Example transcription URL flow:**

```
http://127.0.0.1:8000/outlook/transcribe/?item_id=<OneDrive-item-ID>
```

---

### Task Extraction

After transcription, we automatically extract and list all actionable items (e.g., “Schedule next planning meeting”, “Send budget report”) by running a spaCy‐based rule extractor against the combined transcript.

* **Location of logic**: `outlook_integration/task_extraction.py`

  * Splits the transcript into sentences
  * Flags sentences beginning with an imperative verb (`VB` tag) or containing trigger keywords (e.g., “should”, “action:”, “need to”)
  * Returns a list of cleaned sentences identified as tasks

* **Displayed in template**:

  * `outlook_integration/templates/outlook_integration/transcription.html`
  * Section titled **“Extracted Action Items”** appears below the transcript.

This process is entirely open-source (spaCy) and incurs no external API costs.

---

## Project Structure

```
XIRCLS/                  # Django project settings & URLs
├── __init__.py
├── asgi.py
├── settings.py
├── urls.py
└── wsgi.py

outlook_integration/     # Outlook Integration app
├── __init__.py
├── apps.py
├── task_extraction.py   ←- Rule-based task extraction (spaCy)
├── urls.py
├── views.py
└── templates/
    └── outlook_integration/
        ├── index.html
        ├── dashboard.html
        └── transcription.html   ←- Shows both transcript & actionable tasks

sentiment/               # Sentiment Analysis API app
├── __init__.py
├── admin.py
├── api_views.py
├── apps.py
├── migrations/
├── models.py
├── serializers.py
├── tests.py
├── views.py
└── templates/
    └── voice_vosk.html

transcription/           # Helper for speaker-aware transcription
├── __pycache__/
└── transcribe_with_speaker_labels_hf.py

vosk_model/              # Pre-downloaded Vosk US English ASR model (~50 MB)
└── ... (model files and configs)

db.sqlite3               # SQLite development database

manage.py                # Django CLI

README.md                # ←- This README
```

---

## Running Tests

Currently, the only tests cover the Sentiment API. To run them:

```bash
python manage.py test sentiment
```

---

## Contributing

1. **Fork** the repository.
2. **Create** a feature branch:

   ```bash
   git checkout -b feature/your‐feature-name
   ```
3. **Commit** your changes (follow conventional commits or clear messaging).
4. **Push** to your fork & open a Pull Request.
5. Ensure that `black` and `isort` pass any pre-commit hooks; include tests for new functionality.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

* [CardiffNLP](https://github.com/cardiffnlp) for the RoBERTa sentiment model.
* [Vosk Speech Recognition](https://alphacephei.com/vosk).
* [PyAnnote](https://github.com/pyannote/pyannote-audio) for diarization.
* [OpenAI Whisper](https://github.com/openai/whisper) for ASR.
* [spaCy](https://spacy.io/) for open-source NLP and task extraction.
