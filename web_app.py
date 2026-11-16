#!/usr/bin/env python3
"""
zrouter-web — Web deployment entry point for NVIDIA Free-Model Router.

Wraps zrouter.py's FreeRouter + OpenAI-compatible proxy in a Flask WSGI app
with a built-in browser chat UI.  Runs standalone with Flask's dev server or
production-ready under gunicorn / uWSGI.

Endpoints:
    GET  /                      browser chat UI
    GET  /health                health + key status
    GET  /v1/models             OpenAI model list (allowlisted + auto routes)
    GET  /stats                 per-model / per-key statistics
    POST /v1/chat/completions   OpenAI-compatible chat (stream + non-stream)
    POST /v1/embeddings         embeddings
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

from flask import (
    Flask,
    jsonify,
    make_response,
    render_template,
    request,
    send_from_directory,
    stream_with_context,
    Response,
)

# --------------------------------------------------------------------------- #
# Add package root to path so we can import zrouter.py
# --------------------------------------------------------------------------- #
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Import the core router (functions/classes defined in zrouter.py)
import zrouter  # noqa: E402  (zrouter.py lives in same dir)
from zrouter import FreeRouter, CFG, RouterError, make_handler, serve  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("zrouter-web")

# --------------------------------------------------------------------------- #
# Flask app
# --------------------------------------------------------------------------- #
app = Flask(
    __name__,
    template_folder=os.path.join(_HERE, "templates"),
    static_folder=os.path.join(_HERE, "static"),
)

# --------------------------------------------------------------------------- #
# Router instance (lazy – keys come from env at first request)
# --------------------------------------------------------------------------- #
_router: FreeRouter | None = None


def _get_router() -> FreeRouter:
    global _router
    if _router is None:
        keys_file = os.environ.get("NVIDIA_KEYS_FILE")
        providers_file = os.environ.get("NVIDIA_PROVIDERS_FILE")
        _router = FreeRouter(keys_file=keys_file, providers_file=providers_file)
    return _router


# --------------------------------------------------------------------------- #
# Routes – web UI
# --------------------------------------------------------------------------- #
@app.get("/")
def index() -> str:
    """Browser chat UI."""
    return render_template("index.html")


@app.get("/health")
def health() -> Any:
    """Health endpoint – returns key status as JSON."""
    try:
        r = _get_router()
        return jsonify(
            {
                "ok": True,
                "keys": [
                    {"key": k, "provider": p, "status": s, "ok": o, "429": n429}
                    for k, p, s, o, n429 in r.key_status()
                ],
            }
        )
    except RouterError as e:
        return jsonify({"error": {"message": e.message, "code": e.status}}), e.status


@app.get("/list")
def list_models() -> Any:
    """List allowlisted models grouped by route (from models.json catalog)."""
    try:
        from zrouter import CATALOG
        grouped: dict[str, list[str]] = {route: [] for route in CFG.routes}
        for m in CATALOG.models:
            if not isinstance(m, dict):
                continue
            mid = str(m.get("id", ""))
            model_routes = m.get("routes", []) or []
            for route in model_routes:
                if route in grouped:
                    grouped[route].append(mid)
        # Also include models with no routes under "general"
        for m in CATALOG.models:
            if not isinstance(m, dict):
                continue
            mid = str(m.get("id", ""))
            model_routes = m.get("routes", []) or []
            if not model_routes and "general" in grouped:
                grouped["general"].append(mid)
        return jsonify(grouped)
    except RouterError as e:
        return jsonify({"error": {"message": e.message, "code": e.status}}), e.status


@app.get("/v1/models")
def models() -> Any:
    """OpenAI-compatible model list (allowlisted models + route aliases)."""
    try:
        r = _get_router()
        ids = ["auto"] + [f"free-{rt}" for rt in CFG.routes] + r.all_allowed()
        return jsonify(
            {
                "object": "list",
                "data": [
                    {
                        "id": i,
                        "object": "model",
                        "owned_by": "nvidia-free-router",
                    }
                    for i in ids
                ],
            }
        )
    except RouterError as e:
        return jsonify({"error": {"message": e.message, "code": e.status}}), e.status


@app.get("/stats")
def stats() -> Any:
    """Per-model / per-key statistics snapshot."""
    try:
        r = _get_router()
        return jsonify(r.stats.snapshot() if r.stats else {})
    except RouterError as e:
        return jsonify({"error": {"message": e.message, "code": e.status}}), e.status


@app.post("/v1/chat/completions")
def chat_completions() -> Any:
    """OpenAI-compatible chat/completions endpoint."""
    try:
        r = _get_router()
        body = request.get_json(force=True, silent=True) or {}

        if body.get("stream"):
            resp, model, _key = r.open_chat_stream(body)

            def gen():
                for line in resp.iter_lines():
                    if line:
                        yield line + b"\n\n"

            return Response(
                stream_with_context(gen()),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Router-Model": model,
                },
            )

        out = r.chat_json(body)
        return jsonify(out["json"]), 200, {
            "X-Router-Model": out["model"],
            "X-Router-Key": out["key"],
            "X-Router-Cache": str(out["cached"]).lower(),
        }

    except RouterError as e:
        return jsonify({"error": {"message": e.message, "code": e.status}}), e.status
    except Exception as exc:  # pragma: no cover – safety net
        log.exception("unhandled error in /v1/chat/completions")
        return jsonify({"error": {"message": str(exc), "code": 500}}), 500


@app.post("/v1/embeddings")
def embeddings() -> Any:
    """OpenAI-compatible embeddings endpoint."""
    try:
        r = _get_router()
        body = request.get_json(force=True, silent=True) or {}
        return jsonify(r.embeddings(body)), 200
    except RouterError as e:
        return jsonify({"error": {"message": e.message, "code": e.status}}), e.status
    except Exception as exc:  # pragma: no cover
        log.exception("unhandled error in /v1/embeddings")
        return jsonify({"error": {"message": str(exc), "code": 500}}), 500


# --------------------------------------------------------------------------- #
# Static fallback (serves /static/*, favicon, etc.)
# --------------------------------------------------------------------------- #
@app.get("/favicon.ico")
def favicon() -> Any:
    return send_from_directory(
        app.static_folder, "img/nvidia.png", mimetype="image/png"
    )


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
def main() -> None:
    host = os.environ.get("WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("WEB_PORT", "8000"))
    debug = os.environ.get("WEB_DEBUG", "0") == "1"
    log.info("Starting zrouter-web on http://%s:%d/v1", host, port)
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
