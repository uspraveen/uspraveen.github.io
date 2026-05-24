#!/usr/bin/env python3
"""Minimal blog API for likes + comments on port 3001."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LIKES_PATH = DATA / "likes.json"
COMMENTS_PATH = DATA / "comments.json"
LEGACY_LIKES = ROOT / "likes.json"
LEGACY_COMMENTS = ROOT / "comments.json"
PORT = int(os.environ.get("PORT", "3001"))

DATA.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default):
    if not path.is_file():
        return json.loads(json.dumps(default))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return json.loads(json.dumps(default))


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _migrate_legacy():
    likes = _read_json(LIKES_PATH, {})
    comments = _read_json(COMMENTS_PATH, {})
    if not likes and LEGACY_LIKES.is_file():
        legacy = _read_json(LEGACY_LIKES, {})
        if isinstance(legacy, dict) and legacy:
            likes = legacy
            _write_json(LIKES_PATH, likes)
    if not comments and LEGACY_COMMENTS.is_file():
        legacy = _read_json(LEGACY_COMMENTS, {})
        if isinstance(legacy, dict) and legacy:
            comments = legacy
            _write_json(COMMENTS_PATH, comments)


_migrate_legacy()


def _safe_slug(raw: str) -> str | None:
    s = (raw or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", s):
        return None
    return s


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, code: int, body: bytes, content_type="application/json"):
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload):
        body = json.dumps(payload).encode("utf-8")
        self._send(code, body)

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        parsed = urlparse(self.path)
        m = re.fullmatch(r"/api/(likes|comments)/([^/]+)", parsed.path or "")
        if not m:
            return self._json(404, {"error": "Not found"})
        kind, slug_raw = m.group(1), m.group(2)
        slug = _safe_slug(slug_raw)
        if not slug:
            return self._json(400, {"error": "Invalid slug"})
        if kind == "likes":
            likes = _read_json(LIKES_PATH, {})
            count = int(likes.get(slug, 0) or 0)
            return self._json(200, {"slug": slug, "count": count})
        comments = _read_json(COMMENTS_PATH, {})
        arr = comments.get(slug)
        if not isinstance(arr, list):
            arr = []
        return self._json(200, arr)

    def _read_body_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0 or length > 65536:
            return None, "Empty body"
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8")), None
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, "Invalid JSON"

    def do_POST(self):
        parsed = urlparse(self.path)
        m = re.fullmatch(r"/api/(likes|comments)/([^/]+)", parsed.path or "")
        if not m:
            return self._json(404, {"error": "Not found"})
        kind, slug_raw = m.group(1), m.group(2)
        slug = _safe_slug(slug_raw)
        if not slug:
            return self._json(400, {"error": "Invalid slug"})
        if kind == "likes":
            likes = _read_json(LIKES_PATH, {})
            cur = int(likes.get(slug, 0) or 0)
            nxt = cur + 1
            likes[slug] = nxt
            _write_json(LIKES_PATH, likes)
            return self._json(200, {"slug": slug, "count": nxt})
        data, err = self._read_body_json()
        if err:
            return self._json(400, {"error": err})
        if not isinstance(data, dict):
            return self._json(400, {"error": "JSON object required"})
        name = str(data.get("name", "")).strip()
        message = str(data.get("message", "")).strip()
        if not name or not message:
            return self._json(400, {"error": "Name and message required"})
        if len(name) > 120 or len(message) > 4000:
            return self._json(400, {"error": "Name or message too long"})
        entry = {
            "name": name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        comments = _read_json(COMMENTS_PATH, {})
        if not isinstance(comments, dict):
            comments = {}
        if not isinstance(comments.get(slug), list):
            comments[slug] = []
        comments[slug].append(entry)
        _write_json(COMMENTS_PATH, comments)
        return self._json(201, entry)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))


def main():
    httpd = HTTPServer(("0.0.0.0", PORT), Handler)
    print("portfolio-api (python) listening on", PORT, flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
