FROM python:3.13-slim AS build-venv-test
WORKDIR /app
COPY requirements.txt .
RUN python -m venv --copies /venv && /venv/bin/pip install -r requirements.txt

FROM build-venv-test AS runtime_test
WORKDIR /app
COPY app/ ./app/
COPY tests/ ./tests/
ENTRYPOINT ["/venv/bin/pytest", "tests/", "-v"]