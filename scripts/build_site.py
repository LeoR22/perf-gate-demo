"""Arma el sitio de GitHub Pages con los reportes del Performance Quality Gate.

Entrada:  carpeta con subcarpetas perf-gate-report-<version>/ (artifacts del pipeline)
Salida:   site/index.html                 portada con todas las versiones
          site/<version>/report.html      reporte visual de cada versión
          site/<version>/report.json      reporte completo
          site/grafana.json               filas planas de todas las versiones (fuente para Grafana)
Uso:      python scripts/build_site.py reports site
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ICON = {"PASS": ("✓", "Pasa", "#0ca30c"), "WARN": ("!", "Pasa con advertencias", "#b87800"),
        "FAIL": ("✕", "No pasa", "#d03b3b")}


def main(src: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    versions, rows = [], []
    for report in sorted(src.glob("*/report.json")):
        data = json.loads(report.read_text(encoding="utf-8"))
        name = data["candidate"]
        dest = out / name
        dest.mkdir(exist_ok=True)
        for f in ("report.html", "report.json", "report.md"):
            if (report.parent / f).exists():
                shutil.copy(report.parent / f, dest / f)
        run = data["candidate_run"]
        versions.append({
            "version": name, "status": data["status"], "passed": data["passed"],
            "headline": data["headline"], "throughput_rps": round(run["throughput_rps"], 1),
            "error_rate_pct": round(run["error_rate_pct"], 2), "stabilization_s": run["stabilization_s"],
        })
        rows.extend(data.get("rows", []))

    if not versions:
        sys.exit(f"No se encontraron reportes en {src}")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_url": (f"{os.getenv('GITHUB_SERVER_URL')}/{os.getenv('GITHUB_REPOSITORY')}"
                    f"/actions/runs/{os.getenv('GITHUB_RUN_ID')}") if os.getenv("GITHUB_RUN_ID") else None,
    }
    (out / "grafana.json").write_text(
        json.dumps({**meta, "versions": versions, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    cards = "".join(
        f'<a class="card" href="{escape(v["version"])}/report.html">'
        f'<span class="st" style="color:{ICON[v["status"]][2]}">{ICON[v["status"]][0]} {ICON[v["status"]][1]}</span>'
        f'<h2>{escape(v["version"])}</h2><p>{escape(v["headline"])}</p>'
        f'<small>{v["throughput_rps"]} req/s · {v["error_rate_pct"]}% errores · '
        f'estable a los {v["stabilization_s"]:.0f} s</small></a>'
        for v in versions)
    run_link = f' · <a href="{escape(meta["run_url"])}">ejecución del pipeline</a>' if meta["run_url"] else ""
    (out / "index.html").write_text(f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Performance Gate</title><style>
:root{{color-scheme:light dark;--bg:#fcfcfb;--panel:#fff;--b:#e4e3df;--t:#0b0b0b;--t2:#52514e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1a1a19;--panel:#222220;--b:#383835;--t:#f0efec;--t2:#c3c2b7}}}}
body{{margin:0;background:var(--bg);color:var(--t);font:15px/1.5 system-ui,"Segoe UI",sans-serif}}
main{{max-width:960px;margin:0 auto;padding:32px 16px}}h1{{margin:0 0 4px}}.sub{{color:var(--t2)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-top:20px}}
.card{{display:block;background:var(--panel);border:1px solid var(--b);border-radius:12px;padding:18px;
color:inherit;text-decoration:none}}.card:hover{{border-color:var(--t2)}}.card h2{{margin:6px 0}}
.st{{font-weight:650}}.card p{{margin:0 0 8px}}small,a{{color:var(--t2)}}</style></head><body><main>
<h1>Performance Quality Gate</h1>
<p class="sub">Versiones nuevas frente a producción · generado {meta["generated_at"]}{run_link}</p>
<div class="grid">{cards}</div>
<p class="sub" style="margin-top:28px">Datos para Grafana: <a href="grafana.json">grafana.json</a></p>
</main></body></html>""", encoding="utf-8")
    print(f"Sitio generado en {out}: {', '.join(v['version'] for v in versions)}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "reports"), Path(sys.argv[2] if len(sys.argv) > 2 else "site"))
