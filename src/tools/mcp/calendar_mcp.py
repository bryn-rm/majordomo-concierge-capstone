from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying scopes, delete config/token.json and re-auth.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# Paths relative to project root
CREDENTIALS_PATH = os.path.join("config", "credentials.json")
TOKEN_PATH = os.path.join("config", "token.json")


def _get_calendar_service():
    """
    Build and return an authenticated Google Calendar service client.

    Uses OAuth 2.0 with:
    - config/credentials.json  (downloaded from Google Cloud)
    - config/token.json        (created automatically after first auth)
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If there are no (valid) credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise RuntimeError(
                    f"Google Calendar credentials not found at {CREDENTIALS_PATH}. "
                    "Download OAuth client credentials JSON from Google Cloud "
                    "Console and place it there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service


def add_event(
    user_email: Optional[str],
    title: str,
    start_iso: str,
    end_iso: Optional[str] = None,
    description: Optional[str] = None,
    calendar_id: str = "primary",
) -> str:
    """
    Add an event to Google Calendar.

    Args:
        user_email: optional; can be used in description or attendees later.
        title: event summary/title.
        start_iso: ISO8601 start time (e.g. "2025-12-02T18:00:00").
        end_iso: ISO8601 end time (defaults to +1 hour if None).
        description: event description.
        calendar_id: which calendar to insert into ("primary" by default).

    Returns:
        The created event's id.
    """
    service = _get_calendar_service()

    start_dt = datetime.fromisoformat(start_iso)
    if end_iso is None:
        end_dt = start_dt + timedelta(hours=1)
    else:
        end_dt = datetime.fromisoformat(end_iso)

    event_body = {
        "summary": title,
        "description": description or "",
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "UTC",  # adjust or parameterise if needed
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "UTC",
        },
    }

    event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
    return event.get("id")


def list_upcoming_events(
    max_events: int = 10,
    calendar_id: str = "primary",
) -> List[Dict[str, Any]]:
    """
    List upcoming events from Google Calendar.

    Args:
        max_events: max number of events to return.
        calendar_id: which calendar to read (default: "primary").

    Returns:
        List of event dicts with id, summary, start, end.
    """
    service = _get_calendar_service()

    now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_events,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    simplified: List[Dict[str, Any]] = []
    for ev in events:
        simplified.append(
            {
                "id": ev.get("id"),
                "summary": ev.get("summary"),
                "start": ev.get("start"),
                "end": ev.get("end"),
                "location": ev.get("location"),
            }
        )
    return simplified
