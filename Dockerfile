FROM python:3.13-slim AS venv-build
WORKDIR /app
COPY requirements.txt .
RUN python -m venv --copies /venv

FROM python:3.13-slim AS alternative_build
WORKDIR /app
COPY --from=venv-build venv /venv/
COPY app/ ./app/
CMD ["python3", "-m", "app.main"]

FROM gcr.io/distroless/python3-debian13:latest AS runtime
WORKDIR /app
COPY --from=venv-build /venv/lib/python3.13/site-packages /app/site-packages
COPY app/ ./app/
ENV PYTHONPATH=/app/site-packages
ENTRYPOINT ["python3", "-m", "app.main"]