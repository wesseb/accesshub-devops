"""
Domain model for AccessHub - a deliberately small IAM-flavored app.

The idea: users request access to roles, an admin approves or rejects
the request, and the audit trail (who has what, who approved it) is
queryable. It mirrors - at toy scale - the kind of access-request /
approval workflow you already know from IdentityIQ, which should make
the "what should this app actually do" part familiar, so you can spend
your energy on Docker/K8s/Terraform/CI-CD instead.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class User:
    id: int | None
    username: str
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class Role:
    id: int | None
    name: str
    description: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class AccessRequest:
    id: int | None
    user_id: int
    role_id: int
    status: RequestStatus = RequestStatus.PENDING
    requested_at: str = field(default_factory=utc_now_iso)
    decided_at: str | None = None
    decided_by: str | None = None
