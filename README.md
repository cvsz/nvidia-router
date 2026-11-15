# NVIDIA Free-Model Router

Enterprise-grade OpenAI-compatible proxy/router for NVIDIA's hosted NIM endpoints
(https://integrate.api.nvidia.com/v1).

## Features

- **Free-only allowlist** — Only free models are ever called; paid models are refused
- **Multi-key rotation** — On HTTP 429, the key is benched and the same model is retried on the next key
- **Per-key rate limiting** — Token-bucket style rate limiter per API key
- **Exponential backoff** — Per (key, model) pair backoff on failures
- **Auto routing** — Classifies prompts into general/code/reasoning/fast/vision routes
- **Streaming (SSE)** — With failover before the first byte
- **Response caching** — For temperature == 0, no tools, non-stream requests
- **Persistent stats** — Per model / per key: ok, fail, 429, latency
- **OpenAI-compatible proxy** — Point any OpenAI client at it
- **CLI** — `chat`, `list`, `probe`, `stats`, `keys`, `serve`, `models`, `discover`, `providers`
- **GUI** — Tkinter-based desktop GUI (`zcloud-gui.py`)
- **TUI** — Textual-based terminal UI (`zcloud-tui.py`)

## Installation

### From PyPI

```bash
pip install nvidia-router
```

### From Source

```bash
git clone https://github.com/your-org/nvidia-router.git
cd nvidia-router
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Docker

```bash
docker build -t nvidia-router .
docker run -p 8000:8000 -e NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy" nvidia-router
```

## Usage

### CLI

```bash
# Set your API key(s)
export NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy"

# List available models
python nvidia.py list

# Chat with auto-routing
python nvidia.py chat "write a regex for emails"

# Chat with specific route
python nvidia.py chat "explain TCP slow start" --route reasoning --stream

# Run the OpenAI-compatible proxy
python nvidia.py serve --port 8000 --token secret
```

### GUI

```bash
python zcloud-gui.py
```

### TUI

```bash
python zcloud-tui.py
```

### Docker

```bash
docker run -d \
  --name nvidia-router \
  -p 8000:8000 \
  -e NVIDIA_API_KEYS="nvapi-xxx,nvapi-yyy" \
  nvidia-router:latest
```

Then point your OpenAI client at `http://localhost:8000/v1`.

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `NVIDIA_API_KEYS` | (required) | Comma-separated API keys |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | NVIDIA NIM API base URL |
| `NVIDIA_RPM` | 35 | Per-key requests per minute |
| `NVIDIA_CACHE_TTL` | 3600 | Cache TTL in seconds |
| `NVIDIA_TIMEOUT` | 90 | Request timeout in seconds |
| `NVIDIA_MAX_WAIT` | 60 | Max wait when all keys limited |
| `NVIDIA_ROUTER_CONFIG` | — | Path to router.json config |
| `NVIDIA_ROUTER_HOME` | `~/.nvidia_free_router` | Stats directory |
| `ROUTER_TOKEN` | — | Bearer token for proxy auth |

## Routes

| Route | Description |
|-------|-------------|
| `auto` | Auto-classify the prompt |
| `general` | Everyday questions |
| `code` | Code / debugging / regex / SQL / git |
| `reasoning` | Maths, logic, step-by-step, long prompts |
| `fast` | Short prompts, smallest models |
| `vision` | Messages containing images |

## License

MIT License
