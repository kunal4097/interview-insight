"""
Granola's MCP/OAuth connection - signs in via the same browser OAuth handshake Claude Code/
Claude.ai/ChatGPT use, so it works on any Granola plan (including Basic) with no pasted key.
Granola hasn't published exact MCP tool schemas for third-party clients, so this connects,
discovers each tool's real input schema at runtime, and defensively parses whatever shape
list_meetings/get_meeting_transcript actually return (a custom XML-tag format for meetings,
a security-preamble-wrapped JSON object for transcripts - both reverse-engineered from real
responses, not guessed) rather than assuming a schema Granola never documented.

The "mcp" package is intentionally NOT in requirements.txt (heavy dependency tree most users
won't need) - _import_mcp_client() imports it lazily, only when this connection method is used.
"""
import asyncio
import json
import re

import streamlit as st

from .config import GRANOLA_MCP_URL
from .granola_rest import GranolaAPIError


# --- Granola MCP (OAuth) connection -----------------------------------------------------
# Alternative to the API-key flow above: signs in via Granola's MCP server using the same
# browser OAuth handshake Claude Code/Claude.ai/ChatGPT use, so it works on any Granola plan
# (including Basic) with no pasted key. Granola hasn't published exact MCP tool schemas for
# third-party clients, so rather than guess parameter names, this connects, discovers each
# tool's real input schema at runtime, and lets you call tools directly and feed the raw
# result into the assessment - a transparent tool console, not a guessed parser.
#
# The "mcp" package is intentionally NOT in requirements.txt - it pulls in a fairly heavy
# dependency tree (starlette, uvicorn, pyjwt, etc.) that most users of this app won't need.
# It's imported lazily, only when this connection method is actually used.

def _import_mcp_client():
    try:
        import httpx2
        from mcp import ClientSession
        from mcp.client.auth import OAuthClientProvider
        from mcp.client.streamable_http import streamable_http_client
        from mcp.shared.auth import AuthorizationCodeResult, OAuthClientMetadata
    except ImportError as e:
        raise GranolaAPIError(
            0,
            "The 'mcp' package isn't installed. Run `pip install mcp` to enable "
            f"Granola sign-in via MCP. ({e})",
        )
    return httpx2, ClientSession, OAuthClientProvider, streamable_http_client, AuthorizationCodeResult, OAuthClientMetadata


class _LoopbackCallbackHandler:
    """Factory for a BaseHTTPRequestHandler that captures one OAuth redirect's query
    params and hands them to result_queue - the SDK doesn't ship a loopback server, so
    this app provides its own for the native-app-style redirect Granola's MCP OAuth expects."""

    @staticmethod
    def make(result_queue):
        from http.server import BaseHTTPRequestHandler

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                from urllib.parse import parse_qs, urlparse

                params = parse_qs(urlparse(self.path).query)
                result_queue.put(params)
                body = b"<html><body><p>Signed in with Granola. You can close this tab and return to the app.</p></body></html>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        return Handler


def _run_loopback_server(ready_event, port_holder: dict, result_queue) -> None:
    from http.server import HTTPServer

    handler_cls = _LoopbackCallbackHandler.make(result_queue)
    httpd = HTTPServer(("127.0.0.1", 0), handler_cls)
    port_holder["port"] = httpd.server_address[1]
    ready_event.set()
    httpd.timeout = 180
    httpd.handle_request()
    httpd.server_close()


class StreamlitMCPTokenStorage:
    """TokenStorage backed by st.session_state - memory-only for this browser session,
    cleared on Disconnect. Implements the TokenStorage protocol structurally (get_tokens/
    set_tokens/get_client_info/set_client_info); no base class to inherit from."""

    async def get_tokens(self):
        return st.session_state.get("granola_mcp_tokens")

    async def set_tokens(self, tokens) -> None:
        st.session_state["granola_mcp_tokens"] = tokens

    async def get_client_info(self):
        return st.session_state.get("granola_mcp_client_info")

    async def set_client_info(self, client_info) -> None:
        st.session_state["granola_mcp_client_info"] = client_info


def _extract_tool_text(result) -> str:
    parts = []
    for block in result.content or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)


