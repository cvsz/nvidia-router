# zrouter-web — Web Deployment Package

Production-ready web deployment for the NVIDIA Free-Model Router. Provides a
Flask WSGI app wrapping `zrouter.py`'s `FreeRouter` with a browser-based chat
UI and an OpenAI-compatible proxy API.

## Contents

| File | Purpose |
|------|---------|
| `web_app.py` | Flask WSGI application |
| `gunicorn.conf.py` | Production Gunicorn configuration |
| `templates/index.html` | Browser-based luxury dashboard UI |
| `static/img/nvidia.png` | Favicon / branding |
| `Dockerfile.web` | Container image definition |
| `docker-compose.web.yml` | Docker Compose orchestration |
| `Procfile` | Heroku / PaaS process definition |
| `runtime.txt` | Heroku Python version pin |
| `.env.web.example` | Environment variable template |
| `README.web.md` | This documentation |
| `requirements.txt` | Python dependencies |
| `zrouter.py` | Core router (from project root) |
| `models.json` | Model catalog |
| `provider.json` | Provider configuration |
| `.dockerignore` | Docker build exclusions |

## Quick Start

### 1. Full Deploy (Recommended)

```bash
cd /path/to/zrouter

# Build and start in one command
export NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy"
make build:deploy
```

### 2. Local (Flask dev server)

```bash
cd dist/web

# Install dependencies
pip install -r requirements.txt

# Set your NVIDIA API key(s)
export NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy"

# Run
python web_app.py

# Open http://localhost:8000 in your browser
```

### 3. Production (Gunicorn)

```bash
cd dist/web

pip install -r requirements.txt
export NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy"
export ROUTER_TOKEN=changeme   # recommended

gunicorn -c gunicorn.conf.py web_app:app
```

### 4. Docker

```bash
cd dist/web

docker build -f Dockerfile.web -t zrouter-web:latest .

docker run -d \
  --name zrouter-web \
  -p 8000:8000 \
  -e NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy" \
  -e ROUTER_TOKEN=changeme \
  zrouter-web:latest
```

### 5. Docker Compose

```bash
cd dist/web

cp .env.web.example .env
# edit .env with your keys

docker-compose -f docker-compose.web.yml up -d
```

### 6. Heroku

```bash
cd dist/web

heroku create my-zrouter
heroku config:set NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy"
heroku config:set ROUTER_TOKEN=changeme
git push heroku main
```

## Dashboard Features

| Panel | Description |
|-------|-------------|
| **Overview** | Router health, API key status (masked), route count, key details |
| **Models** | Allowlisted models grouped by route (code, fast, general, reasoning, vision) |
| **Chat** | Streaming + non-streaming chat, route/model selection, max tokens |
| **Stats** | Per-model and per-key statistics (ok, fail, 429, avg latency) |

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/` | Browser chat UI | No |
| GET | `/health` | Health + key status | No |
| GET | `/list` | Allowlisted models grouped by route | Yes (if token set) |
| GET | `/v1/models` | OpenAI model list | Yes (if token set) |
| GET | `/stats` | Per-model/per-key stats | Yes (if token set) |
| POST | `/v1/chat/completions` | OpenAI-compatible chat | Yes (if token set) |
| POST | `/v1/embeddings` | Embeddings | Yes (if token set) |

### OpenAI Client Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="changeme",  # matches ROUTER_TOKEN
)

response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "write a regex for emails"}],
)
print(response.choices[0].message.content)
```

### Streaming (SSE)

```python
response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "hello"}],
    stream=True,
)
for chunk in response:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `NVIDIA_API_KEYS` | — | Yes | Comma-separated NVIDIA API keys |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | No | NVIDIA NIM API base URL |
| `NVIDIA_RPM` | 35 | No | Per-key requests per minute |
| `NVIDIA_CACHE_TTL` | 3600 | No | Cache TTL seconds (0 = off) |
| `NVIDIA_TIMEOUT` | 90 | No | Request timeout seconds |
| `NVIDIA_MAX_WAIT` | 60 | No | Max wait when all keys limited |
| `ROUTER_TOKEN` | — | No | Bearer token for proxy auth |
| `WEB_HOST` | `0.0.0.0` | No | Bind host |
| `WEB_PORT` | 8000 | No | Bind port |
| `WEB_DEBUG` | 0 | No | Flask debug mode |
| `WEB_WORKERS` | 4 | No | Gunicorn workers |
| `WEB_THREADS` | 8 | No | Gunicorn threads per worker |
| `WEB_LOG_LEVEL` | info | No | Log level |

## Production Checklist

- [ ] Set `NVIDIA_API_KEYS` with valid keys
- [ ] Set `ROUTER_TOKEN` for proxy authentication
- [ ] Use HTTPS/TLS in production (terminate at reverse proxy)
- [ ] Configure `NVIDIA_RPM` for your key tier
- [ ] Set up monitoring and logging
- [ ] Use Gunicorn (not Flask dev server) in production

## Reverse Proxy (Nginx)

See the project's `DEPLOYMENT.md` for an example Nginx config with TLS termination
proxying to `http://127.0.0.1:8000/`.
