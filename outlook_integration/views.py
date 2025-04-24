# outlook_integration/views.py

import os
import tempfile
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv, find_dotenv
from django.shortcuts import render, redirect
from O365 import Account, FileSystemTokenBackend
from requests.exceptions import HTTPError

# Import your transcription function here; adjust the path as needed
from transcription.transcribe_with_speaker_labels_hf import transcribe_with_speaker_labels

load_dotenv(find_dotenv())

CLIENT_ID = os.environ.get("O365_CLIENT_ID")
CLIENT_SECRET = os.environ.get("O365_CLIENT_SECRET")
# Only Graph API scopes; omit reserved scopes (openid, profile, offline_access)
SCOPES = [
    "https://graph.microsoft.com/Calendars.Read",
    "https://graph.microsoft.com/Files.Read.All",
]
REDIRECT_URI = "http://localhost:8000/outlook/callback/"  # must exactly match your Azure app registration


def get_account():
    creds = (CLIENT_ID, CLIENT_SECRET)
    token_backend = FileSystemTokenBackend(
        token_path=".", token_filename="o365_token.txt"
    )
    return Account(
        creds,
        tenant_id="common",
        token_backend=token_backend,
        auth_flow_type="authorization",
    )


def outlook_index(request):
    """Home page: if authenticated, redirect to dashboard; else show login"""
    account = get_account()
    if account.is_authenticated:
        return redirect("outlook_dashboard")
    return render(request, "outlook_integration/index.html")


def outlook_login(request):
    account = get_account()
    if not account.is_authenticated:
        auth_url, auth_flow = account.con.get_authorization_url(
            requested_scopes=SCOPES, redirect_uri=REDIRECT_URI
        )
        request.session["o365_auth_flow"] = auth_flow
        return redirect(auth_url)
    return redirect("outlook_dashboard")


def outlook_callback(request):
    account = get_account()
    if not account.is_authenticated:
        auth_flow = request.session.pop("o365_auth_flow", None)
        if not auth_flow:
            return redirect("outlook_login")
        callback_url = request.build_absolute_uri()
        account.con.request_token(
            callback_url, flow=auth_flow, redirect_uri=REDIRECT_URI
        )
    return redirect("outlook_dashboard")


def outlook_dashboard(request):
    account = get_account()
    if not account.is_authenticated:
        return redirect("outlook_login")

    # 1) Fetch calendar events for the next 30 days
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)
    q = (
        calendar.new_query("start")
        .greater_equal(now)
        .chain("and")
        .on_attribute("end")
        .less_equal(future)
    )
    events_raw = calendar.get_events(query=q, include_recurring=True)

    events = []
    for ev in events_raw:
        events.append(
            {
                "subject": ev.subject,
                "start": ev.start,
                "end": ev.end,
                "online_meeting_url": ev.online_meeting_url,
                "attachments": [
                    {
                        "name": att.name,
                        "content_url": getattr(att, "content_url", None),
                        "size": getattr(att, "size", None),
                    }
                    for att in getattr(ev, "attachments", [])
                ],
            }
        )

    # 2) Try fetching OneDrive "Recordings" folder by name
    recordings = []
    try:
        storage = account.storage()
        drive = storage.get_default_drive()
        root_folder = drive.get_root_folder()
        for item in root_folder.get_items():
            if item.is_folder and item.name.lower() == "recordings":
                for rec in item.get_items():
                    recordings.append(
                        {
                            "name": rec.name,
                            "item_id": rec.object_id,  # pass this to transcribe
                            "web_url": rec.web_url,
                        }
                    )
                break
    except HTTPError:
        recordings = []

    return render(
        request,
        "outlook_integration/dashboard.html",
        {
            "events": events,
            "recordings": recordings,
        },
    )


def transcribe_recording(request):
    """
    Download the specified recording to a temp file, then run
    speaker-aware transcription on it.
    """
    account = get_account()
    if not account.is_authenticated:
        return redirect("outlook_login")

    item_id = request.GET.get("item_id")
    if not item_id:
        return redirect("outlook_dashboard")

    # 1) Retrieve the file from OneDrive
    storage = account.storage()
    drive = storage.get_default_drive()
    item = drive.get_item(item_id)

    # 2) Download it to a temp directory
    tmp_dir = tempfile.mkdtemp()
    filename = item.name
    success = item.download(to_path=tmp_dir, name=filename)
    if not success:
        return render(
            request,
            "outlook_integration/transcription_error.html",
            {"message": "Could not download recording."},
        )
    file_path = os.path.join(tmp_dir, filename)

    # 3) Run your Hugging Face + diarization transcription
    segments = transcribe_with_speaker_labels(
        mp3_path=file_path,
        model_size="base",
        diarization_model="pyannote/speaker-diarization",
    )

    # 4) Render the results
    return render(
        request,
        "outlook_integration/transcription.html",
        {"segments": segments, "recording_name": filename},
    )


def outlook_logout(request):
    """Log out by deleting stored token and clearing session"""
    tb = FileSystemTokenBackend(token_path=".", token_filename="o365_token.txt")
    tb.delete_token()
    request.session.flush()
    return redirect("outlook_index")