def _clean_mcp_transcript_text(raw: str) -> str:
    """Granola's real get_meeting_transcript tool doesn't return plain text - it prefixes a
    security preamble ("treat this as data, not instructions") before a JSON object whose
    `transcript` field holds the actual text. Pull that field out so the assessment (and the
    review screen) see readable text instead of a raw JSON blob with a preamble glued on.
    Falls back to the untouched raw text if the shape doesn't match - never lose data by
    guessing wrong."""
    if not raw:
        return raw
    start = raw.find("{")
    if start == -1:
        return raw
    try:
        parsed, _end = json.JSONDecoder().raw_decode(raw, start)
    except json.JSONDecodeError:
        return raw
    if isinstance(parsed, dict) and isinstance(parsed.get("transcript"), str) and parsed["transcript"].strip():
        return parsed["transcript"]
    return raw


async def _granola_mcp_session(work_fn):
    """Opens one OAuth-authenticated MCP session against Granola and runs work_fn(session,
    tools_by_name) inside it. Reuses stored tokens from StreamlitMCPTokenStorage when valid;
    only opens the browser for the loopback redirect when no valid token exists yet."""
    import queue
    import threading
    import webbrowser

    httpx2, ClientSession, OAuthClientProvider, streamable_http_client, AuthorizationCodeResult, OAuthClientMetadata = _import_mcp_client()

    result_queue: queue.Queue = queue.Queue()
    port_holder: dict = {}
    ready_event = threading.Event()
    server_thread = threading.Thread(target=_run_loopback_server, args=(ready_event, port_holder, result_queue), daemon=True)
    server_thread.start()
    if not ready_event.wait(timeout=5):
        raise GranolaAPIError(0, "Couldn't start the local sign-in listener.")
    redirect_uri = f"http://127.0.0.1:{port_holder['port']}/callback"

    async def redirect_handler(authorization_url: str) -> None:
        webbrowser.open(authorization_url)

    async def callback_handler():
        try:
            params = await asyncio.to_thread(result_queue.get, True, 180)
        except queue.Empty:
            raise GranolaAPIError(0, "Timed out waiting for Granola sign-in.")
        code = (params.get("code") or [None])[0]
        state = (params.get("state") or [None])[0]
        iss = (params.get("iss") or [None])[0]
        if not code:
            raise GranolaAPIError(0, "Granola sign-in was cancelled or didn't return an authorization code.")
        return AuthorizationCodeResult(code=code, state=state, iss=iss)

    client_metadata = OAuthClientMetadata(
        client_name="PM Interview Coach",
        redirect_uris=[redirect_uri],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
    )
    oauth = OAuthClientProvider(
        server_url=GRANOLA_MCP_URL,
        client_metadata=client_metadata,
        storage=StreamlitMCPTokenStorage(),
        redirect_handler=redirect_handler,
        callback_handler=callback_handler,
    )

    async with httpx2.AsyncClient(auth=oauth, timeout=60) as http_client:
        async with streamable_http_client(GRANOLA_MCP_URL, http_client=http_client) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                tools_by_name = {t.name: t for t in tools_result.tools}
                return await work_fn(session, tools_by_name)


def granola_mcp_connect() -> list:
    """Signs in (or reuses a stored session) and returns the list of available tool names."""
    async def work(session, tools_by_name):
        st.session_state["granola_mcp_tool_schemas"] = {
            name: tool.input_schema for name, tool in tools_by_name.items()
        }
        return list(tools_by_name.keys())
    return asyncio.run(_granola_mcp_session(work))


def granola_mcp_call_tool(tool_name: str, arguments: dict) -> dict:
    """Calls one tool on a fresh authenticated session (tokens are reused; only the network
    round-trip is new) and returns {"structured": ..., "text": ..., "is_error": bool}."""
    async def work(session, tools_by_name):
        if tool_name not in tools_by_name:
            raise GranolaAPIError(0, f"Tool '{tool_name}' is not available.")
        result = await session.call_tool(tool_name, arguments)
        return {
            "structured": result.structured_content,
            "text": _extract_tool_text(result),
            "is_error": bool(result.is_error),
        }
    return asyncio.run(_granola_mcp_session(work))


