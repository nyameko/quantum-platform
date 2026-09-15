FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY apps/user-api/pyproject.toml /app/pyproject.toml
COPY apps/user-api/config /app/config
COPY apps/user-api/portal /app/portal
COPY apps/user-api/templates /app/templates
COPY apps/user-api/manage.py /app/manage.py

RUN pip install --upgrade pip \
    && pip install .

RUN DJANGO_DEBUG=false \
    DJANGO_SECRET_KEY=build-only-not-production \
    python manage.py collectstatic --noinput

RUN useradd --create-home --uid 10001 quantum
USER 10001

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
