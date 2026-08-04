"""
Tiny persistence layer on top of sqlite3 (stdlib only - no ORM).

Kept deliberately simple and file-based: it's an easy thing to
containerize (bind mount / volume), an easy thing to break on purpose
in Kubernetes (ephemeral storage vs PersistentVolumeClaim is a great
lesson to learn the hard way), and an easy thing to eventually swap
for a real Postgres instance provisioned by Terraform.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import config
from app.models import AccessRequest, RequestStatus, Role, User

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS access_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    role_id INTEGER NOT NULL REFERENCES roles(id),
    status TEXT NOT NULL DEFAULT 'pending',
    requested_at TEXT NOT NULL,
    decided_at TEXT,
    decided_by TEXT
);
"""


def init_db() -> None:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# --- Users -----------------------------------------------------------------

def create_user(username: str) -> User:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, created_at) VALUES (?, ?)",
            (username, User(id=None, username=username).created_at),
        )
        new_id = cur.lastrowid
    return get_user(new_id)


def get_user(user_id: int) -> User | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return User(**dict(row)) if row else None


def list_users() -> list[User]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users").fetchall()
        return [User(**dict(r)) for r in rows]


# --- Roles -------------------------------------------------------------------

def create_role(name: str, description: str = "") -> Role:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO roles (name, description, created_at) VALUES (?, ?, ?)",
            (name, description, Role(id=None, name=name).created_at),
        )
        new_id = cur.lastrowid
    return get_role(new_id)


def get_role(role_id: int) -> Role | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
        return Role(**dict(row)) if row else None


def list_roles() -> list[Role]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM roles").fetchall()
        return [Role(**dict(r)) for r in rows]


# --- Access requests -----------------------------------------------------------

def create_access_request(user_id: int, role_id: int) -> AccessRequest:
    with get_conn() as conn:
        ar = AccessRequest(id=None, user_id=user_id, role_id=role_id)
        cur = conn.execute(
            "INSERT INTO access_requests (user_id, role_id, status, requested_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, role_id, ar.status.value, ar.requested_at),
        )
        new_id = cur.lastrowid
    return get_access_request(new_id)


def get_access_request(request_id: int) -> AccessRequest | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM access_requests WHERE id = ?", (request_id,)
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["status"] = RequestStatus(data["status"])
        return AccessRequest(**data)


def list_access_requests() -> list[AccessRequest]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM access_requests").fetchall()
        result = []
        for r in rows:
            data = dict(r)
            data["status"] = RequestStatus(data["status"])
            result.append(AccessRequest(**data))
        return result


def decide_access_request(request_id: int, approve: bool, decided_by: str) -> AccessRequest | None:
    status = RequestStatus.APPROVED if approve else RequestStatus.REJECTED
    with get_conn() as conn:
        conn.execute(
            "UPDATE access_requests SET status = ?, decided_at = ?, decided_by = ? "
            "WHERE id = ?",
            (status.value, User(id=None, username="").created_at, decided_by, request_id),
        )
    return get_access_request(request_id)
