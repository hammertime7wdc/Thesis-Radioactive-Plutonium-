"""
Google sign-in for the desktop app.

Desktop apps can't receive a normal web redirect, so this opens the
system browser to Supabase's Google auth URL, then spins up a short-lived
local HTTP server on 127.0.0.1 to catch the redirect Supabase sends back
after the user finishes signing in with Google. The authorization code in
that redirect is then exchanged for a real Supabase session.

Requires:
  - Google provider enabled in Supabase (Authentication > Providers > Google)
  - http://127.0.0.1:51876/* added to Supabase's Redirect URLs allow list
    (Authentication > URL Configuration)
"""

import http.server
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs

from services.supabase_client import get_supabase_client

CALLBACK_PORT = 51876
REDIRECT_URL = f"http://127.0.0.1:{CALLBACK_PORT}/callback"

_SUCCESS_HTML = (
    b"<html><body style='font-family: sans-serif; text-align:center; margin-top:80px;'>"
    b"<h2>Signed in with Google</h2>"
    b"<p>You can close this tab and return to QualCheck.</p>"
    b"</body></html>"
)
_FAILURE_HTML = (
    b"<html><body style='font-family: sans-serif; text-align:center; margin-top:80px;'>"
    b"<h2>Google sign-in failed</h2>"
    b"<p>You can close this tab and try again in QualCheck.</p>"
    b"</body></html>"
)


class _OAuthResult:
    code = None
    error = None
    error_description = None


def _make_handler(result_holder: _OAuthResult, done_event: threading.Event):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            params = parse_qs(urlparse(self.path).query)
            if "code" in params:
                result_holder.code = params["code"][0]
            if "error" in params:
                result_holder.error = params.get("error", [None])[0]
                result_holder.error_description = params.get(
                    "error_description", [None]
                )[0]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(_SUCCESS_HTML if result_holder.code else _FAILURE_HTML)

            done_event.set()

        def log_message(self, format, *args):
            pass  # silence default request logging to stdout

    return Handler


def sign_in_with_google(timeout_seconds: int = 120):
    """
    Runs the full Google sign-in flow and returns a Supabase AuthResponse
    (same shape as sign_in_with_password's return value - has .session
    and .user) on success.

    Raises Exception with a user-facing message on failure, timeout, or
    if the user closes the browser tab without completing sign-in.
    """
    result_holder = _OAuthResult()
    done_event = threading.Event()

    handler_cls = _make_handler(result_holder, done_event)
    httpd = http.server.HTTPServer(("127.0.0.1", CALLBACK_PORT), handler_cls)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    try:
        supabase = get_supabase_client()
        oauth_response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {"redirect_to": REDIRECT_URL},
            }
        )
        webbrowser.open(oauth_response.url)

        finished = done_event.wait(timeout=timeout_seconds)
        if not finished:
            raise Exception("Google sign-in timed out. Please try again.")

        if result_holder.error:
            raise Exception(
                result_holder.error_description
                or result_holder.error
                or "Google sign-in was cancelled."
            )

        if not result_holder.code:
            raise Exception("Google sign-in did not return an authorization code.")

        return supabase.auth.exchange_code_for_session(
            {"auth_code": result_holder.code}
        )
    finally:
        httpd.shutdown()
        httpd.server_close()
