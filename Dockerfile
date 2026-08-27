FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TOOL_PROFILE=server \
    API_TOOL_PROFILE=server \
    MYCHATBOT_DATA=/data \
    API_HOST=0.0.0.0 \
    API_PORT=8765

WORKDIR /app

COPY requirements-prod.txt ./
RUN python -m pip install --no-cache-dir -r requirements-prod.txt \
    && python -m pip check

COPY core ./core
COPY providers ./providers
COPY tools ./tools
COPY interfaces ./interfaces
COPY mychatbot ./mychatbot
COPY pyproject.toml ./

RUN groupadd --system --gid 10001 appuser \
    && useradd --system --uid 10001 --gid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown -R 10001:10001 /app /data

USER 10001:10001

VOLUME ["/data"]
EXPOSE 8765

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=6 \
  CMD python -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3); raise SystemExit(0 if r.status == 200 else 1)"

CMD ["python", "-m", "uvicorn", "interfaces.api_server:app", "--host", "0.0.0.0", "--port", "8765"]