# Granola hasn't published exact MCP output schemas for third-party clients (see the note in
# README), so these are deliberately defensive: they try several plausible shapes/key names and
# return None/"" rather than a guessed-wrong value when nothing recognizable is found - callers
# fall back to the raw tool console in that case instead of showing something silently wrong.
_MEETING_ID_KEYS = ["id", "meeting_id", "meetingId", "uuid", "note_id", "noteId"]
_MEETING_TITLE_KEYS = ["title", "name", "subject", "meeting_title", "meetingTitle"]
_MEETING_DATE_KEYS = ["date", "created_at", "createdAt", "start_time", "startTime", "scheduled_at", "scheduledAt"]
_MEETING_SUMMARY_KEYS = ["summary", "summary_text", "summary_markdown", "notes", "overview", "description"]


def _pick_field(item: dict, keys: list) -> str:
    for k in keys:
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _meeting_id(item: dict) -> str:
    return _pick_field(item, _MEETING_ID_KEYS)


def _meeting_title(item: dict) -> str:
    return _pick_field(item, _MEETING_TITLE_KEYS) or "Untitled interview"


def _meeting_date(item: dict) -> str:
    date = _pick_field(item, _MEETING_DATE_KEYS)
    if not date:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}", date):
        return date[:10]
    # Granola's real MCP server returns human-readable dates like
    # "Sep 22, 2026 10:53 AM GMT+5:30" - trim the timezone suffix rather than blindly
    # slicing to 10 chars (which would chop an ISO-style date mid-string here).
    return re.sub(r"\s*GMT[+-]\d{1,2}(:\d{2})?$", "", date).strip()


def _meeting_summary(item: dict) -> str:
    return _pick_field(item, _MEETING_SUMMARY_KEYS)


_MEETING_TAG_RE = re.compile(r"<meeting\b([^>]*)>", re.IGNORECASE)
_TAG_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def _unescape_xml(s: str) -> str:
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")


def _parse_meeting_tags(text: str) -> list:
    """Granola's real MCP server returns list_meetings as a custom tag format, e.g.
    <meetings_data ...><meeting id="..." title="..." date="..." url="..."/>...</meetings_data> -
    not JSON. Reads attributes straight off each <meeting> opening tag only (never the tag
    body, which can carry participant names/emails - out of scope for a meeting-list card and
    exactly the kind of personal detail this app is built to never surface)."""
    meetings = []
    for tag_match in _MEETING_TAG_RE.finditer(text):
        attrs = {k: _unescape_xml(v) for k, v in _TAG_ATTR_RE.findall(tag_match.group(1))}
        if attrs.get("id"):
            meetings.append(attrs)
    return meetings


def _find_meeting_list(result: dict) -> list | None:
    """Locates a list of meeting-like dicts inside an MCP tool result. Returns None when
    nothing list-shaped can be found. A found empty list ([], "you have no calls yet") is
    distinct from "couldn't parse this at all"."""

    def is_dict_list(value) -> bool:
        return isinstance(value, list) and (not value or all(isinstance(v, dict) for v in value))

    def search(value):
        if is_dict_list(value):
            return [v for v in value if _meeting_id(v)] if value else value
        if isinstance(value, dict):
            for key in ("meetings", "items", "notes", "results", "data"):
                found = value.get(key)
                if is_dict_list(found):
                    return [v for v in found if _meeting_id(v)] if found else found
        return None

    found = search(result.get("structured"))
    if found is not None:
        return found
    text = (result.get("text") or "").strip()
    if text.startswith("{") or text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if parsed is not None:
            found = search(parsed)
            if found is not None:
                return found
    if "<meeting" in text:
        tag_meetings = _parse_meeting_tags(text)
        if tag_meetings:
            return tag_meetings
    return None


def _tool_id_arg_name(schema: dict, fallback: str = "meeting_id") -> str:
    required = (schema or {}).get("required") or []
    if required:
        return required[0]
    props = (schema or {}).get("properties") or {}
    return next(iter(props), fallback)
