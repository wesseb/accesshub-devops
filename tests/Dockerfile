FROM python:3.13-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN python -m venv --copies /venv && /venv/bin/pip install -r requirements.txt

FROM build AS build_test
WORKDIR /app
COPY app/ ./app/
COPY tests/ ./tests/
ENTRYPOINT ["/venv/bin/pytest", "tests/", "-v"]