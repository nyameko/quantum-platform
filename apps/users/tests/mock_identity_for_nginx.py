"""Local fake identity service for Nginx auth_request CI. Never deployed."""
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/api/v1/me/":
            self.send_response(404)
        elif "sessionid=valid" in self.headers.get("Cookie", ""):
            self.send_response(200)
        else:
            self.send_response(403)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format, *args):
        # No cookies, credentials or personal data in CI logs.
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
