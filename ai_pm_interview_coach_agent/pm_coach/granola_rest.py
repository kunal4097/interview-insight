"""
Granola's key-based REST API client (public-api.granola.ai) - the "paste an API key" connect
path (Business/Enterprise plans only; see granola_mcp.py for the no-key OAuth alternative that
works on any plan). GranolaAPIError is the one exception type both Granola clients raise;
granola_rest owns it since the REST client was written first.
"""
import requests

from .config import GRANOLA_BASE_URL


class GranolaAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def granola_request(api_key: str, path: str, params: dict | None = None) -> dict:
    try:
        resp = requests.get(
            f"{GRANOLA_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {api_key}"},
            params=params or {},
            timeout=15,
        )
    except requests.RequestException as e:
        raise GranolaAPIError(0, f"Network error reaching Granola: {e}")

    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 401:
        raise GranolaAPIError(401, "Invalid Granola API key.")
    if resp.status_code == 403:
        raise GranolaAPIError(403, "This key doesn't have access. Granola API access requires a Business or Enterprise plan.")
    if resp.status_code == 404:
        raise GranolaAPIError(404, "Not found.")
    if resp.status_code == 413:
        raise GranolaAPIError(413, "TRANSCRIPT_TOO_LARGE")
    if resp.status_code == 429:
        raise GranolaAPIError(429, "Rate limited by Granola. Wait a few seconds and try again.")
    raise GranolaAPIError(resp.status_code, f"Granola API error ({resp.status_code}).")


def granola_list_notes(api_key: str, folder_id: str | None = None, cursor: str | None = None, page_size: int = 20):
    params: dict = {"page_size": page_size}
    if folder_id:
        params["folder_id"] = folder_id
    if cursor:
        params["cursor"] = cursor
    data = granola_request(api_key, "/notes", params)
    return data["notes"], data["hasMore"], data["cursor"]


def granola_list_all_folders(api_key: str, cap: int = 200) -> list:
    folders, cursor = [], None
    while True:
        params = {"page_size": 30}
        if cursor:
            params["cursor"] = cursor
        data = granola_request(api_key, "/folders", params)
        folders.extend(data["folders"])
        cursor = data["cursor"]
        if not data["hasMore"] or not cursor or len(folders) >= cap:
            break
    return folders


def granola_get_transcript_full(api_key: str, note_id: str, cap_items: int = 4000) -> list:
    items, cursor = [], None
    while True:
        params: dict = {"page_size": 100}
        if cursor:
            params["cursor"] = cursor
        data = granola_request(api_key, f"/notes/{note_id}/transcript", params)
        items.extend(data["transcript"])
        cursor = data["cursor"]
        if not data["hasMore"] or not cursor or len(items) >= cap_items:
            break
    return items


def granola_get_note(api_key: str, note_id: str) -> dict:
    """Fetch a note with its transcript. Falls back to the paginated transcript
    endpoint when the inline transcript is too large for Get Note to return."""
    try:
        return granola_request(api_key, f"/notes/{note_id}", {"include": "transcript"})
    except GranolaAPIError as e:
        if e.status_code != 413:
            raise
        note = granola_request(api_key, f"/notes/{note_id}", {})
        note["transcript"] = granola_get_transcript_full(api_key, note_id)
        return note


def format_granola_transcript(items: list) -> str:
    lines = []
    attribution_labels = {"me": "You", "them": "Other speaker"}
    for item in items:
        speaker = item.get("speaker") or {}
        attribution = speaker.get("attribution")
        label = (
            speaker.get("name")
            or (attribution_labels.get(attribution) if attribution else None)
            or speaker.get("diarization_label")
            or "Speaker"
        )
        text = (item.get("text") or "").strip()
        if text:
            lines.append(f"{label}: {text}")
    return "\n".join(lines)
