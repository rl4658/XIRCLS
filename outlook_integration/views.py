# outlook_integration/views.py

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv, find_dotenv
from django.shortcuts import render, redirect
from O365 import Account, FileSystemTokenBackend

load_dotenv(find_dotenv())

CLIENT_ID = os.environ.get('O365_CLIENT_ID')
CLIENT_SECRET = os.environ.get('O365_CLIENT_SECRET')
SCOPES = ['https://graph.microsoft.com/Calendars.Read']
REDIRECT_URI = 'http://localhost:8000/outlook/callback/'  # must match your Azure app registration

def get_account():
    creds = (CLIENT_ID, CLIENT_SECRET)
    token_backend = FileSystemTokenBackend(
        token_path='.',
        token_filename='o365_token.txt'
    )
    return Account(
        creds,
        tenant_id='common',
        token_backend=token_backend,
        auth_flow_type='authorization'
    )

def outlook_login(request):
    account = get_account()
    if not account.is_authenticated:
        auth_url, auth_flow = account.con.get_authorization_url(
            requested_scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        request.session['o365_auth_flow'] = auth_flow
        return redirect(auth_url)
    return redirect('outlook_dashboard')

def outlook_callback(request):
    account = get_account()
    if not account.is_authenticated:
        auth_flow = request.session.pop('o365_auth_flow', None)
        if not auth_flow:
            return redirect('outlook_login')
        callback_url = request.build_absolute_uri()
        account.con.request_token(
            callback_url,
            flow=auth_flow,
            redirect_uri=REDIRECT_URI
        )
    return redirect('outlook_dashboard')

def outlook_dashboard(request):
    account = get_account()
    if not account.is_authenticated:
        return redirect('outlook_login')

    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    # define a window from now until 30 days out
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)

    # build a query: start >= now AND end <= future
    q = calendar.new_query('start').greater_equal(now) \
                              .chain('and').on_attribute('end').less_equal(future)

    # fetch events in that window, including recurring
    events = calendar.get_events(query=q, include_recurring=True)

    enriched = []
    for ev in events:
        evd = {
            'subject': ev.subject,
            'start': ev.start,
            'end': ev.end,
            'online_meeting_url': ev.online_meeting_url,
            'attachments': []
        }
        try:
            for att in ev.attachments:
                evd['attachments'].append({
                    'name': att.name,
                    'content_url': getattr(att, 'content_url', None),
                    'size': getattr(att, 'size', None),
                })
        except Exception:
            pass
        enriched.append(evd)

    return render(request, 'outlook_integration/dashboard.html', {'events': enriched})
