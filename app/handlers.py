"""
Route handling, built directly on http.server (no framework).

Kept framework-free on purpose - it makes the request/response cycle
fully visible, which is useful when you later put this behind a
reverse proxy / Ingress and need to reason about what's actually
happening at the HTTP layer.
"""

import json
import re
from http.server import BaseHTTPRequestHandler

from app import db
from app.config import config
from app.logger import get_logger

log = get_logger(__name__)

ROUTES = []


def route(method: str, pattern: str):
    compiled = re.compile(pattern)

    def decorator(func):
        ROUTES.append((method, compiled, func))
        return func

    return decorator


# --- Routes ------------------------------------------------------------------

@route("GET", r"^/health$")
def health(handler, match):
    return 200, {"status": "ok"}


@route("POST", r"^/users$")
def create_user(handler, match):
    body = handler.json_body()
    username = body.get("username")
    if not username:
        return 400, {"error": "username is required"}
    user = db.create_user(username)
    return 201, user.__dict__


@route("GET", r"^/users$")
def list_users(handler, match):
    return 200, [u.__dict__ for u in db.list_users()]


@route("POST", r"^/roles$")
def create_role(handler, match):
    if not handler.is_admin():
        return 403, {"error": "admin token required"}
    body = handler.json_body()
    name = body.get("name")
    if not name:
        return 400, {"error": "name is required"}
    role = db.create_role(name, body.get("description", ""))
    return 201, role.__dict__


@route("GET", r"^/roles$")
def list_roles(handler, match):
    return 200, [r.__dict__ for r in db.list_roles()]


@route("POST", r"^/access-requests$")
def create_access_request(handler, match):
    body = handler.json_body()
    user_id, role_id = body.get("user_id"), body.get("role_id")
    if not user_id or not role_id:
        return 400, {"error": "user_id and role_id are required"}
    if not db.get_user(user_id) or not db.get_role(role_id):
        return 404, {"error": "user or role not found"}
    ar = db.create_access_request(user_id, role_id)
    log.info("access request %s created (user=%s, role=%s)", ar.id, user_id, role_id)
    return 201, _serialize_request(ar)


@route("GET", r"^/access-requests$")
def list_access_requests(handler, match):
    return 200, [_serialize_request(r) for r in db.list_access_requests()]


@route("POST", r"^/access-requests/(?P<request_id>\d+)/approve$")
def approve_access_request(handler, match):
    if not handler.is_admin():
        return 403, {"error": "admin token required"}
    ar = _decide(handler, match, approve=True)
    return _respond_decision(ar)


@route("POST", r"^/access-requests/(?P<request_id>\d+)/reject$")
def reject_access_request(handler, match):
    if not handler.is_admin():
        return 403, {"error": "admin token required"}
    ar = _decide(handler, match, approve=False)
    return _respond_decision(ar)


def _decide(handler, match, approve: bool):
    request_id = int(match.group("request_id"))
    return db.decide_access_request(request_id, approve, decided_by="admin")


def _respond_decision(ar):
    if not ar:
        return 404, {"error": "access request not found"}
    log.info("access request %s -> %s", ar.id, ar.status.value)
    return 200, _serialize_request(ar)


def _serialize_request(ar):
    data = dict(ar.__dict__)
    data["status"] = ar.status.value
    return data


# --- The actual HTTP handler --------------------------------------------------

class AccessHubHandler(BaseHTTPRequestHandler):
    def json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def is_admin(self) -> bool:
        return self.headers.get("X-Admin-Token") == config.ADMIN_TOKEN

    def _dispatch(self, method: str):
        for route_method, pattern, func in ROUTES:
            if route_method != method:
                continue
            match = pattern.match(self.path)
            if match:
                try:
                    status, payload = func(self, match)
                except Exception:
                    log.exception("unhandled error in %s %s", method, self.path)
                    status, payload = 500, {"error": "internal server error"}
                self._send_json(status, payload)
                return
        self._send_json(404, {"error": "not found"})

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)
