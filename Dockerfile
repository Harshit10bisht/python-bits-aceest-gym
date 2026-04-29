# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

FROM base AS test
COPY requirements.txt requirements-dev.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY app.py fitness_core.py ./
COPY tests ./tests
CMD ["python", "-m", "pytest", "-v"]

FROM base AS runtime
RUN useradd --create-home --uid 1000 --user-group appuser
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip
COPY app.py fitness_core.py ./
USER appuser
ENV ACEEST_DB=/tmp/aceest_fitness.db
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--app-factory", "app:create_app"]
