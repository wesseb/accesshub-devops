"""
Central place for runtime configuration.

Everything here is read from environment variables with sane defaults,
on purpose: this is the seam you'll hook into later when you start
injecting config via Docker ENV, Kubernetes ConfigMaps/Secrets, or
Terraform-provisioned infrastructure. Nothing in this file should ever
need to change because of *how* the app is deployed - only *where*.
"""

import os


class Config:
    # Network
    HOST: str = os.environ.get("ACCESSHUB_HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("ACCESSHUB_PORT", "8080"))

    # Storage
    DB_PATH: str = os.environ.get("ACCESSHUB_DB_PATH", "data/accesshub.db")

    # Observability
    LOG_LEVEL: str = os.environ.get("ACCESSHUB_LOG_LEVEL", "INFO")

    # "Secret" - deliberately included so you have something to practice
    # handling properly later (Kubernetes Secrets, Vault, SOPS, sealed
    # secrets, GitLab CI/CD masked variables, etc). Right now it's just
    # a plain env var with a weak default - that's the point, it gives
    # you something concrete to fix as a security exercise.
    ADMIN_TOKEN: str = os.environ.get("ACCESSHUB_ADMIN_TOKEN", "change-me")


config = Config()
