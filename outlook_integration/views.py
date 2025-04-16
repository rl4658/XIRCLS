# outlook_integration/views.py

import os
from dotenv import load_dotenv, find_dotenv
from django.shortcuts import render, redirect
from O365 import Account, FileSystemTokenBackend

# Force dotenv to search and load the .env file from the project root
load_dotenv(find_dotenv())

# Retrieve credentials from environment variables
CLIENT_ID = os.environ.get('O365_CLIENT_ID')
CLIENT_SECRET = os.environ.get('O365_CLIENT_SECRET')

# (Optional) Debug printing to verify credentials are loaded (remove once confirmed)
print("CLIENT_ID:", CLIENT_ID)
print("CLIENT_SECRET:", CLIENT_SECRET)

# Define the required scopes for accessing calendar events
SCOPES = ['https://graph.microsoft.com/Calendars.Read']

def get_account():
    """
    Creates an O365 Account instance using credentials loaded from the environment.
    The auth_flow_type 'authorization' is used.
    """
    credentials = (CLIENT_ID, CLIENT_SECRET)
    token_backend = FileSystemTokenBackend(token_path='.', token_filename='o365_token.txt')
    return Account(credentials, token_backend=token_backend, auth_flow_type='authorization')

def outlook_login(request):
    """
    Initiates the OAuth2 authentication process with Microsoft.
    """
    account = get_account()
    if not account.is_authenticated:
        # Use 'requested_scopes' instead of 'scopes'
        auth_url, state = account.con.get_authorization_url(requested_scopes=SCOPES)
        request.session['o365_auth_state'] = state
        return redirect(auth_url)
    return redirect('outlook_dashboard')


def outlook_callback(request):
    """
    Handles the OAuth2 callback from Microsoft.
    """
    account = get_account()
    code = request.GET.get('code')
    if code:
        account.con.request_token(code, state=request.session.get('o365_auth_state'))
    return redirect('outlook_dashboard')

def outlook_dashboard(request):
    """
    Retrieves calendar events from Outlook and renders a dashboard.
    """
    account = get_account()
    if not account.is_authenticated:
        return redirect('outlook_login')

    schedule = account.schedule()
    calendar = schedule.get_default_calendar()
    events = list(calendar.get_events())
    return render(request, 'outlook_integration/dashboard.html', {'events': events})
