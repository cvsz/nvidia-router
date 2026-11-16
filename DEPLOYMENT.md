# Deployment Guide — NVIDIA Free-Model Router

## Local Development

### Prerequisites
- Python 3.10+
- pip

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/zrouter.git
cd zrouter

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Set your NVIDIA API key(s)
export NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy"

# Run the router
python zrouter.py chat "hello"
```

### Run as Proxy Server

```bash
# Start the OpenAI-compatible proxy
python zrouter.py serve --port 8000 --token secret

# Test with curl
curl http://localhost:8000/health

# Use with OpenAI client
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=secret
```

## Web Dashboard Deployment

The web dashboard is a Flask app with Gunicorn, providing a browser-based UI and OpenAI-compatible API.

### Quick Deploy (Recommended)

```bash
# Build and start in one command
export NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy"
make build:deploy
```

### Manual Steps

```bash
# Build the web package
make build:web

# Start the server
make build:web:start

# Or with debug mode
WEB_DEBUG=1 make build:web:start
```

The dashboard is available at `http://localhost:8000`.

### Web Make Targets

| Target | Description |
|--------|-------------|
| `make build:web` | Build web deployment package |
| `make build:web:all` | Build all web variants (dev + prod + ent) |
| `make build:web:dev` | Build web dev package (hot-reload, debug) |
| `make build:web:prod` | Build web production package (gunicorn) |
| `make build:web:ent` | Build web enterprise package (all features) |
| `make build:web:start` | Start web server from dist/web/ |
| `make build:deploy` | Build web package + start server |

## Docker Deployment

### Build Image

```bash
docker build -t zrouter:latest .
```

### Run Container

```bash
docker run -d \
  --name zrouter \
  -p 8000:8000 \
  -e NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy" \
  -e NVIDIA_RPM=35 \
  -e NVIDIA_CACHE_TTL=3600 \
  zrouter:latest
```

### Using Make

```bash
make docker:build
make docker:run
```

### Web Docker Deployment

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

### Docker Compose

```bash
cd dist/web
cp .env.web.example .env
# edit .env with your keys
docker-compose -f docker-compose.web.yml up -d
```

## systemd Service (Linux)

Create `/etc/systemd/system/zrouter.service`:

```ini
[Unit]
Description=NVIDIA Free-Model Router
After=network.target

[Service]
Type=simple
User=zrouter
WorkingDirectory=/opt/zrouter/dist/web
Environment=NVIDIA_API_KEYS=nvapi-xxx,nvapi-yyy
Environment=NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
Environment=NVIDIA_RPM=35
ExecStart=/opt/zrouter/.venv/bin/python -m gunicorn -c gunicorn.conf.py web_app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable zrouter
sudo systemctl start zrouter
```

## Docker Compose (Create `docker-compose.yml`)

```yaml
version: "3.8"

services:
  zrouter:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NVIDIA_API_KEYS=${NVIDIA_API_KEYS}
      - NVIDIA_RPM=35
      - NVIDIA_CACHE_TTL=3600
    restart: unless-stopped
```

```bash
docker-compose up -d
```

## Reverse Proxy (Nginx)

Example Nginx config for TLS termination:

```nginx
server {
    listen 443 ssl;
    server_name router.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /v1/ {
        proxy_pass http://127.0.0.1:8000/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

## Production Checklist

- [ ] Set `NVIDIA_API_KEYS` with valid keys
- [ ] Set `ROUTER_TOKEN` for proxy authentication
- [ ] Configure `NVIDIA_RPM` appropriately for your key tier
- [ ] Use HTTPS/TLS in production (terminate at reverse proxy)
- [ ] Set up monitoring and logging
- [ ] Configure `NVIDIA_CACHE_TTL` for caching behavior
- [ ] Enable `stats` persistence for usage tracking
- [ ] Use Gunicorn (not Flask dev server) in production

## Environment Variable Reference

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `NVIDIA_API_KEYS` | — | Yes | Comma-separated NVIDIA API keys |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | No | NVIDIA NIM API base URL |
| `NVIDIA_RPM` | 35 | No | Per-key requests per minute |
| `NVIDIA_CACHE_TTL` | 3600 | No | Cache TTL seconds (0 = off) |
| `NVIDIA_TIMEOUT` | 90 | No | Request timeout seconds |
| `NVIDIA_MAX_WAIT` | 60 | No | Max wait when all keys limited |
| `NVIDIA_ROUTER_CONFIG` | — | No | Path to router.json config |
| `NVIDIA_ROUTER_HOME` | `~/.nvidia_free_router` | No | Stats directory |
| `ROUTER_TOKEN` | — | No | Bearer token for proxy auth |
| `WEB_HOST` | `0.0.0.0` | No | Web bind host |
| `WEB_PORT` | 8000 | No | Web bind port |
| `WEB_DEBUG` | 0 | No | Flask debug mode |
| `WEB_WORKERS` | 4 | No | Gunicorn workers |
| `WEB_THREADS` | 8 | No | Gunicorn threads per worker |
| `WEB_LOG_LEVEL` | info | No | Log level |
