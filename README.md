# perf-gate-demo

Repositorio de ejemplo de un **equipo** que usa el
[Performance Quality Gate](https://github.com/LeoR22/perf-quality-gate) en su pipeline antes de desplegar.

La herramienta vive en su propio repositorio y se consume por versión, como cualquier GitHub Action:

```yaml
- uses: LeoR22/perf-quality-gate@v1
  with:
    baseline: resultados/produccion-actual.csv
    candidate: resultados/version-a.csv
    config: perf-gate.yml
```

## Qué hay aquí

| Archivo | Para qué |
|---|---|
| [`resultados/`](resultados) | Resultados JMeter del kit: producción, versión A y versión B (5 min, 50 usuarios) |
| [`perf-gate.yml`](perf-gate.yml) | Límites de **este** equipo (p. ej. pagos más estricto: +10 % y SLA de 600 ms) |
| [`.github/workflows/performance-gate.yml`](.github/workflows/performance-gate.yml) | Evalúa A y B; solo despliega (simulado) la que pasa |
| [`docker-compose.yml`](docker-compose.yml) + [`local/`](local) | Demo local: APIs simuladas, k6, gate y Grafana con un solo comando |
| [`grafana/`](grafana) | Dashboard importable y su generador |

## Resultado

| Versión | Gate | Despliegue | Por qué |
|---|---|---|---|
| [**version-a**](https://github.com/LeoR22/perf-gate-demo/actions/runs/42702445734/job/129450405621) | ❌ NO PASA | Bloqueado | `POST /pagos` p95 767 ms vs 353 ms en producción (2,2x) y 3,33 % de errores |
| [**version-b**](https://github.com/LeoR22/perf-gate-demo/actions/runs/42702445734/job/129450406297) | ✅ PASA (con advertencias) | Ejecutado | Igual a producción en estado estable; tarda 50 s en estabilizarse (prod: 20 s) |

**La versión B reemplaza a producción.** El análisis completo y la justificación están en el
[README de la herramienta](https://github.com/LeoR22/perf-quality-gate#cuál-versión-reemplaza-a-producción).

Las ejecuciones están en la pestaña [Actions](https://github.com/LeoR22/perf-gate-demo/actions). En cada
job, el **Summary** muestra el reporte visual endpoint por endpoint frente a producción y qué falló.

## Reporte visual

El job **Publicar reporte** corre siempre, pase o no pase el gate (el equipo necesita ver justamente qué
falló), y publica en GitHub Pages:

| Página | Qué muestra |
|---|---|
| [Portada](https://leor22.github.io/perf-gate-demo/) | Todas las versiones con su veredicto |
| [Versión A](https://leor22.github.io/perf-gate-demo/version-a/report.html) / [Versión B](https://leor22.github.io/perf-gate-demo/version-b/report.html) | Endpoint por endpoint frente a producción, qué falló y qué mejorar |
| [`grafana.json`](https://leor22.github.io/perf-gate-demo/grafana.json) | Filas planas de todas las versiones: la fuente de datos de Grafana |

### Grafana

[`grafana/dashboard.json`](grafana/dashboard.json) es un dashboard listo para importar. Lee `grafana.json`
con el plugin [Infinity](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/), así que el
pipeline no necesita credenciales de Grafana y los datos no vencen (viven en Pages).

1. En Grafana (Cloud gratis o local): **Connections → Add new connection → Infinity → Install** y crear
   la fuente de datos con los valores por defecto.
2. **Dashboards → New → Import**, subir `grafana/dashboard.json` y elegir la fuente Infinity.
3. Elegir la versión en el selector de arriba. Otro equipo solo cambia la variable *Fuente* por la URL de
   su propio `grafana.json`.

## Demo local con Docker (k6 + Grafana)

Todo el ciclo en tu máquina con un solo comando, sin cuentas ni credenciales:

```bash
docker compose up
```

```
APIs simuladas ──► k6 (producción → A → B) ──► perf-gate ──► reportes HTML + Grafana
```

| Servicio | Qué hace |
|---|---|
| `api-produccion`, `api-version-a`, `api-version-b` | [API simulada](local/api/mock_api.py) con los endpoints del kit. A: pagos 2,2x más lento y 3 % de errores. B: igual a producción, pero con 25 s de arranque en frío |
| `k6-*` | [Prueba k6](local/k6/script.js) (10 usuarios, 75 s) contra cada API, una a la vez, con salida `--out json` |
| `gate` | Instala `perf-quality-gate@v1` desde GitHub y evalúa A y B contra producción ([límites locales](local/perf-gate.local.yml)) |
| `reports` | http://localhost:8000: reportes HTML y `grafana.json` |
| `grafana` | **http://localhost:3000**: sin login, con Infinity y el dashboard ya cargados |

Tarda unos 5 minutos. Cuando el contenedor `gate` imprime `RESULTADO`, el dashboard ya muestra los datos:
A **no pasa** (pagos 2,1x más lento, errores significativos al 99 % y throughput −23 %) y B **pasa con
advertencias** (se estabiliza en 20 s, producción en 0 s).

- Más corto o más largo: `DURATION=40s docker compose up` (variables `DURATION` y `VUS`).
- Otra versión de la herramienta: `PERF_GATE_REF=v1.3.0`.
- Volver a evaluar sin repetir k6: `docker compose run --rm --no-deps gate`.
- Apagar: `docker compose down`.

Validar contra Grafana y k6 reales dejó mejoras en la herramienta: el lector de k6 2.x (que copia `name`
en `url`), la prueba de significancia para errores (antes 3 errores sueltos en 415 peticiones hacían
fallar a B) y, en el dashboard, el parser `backend` de Infinity v4.

## Cómo probarlo en GitHub

- **Actions → Performance Gate → Run workflow**, y elegir `todas`, `version-a` o `version-b`.
- O cambiar un límite en `perf-gate.yml` y hacer push. Por ejemplo, con `max_increase_pct: 150` en
  `POST /pagos` y sin `max_ms`, la versión A seguiría fallando por su tasa de error.
