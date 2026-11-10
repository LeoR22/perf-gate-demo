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
| [`.github/workflows/k6-load-test.yml`](.github/workflows/k6-load-test.yml) | **Prueba de carga real con k6** en el runner: levanta las APIs simuladas, k6 genera el tráfico y el gate decide |
| [`docker-compose.yml`](docker-compose.yml) + [`local/`](local) | Demo local: APIs simuladas, k6, gate y reporte HTML con un solo comando |

## Resultado

| Versión | Gate | Despliegue | Por qué |
|---|---|---|---|
| [**version-a**](https://github.com/LeoR22/perf-gate-demo/actions/runs/42726306808/job/129532693543) | ❌ NO PASA | Bloqueado | `POST /pagos` p95 767 ms vs 353 ms en producción (2,2x) y 3,33 % de errores |
| [**version-b**](https://github.com/LeoR22/perf-gate-demo/actions/runs/42726306808/job/129532693245) | ✅ PASA (con advertencias) | Ejecutado | Igual a producción en estado estable; tarda 50 s en estabilizarse (prod: 20 s) |

**La versión B reemplaza a producción.** El análisis completo y la justificación están en el
[README de la herramienta](https://github.com/LeoR22/perf-quality-gate#cuál-versión-reemplaza-a-producción).

Las ejecuciones están en la pestaña [Actions](https://github.com/LeoR22/perf-gate-demo/actions). En cada
job, el **Summary** muestra el reporte visual endpoint por endpoint frente a producción y qué falló.

## Defecto automático

Cuando una versión no pasa, el gate abre el issue
[`[perf-gate] version-a no pasa`](https://github.com/LeoR22/perf-gate-demo/issues?q=label%3Aperf-gate)
con el reporte y el link a la ejecución. En las ejecuciones siguientes lo comenta, y lo cierra solo
cuando la versión pase. En los PR solo se reporta, no se abren issues.

## Reporte visual

El job **Publicar reporte** corre siempre, pase o no pase el gate (el equipo necesita ver justamente qué
falló), y publica en GitHub Pages:

| Página | Qué muestra |
|---|---|
| [Portada](https://leor22.github.io/perf-gate-demo/) | Todas las versiones con su veredicto |
| [Versión A](https://leor22.github.io/perf-gate-demo/version-a/report.html) / [Versión B](https://leor22.github.io/perf-gate-demo/version-b/report.html) | Endpoint por endpoint frente a producción, qué falló y qué mejorar |

## Demo local con Docker (k6)

Todo el ciclo en tu máquina con un solo comando, sin cuentas ni credenciales:

```bash
docker compose up
```

```
APIs simuladas ──► k6 (producción → A → B) ──► perf-gate ──► reporte HTML
```

| Servicio | Qué hace |
|---|---|
| `api-produccion`, `api-version-a`, `api-version-b` | [API simulada](local/api/mock_api.py) con los endpoints del kit. A: pagos 2,2x más lento y 3 % de errores. B: igual a producción, pero con 25 s de arranque en frío |
| `k6-*` | [Prueba k6](local/k6/script.js) (10 usuarios, 75 s) contra cada API, una a la vez, con salida `--out json` |
| `gate` | Instala `perf-quality-gate@v1` desde GitHub y evalúa A y B contra producción ([límites locales](local/perf-gate.local.yml)) |
| `reports` | **http://localhost:8000**: portada y reporte HTML de cada versión |

Tarda unos 5 minutos. Cuando el contenedor `gate` imprime `RESULTADO`, los reportes ya están en http://localhost:8000:
A **no pasa** y B **pasa con advertencias**.

> **Cifras ilustrativas.** Las APIs son **simuladas** (imitan el comportamiento de A y B; no son las
> versiones reales del reto) y k6 genera datos nuevos en cada corrida, así que los números varían. En una
> ejecución de ejemplo: pagos 2,1x más lento en A, con errores significativos y throughput −23 %; B se
> estabiliza en 20 s, producción en 0 s. El **veredicto oficial** sale de los resultados JMeter del kit
> (workflow *Performance Gate*).

- Más corto o más largo: `DURATION=40s docker compose up` (variables `DURATION` y `VUS`).
- Otra versión de la herramienta: `PERF_GATE_REF=v1.3.0`.
- Volver a evaluar sin repetir k6: `docker compose run --rm --no-deps gate`.
- Apagar: `docker compose down`.

Validar con k6 real dejó dos mejoras en la herramienta: el lector de k6 2.x (que copia `name` en `url`) y
la prueba de significancia para errores (antes 3 errores sueltos en 415 peticiones hacían fallar a B).

## Cómo probarlo en GitHub

- **Actions → Performance Gate → Run workflow**, y elegir `todas`, `version-a` o `version-b`.
- O cambiar un límite en `perf-gate.yml` y hacer push. Por ejemplo, con `max_increase_pct: 150` en
  `POST /pagos` y sin `max_ms`, la versión A seguiría fallando por su tasa de error.
