"""API simulada para la demo local (solo librería estándar).

Imita los endpoints del kit. Variables de entorno:
  PORT              puerto (default 8080)
  PAGOS_FACTOR      multiplica la latencia de POST /pagos (2.2 = versión lenta, como A)
  ERROR_PCT         % de respuestas 500 en todos los endpoints (default 0.3)
  PAGOS_ERROR_PCT   % de respuestas 500 en POST /pagos (default = ERROR_PCT)
  COLD_START_S      segundos de arranque en frío desde la PRIMERA petición (como B)
  COLD_FACTOR       cuánto más lento responde durante el arranque en frío (default 3)
"""
from __future__ import annotations

import json
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGOS_FACTOR = float(os.getenv("PAGOS_FACTOR", "1"))
ERROR_PCT = float(os.getenv("ERROR_PCT", "0.3"))
PAGOS_ERROR_PCT = float(os.getenv("PAGOS_ERROR_PCT", str(ERROR_PCT)))
COLD_START_S = float(os.getenv("COLD_START_S", "0"))
COLD_FACTOR = float(os.getenv("COLD_FACTOR", "3"))

ROUTES = {  # (método, ruta) -> latencia base en ms
    ("GET", "/clientes"): 135,
    ("GET", "/cuentas/ahorros/saldo"): 170,
    ("POST", "/pagos"): 295 * PAGOS_FACTOR,
    ("POST", "/transferencias"): 220,
}

_first_request: float | None = None
_lock = threading.Lock()


def _cold_multiplier() -> float:
    """El arranque en frío empieza con la primera petición, no al levantar el contenedor."""
    global _first_request
    with _lock:
        if _first_request is None:
            _first_request = time.monotonic()
        elapsed = time.monotonic() - _first_request
    if elapsed >= COLD_START_S:
        return 1.0
    return 1 + (COLD_FACTOR - 1) * (1 - elapsed / COLD_START_S)  # se recupera gradualmente


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _handle(self, method: str) -> None:
        path = self.path.split("?")[0]
        if path == "/health":
            self._send(200, {"ok": True})
            return
        base = ROUTES.get((method, path))
        if base is None:
            self._send(404, {"error": "no existe"})
            return
        if method == "POST":
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
        time.sleep(random.uniform(0.85, 1.15) * base * _cold_multiplier() / 1000)
        err = PAGOS_ERROR_PCT if path == "/pagos" else ERROR_PCT
        if random.random() * 100 < err:
            self._send(500, {"error": "Internal Server Error"})
        else:
            self._send(201 if method == "POST" else 200, {"ok": True})

    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")

    def log_message(self, *args) -> None:  # silencioso
        pass


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"API simulada en :{port} pagos_x{PAGOS_FACTOR} errores={ERROR_PCT}% "
          f"pagos_errores={PAGOS_ERROR_PCT}% cold_start={COLD_START_S}s", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
