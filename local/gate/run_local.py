"""Evalúa cada versión contra producción con perf-gate y arma el sitio con los reportes HTML.

Corre dentro del contenedor `gate` cuando k6 terminó. Nunca falla por un gate en rojo:
el objetivo local es VER el resultado (en CI, el exit code sí bloquea el pipeline).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

RESULTS = Path(os.getenv("RESULTS_DIR", "/results"))
SITE = Path(os.getenv("SITE_DIR", "/site"))
CONFIG = os.getenv("GATE_CONFIG", "/demo/local/perf-gate.local.yml")
VERSIONS = os.getenv("VERSIONS", "version-a,version-b").split(",")

sys.path.insert(0, "/demo/scripts")
from build_site import main as build_site  # noqa: E402


def main() -> int:
    baseline = RESULTS / "produccion.json"
    reports = Path("/tmp/reports")
    shutil.rmtree(reports, ignore_errors=True)
    verdicts = {}
    for version in VERSIONS:
        out = reports / f"perf-gate-report-{version}"
        print(f"\n######## {version} vs producción", flush=True)
        code = subprocess.call(["perf-gate", "--baseline", str(baseline),
                                "--candidate", str(RESULTS / f"{version}.json"),
                                "--config", CONFIG, "--name", version, "--report-dir", str(out)])
        verdicts[version] = {0: "PASA", 1: "NO PASA"}.get(code, f"ERROR ({code})")

    # Reemplazar el sitio completo de una vez (el navegador nunca ve uno a medias).
    tmp = SITE.with_name("site.tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    build_site(reports, tmp)
    SITE.mkdir(exist_ok=True)
    for item in SITE.iterdir():
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    for item in tmp.iterdir():
        shutil.move(str(item), SITE / item.name)
    shutil.rmtree(tmp, ignore_errors=True)

    print("\n================ RESULTADO ================")
    for v, verdict in verdicts.items():
        print(f"  {v}: {verdict}")
    print("  Reportes: http://localhost:8000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
