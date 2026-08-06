FROM python:3.13-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN python -m venv --copies /venv && /venv/bin/pip install -r requirements.txt

FROM build as build_test
WORKDIR /app
COPY app/ ./app/
COPY tests/ ./tests/
RUN /venv/bin/pip install pytest
ENTRYPOINT ["/venv/bin/pytest", "tests/", "-v"]

FROM python:3.13-slim as alternative_build
WORKDIR /app
COPY --from=build venv /venv/
COPY app/ ./app/
CMD ["python3", "-m", "app.main"]

FROM gcr.io/distroless/python3-debian13:latest AS runtime
WORKDIR /app
COPY --from=build /venv/lib/python3.13/site-packages /app/site-packages
COPY app/ ./app/
ENV PYTHONPATH=/app/site-packages
ENTRYPOINT ["python3", "-m", "app.main"]