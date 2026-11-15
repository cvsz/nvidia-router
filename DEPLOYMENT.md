# Deployment Guide — NVIDIA Free-Model Router

## Local Development

### Prerequisites
- Python 3.10+
- pip

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/nvidia-router.git
cd nvidia-router

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Set your NVIDIA API key(s)
export NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy"

# Run the router
python nvidia.py chat "hello"
```

### Run as Proxy Server

```bash
# Start the OpenAI-compatible proxy
python nvidia.py serve --port 8000 --token secret

# Test with curl
curl http://localhost:8000/health

# Use with OpenAI client
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=secret
```

## Docker Deployment

### Build Image

```bash
docker build -t nvidia-router:latest .
```

### Run Container

```bash
docker run -d \
  --name nvidia-router \
  -p 8000:8000 \
  -e NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy" \
  -e NVIDIA_RPM=35 \
  -e NVIDIA_CACHE_TTL=3600 \
  nvidia-router:latest
```

### Using Make

```bash
make docker:build
make docker:run
```

## systemd Service (Linux)

Create `/etc/systemd/system/nvidia-router.service`:

```ini
[Unit]
Description=NVIDIA Free-Model Router
After=network.target

[Service]
Type=simple
User=nvidia-router
WorkingDirectory=/opt/nvidia-router
Environment=NVIDIA_API_KEYS=nvapi-xxx,nvapi-yyy
Environment=NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
Environment=NVIDIA_RPM=35
ExecStart=/opt/nvidia-router/.venv/bin/python nvidia.py serve --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable nvidia-router
sudo systemctl start nvidia-router
```

## Docker Compose

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  nvidia-router:
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
- [ ] Use HTTPS/TLS in production
- [ ] Set up monitoring and logging
- [ ] Configure `NVIDIA_CACHE_TTL` for caching behavior
- [ ] Enable `stats` persistence for usage tracking

## Environment Variable Reference

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `NVIDIA_API_KEYS` | — | Yes | Comma-separated NVIDIA API keys |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | No | NVIDIA NIM API base URL |
| `NVIDIA_RPM` | 35 | No | Per-key requests per minute |
| `NVIDIA_CACHE_TTL` | 3600 | No | Cache TTL in seconds |
| `NVIDIA_TIMEOUT` | 90 | No | Request timeout in seconds |
| `NVIDIA_MAX_WAIT` | 60 | No | Max wait when all keys limited |
| `NVIDIA_ROUTER_CONFIG` | — | No | Path to router.json config |
| `NVIDIA_ROUTER_HOME` | `~/.nvidia_free_router` | No | Stats directory |
| `ROUTER_TOKEN` | — | No | Bearer token for proxy auth |
