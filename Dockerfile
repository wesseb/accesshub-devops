FROM python:3.13-slim AS build-venv
WORKDIR /app
RUN python -m venv --copies /venv

FROM python:3.13-slim AS runtime_slim
WORKDIR /app
COPY --from=build-venv venv /venv/
COPY app/ ./app/
CMD ["python3", "-m", "app.main"]

FROM gcr.io/distroless/python3-debian13:nonroot AS runtime_distroless
WORKDIR /app
COPY --from=build-venv /venv/lib/python3.13/site-packages /app/site-packages
COPY app/ ./app/
ENV PYTHONPATH=/app/site-packages
ENTRYPOINT ["python3", "-m", "app.main"]