"""Genera el dashboard de Grafana del Performance Quality Gate en dos variantes:

* grafana/dashboard.json                         importable (Grafana Cloud): pide elegir la fuente Infinity
                                                  y lee grafana.json publicado en GitHub Pages.
* local/grafana/dashboards/perf-gate.json        provisionado en el Grafana del docker compose:
                                                  fuente fija y lee grafana.json del contenedor `reports`.

Uso: python grafana/build_dashboards.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_URL = "https://leor22.github.io/perf-gate-demo/grafana.json"
LOCAL_URL = "http://reports:8000/grafana.json"

STATUS_MAP = [{"type": "value", "options": {
    "PASS": {"text": "✓ PASA", "color": "green", "index": 0},
    "WARN": {"text": "! PASA CON ADVERTENCIAS", "color": "orange", "index": 1},
    "FAIL": {"text": "✕ NO PASA", "color": "red", "index": 2},
    "SKIP": {"text": "– OMITIDO", "color": "text", "index": 3}}}]
STATUS_CELL = [{"id": "mappings", "value": STATUS_MAP},
               {"id": "custom.cellOptions", "value": {"type": "color-background", "mode": "basic"}},
               {"id": "custom.width", "value": 230}]
SEL, ROWS = "versions", "rows"
# Infinity v4 (parser "backend") filtra por el NOMBRE VISIBLE de la columna; se agrega una columna
# "version" solo para filtrar y se oculta en cada panel. (El parser "jsonata" no devuelve filas en v4.)
FILTER = "version == '${version}'"
HIDE_VERSION = [{"id": "organize", "options": {"excludeByName": {"version": True}}}]
DETAIL_ORDER = ["Estado", "Endpoint", "Percentil", "Producción ms", "Nueva ms", "Cambio %",
                "Errores prod %", "Errores nueva %", "Muestras", "Motivo"]
# El parser backend devuelve las columnas en orden alfabético: se fija el orden explícitamente.
DETAIL_TRANSFORM = [{"id": "organize", "options": {
    "excludeByName": {"version": True},
    "indexByName": {name: i for i, name in enumerate(DETAIL_ORDER)}}}]
ALL_ORDER = ["Estado", "Versión", "Resumen", "req/s", "Errores %", "Estable (s)"]
ALL_TRANSFORM = [{"id": "organize", "options": {"indexByName": {n: i for i, n in enumerate(ALL_ORDER)}}}]


def col(sel: str, text: str, typ: str = "number") -> dict:
    return {"selector": sel, "text": text, "type": typ}


def build(ds_uid: str, url: str, importable: bool) -> dict:
    ds = {"type": "yesoreyeram-infinity-datasource", "uid": ds_uid}

    def q(root: str, columns: list[dict], filtered: bool = True) -> dict:
        query = {"refId": "A", "datasource": ds, "type": "json", "source": "url", "format": "table",
                 "parser": "backend", "url": "${source}", "url_options": {"method": "GET", "data": ""},
                 "root_selector": root, "columns": columns}
        if filtered:
            query["columns"] = [col("version", "version", "string"), *columns]
            query["filterExpression"] = FILTER
        return query

    def stat(pid, title, field, text, unit, x, w, mappings=None, decimals=None):
        defaults = {"unit": unit, "mappings": mappings or [],
                    "color": {"mode": "thresholds"} if mappings else {"mode": "fixed", "fixedColor": "text"}}
        if decimals is not None:
            defaults["decimals"] = decimals
        return {"id": pid, "type": "stat", "title": title, "datasource": ds,
                "gridPos": {"h": 4, "w": w, "x": x, "y": 0},
                "targets": [q(SEL, [col(field, text, "string" if mappings else "number")])],
                "transformations": HIDE_VERSION,
                "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": f"/^{text}$/", "values": False},
                            "colorMode": "background" if mappings else "none", "graphMode": "none",
                            "textMode": "value", "justifyMode": "center"},
                "fieldConfig": {"defaults": defaults, "overrides": []}}

    panels = [
        stat(1, "Veredicto", "status", "Estado", "none", 0, 9, STATUS_MAP),
        stat(2, "Throughput", "throughput_rps", "Throughput", "reqps", 9, 5, decimals=1),
        stat(3, "Tasa de error", "error_rate_pct", "Errores", "percent", 14, 5, decimals=2),
        stat(4, "Tiempo hasta estabilizarse", "stabilization_s", "Estable", "s", 19, 5, decimals=0),
        {"id": 5, "type": "barchart", "title": "p95 por endpoint: producción vs versión nueva (ms)", "datasource": ds, "transformations": HIDE_VERSION,
         "gridPos": {"h": 10, "w": 14, "x": 0, "y": 4},
         "targets": [q(ROWS, [col("endpoint", "Endpoint", "string"), col("baseline_ms", "Producción"),
                              col("candidate_ms", "Versión nueva")])],
         "options": {"orientation": "horizontal", "xField": "Endpoint", "barWidth": 0.8, "groupWidth": 0.75,
                     "showValue": "always", "legend": {"showLegend": True, "displayMode": "list", "placement": "bottom"},
                     "tooltip": {"mode": "multi"}},
         "fieldConfig": {"defaults": {"unit": "ms", "min": 0, "color": {"mode": "palette-classic"}},
                         "overrides": [
                             {"matcher": {"id": "byName", "options": "Producción"},
                              "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "#2a78d6"}}]},
                             {"matcher": {"id": "byName", "options": "Versión nueva"},
                              "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "#eb6834"}}]}]}},
        {"id": 6, "type": "barchart", "title": "Cambio frente a producción (%)", "datasource": ds, "transformations": HIDE_VERSION,
         "gridPos": {"h": 10, "w": 10, "x": 14, "y": 4},
         "targets": [q(ROWS, [col("endpoint", "Endpoint", "string"), col("change_pct", "Cambio %")])],
         "options": {"orientation": "horizontal", "xField": "Endpoint", "showValue": "always",
                     "legend": {"showLegend": False}, "tooltip": {"mode": "single"}},
         "fieldConfig": {"defaults": {"unit": "percent", "color": {"mode": "thresholds"},
                                      "thresholds": {"mode": "absolute", "steps": [
                                          {"color": "green", "value": None}, {"color": "orange", "value": 10},
                                          {"color": "red", "value": 20}]}}, "overrides": []}},
        {"id": 7, "type": "table", "title": "Detalle por endpoint: qué falló y por qué", "datasource": ds, "transformations": DETAIL_TRANSFORM,
         "gridPos": {"h": 9, "w": 24, "x": 0, "y": 14},
         "targets": [q(ROWS, [col("status", "Estado", "string"), col("endpoint", "Endpoint", "string"),
                              col("percentile", "Percentil"), col("baseline_ms", "Producción ms"),
                              col("candidate_ms", "Nueva ms"), col("change_pct", "Cambio %"),
                              col("baseline_error_pct", "Errores prod %"),
                              col("candidate_error_pct", "Errores nueva %"),
                              col("candidate_samples", "Muestras"), col("reason", "Motivo", "string")])],
         "options": {"showHeader": True, "cellHeight": "sm"},
         "fieldConfig": {"defaults": {"custom": {"align": "auto", "cellOptions": {"type": "auto"}}},
                         "overrides": [
                             {"matcher": {"id": "byName", "options": "Estado"}, "properties": STATUS_CELL},
                             {"matcher": {"id": "byName", "options": "Motivo"}, "properties": [
                                 {"id": "custom.cellOptions", "value": {"type": "auto", "wrapText": True}},
                                 {"id": "custom.minWidth", "value": 380}]}]}},
        {"id": 8, "type": "table", "title": "Todas las versiones evaluadas", "datasource": ds, "transformations": ALL_TRANSFORM,
         "gridPos": {"h": 6, "w": 24, "x": 0, "y": 23},
         "targets": [q("versions", filtered=False, columns=[col("status", "Estado", "string"), col("version", "Versión", "string"),
                                    col("headline", "Resumen", "string"), col("throughput_rps", "req/s"),
                                    col("error_rate_pct", "Errores %"), col("stabilization_s", "Estable (s)")])],
         "fieldConfig": {"defaults": {"custom": {"cellOptions": {"type": "auto", "wrapText": True}}},
                         "overrides": [{"matcher": {"id": "byName", "options": "Estado"},
                                        "properties": STATUS_CELL}]}},
    ]

    dash = {
        "title": "Performance Quality Gate", "uid": "perf-quality-gate",
        "tags": ["performance", "quality-gate", "jmeter", "k6"],
        "description": "Versión nueva vs producción, endpoint por endpoint. Fuente: grafana.json del pipeline.",
        "editable": True, "schemaVersion": 39, "time": {"from": "now-7d", "to": "now"}, "refresh": "30s",
        "links": [{"title": "Repositorio", "type": "link", "url": "https://github.com/LeoR22/perf-quality-gate",
                   "targetBlank": True}],
        "templating": {"list": [
            {"name": "source", "label": "Fuente (grafana.json)", "type": "textbox", "query": url,
             "current": {"text": url, "value": url}},
            {"name": "version", "label": "Versión", "type": "custom", "query": "version-a,version-b",
             "current": {"text": "version-a", "value": "version-a"},
             "options": [{"text": "version-a", "value": "version-a", "selected": True},
                         {"text": "version-b", "value": "version-b", "selected": False}]}]},
        "panels": panels,
    }
    if importable:
        dash = {
            "__inputs": [{"name": "DS_INFINITY", "label": "Infinity", "type": "datasource",
                          "pluginId": "yesoreyeram-infinity-datasource", "pluginName": "Infinity"}],
            "__requires": [{"type": "datasource", "id": "yesoreyeram-infinity-datasource",
                            "name": "Infinity", "version": "2.0.0"}],
            **dash,
        }
    return dash


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ok {path.relative_to(ROOT)}")


if __name__ == "__main__":
    write(ROOT / "grafana" / "dashboard.json", build("${DS_INFINITY}", PAGES_URL, importable=True))
    write(ROOT / "local" / "grafana" / "dashboards" / "perf-gate.json", build("infinity", LOCAL_URL, importable=False))
