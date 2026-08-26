FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY core ./core
COPY providers ./providers
COPY tools ./tools
COPY interfaces ./interfaces
COPY mychatbot ./mychatbot

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

USER appuser

ENV MYCHATBOT_DATA=/data \
    API_HOST=0.0.0.0 \
    API_PORT=8765

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('API_PORT','8765') + '/health', timeout=3)"

CMD ["uvicorn", "interfaces.api_server:app", "--host", "0.0.0.0", "--port", "8765"]
