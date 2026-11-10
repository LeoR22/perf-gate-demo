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
| [`k6/`](k6) | Script de k6, API simulada y límites que usa la prueba de carga real |

## Resultado

| Versión | Gate | Despliegue | Por qué |
|---|---|---|---|
| [**version-a**](https://github.com/LeoR22/perf-gate-demo/actions/runs/42729780645/job/129544585059) | ❌ NO PASA | Bloqueado | `POST /pagos` p95 767 ms vs 353 ms en producción (2,2x) y 3,33 % de errores |
| [**version-b**](https://github.com/LeoR22/perf-gate-demo/actions/runs/42729780645/job/129544585407) | ✅ PASA (con advertencias) | Ejecutado | Igual a producción en estado estable; tarda 50 s en estabilizarse (prod: 20 s) |

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

## Prueba de carga real con k6 (en GitHub Actions)

El workflow [`k6-load-test.yml`](.github/workflows/k6-load-test.yml) corre **solo en cada push**, dentro del
runner de GitHub, sin nada que instalar en tu computador:

```
API simulada de producción (:8080) ─┐
                                    ├─► k6 genera carga real ─► perf-gate decide ─► A en rojo, B en verde
API simulada de la versión (:8081) ─┘
```

| Paso del job | Qué hace |
|---|---|
| Levantar APIs | Inicia la [API simulada](k6/mock_api.py) de producción y la de la versión. A: pagos 2,2x más lento y 3 % de errores. B: igual a producción, pero con 25 s de arranque en frío |
| k6 contra producción y contra la versión | Corre el [script de k6](k6/script.js) (10 usuarios, 75 s) con salida `--out json` |
| Performance Quality Gate | Evalúa la versión contra producción con `LeoR22/perf-quality-gate@v1` y los [límites para k6](k6/perf-gate.k6.yml) |

Para lanzarlo a mano con otra duración: **Actions → Prueba de carga real (k6) → Run workflow** y elegir la duración.

> **Cifras ilustrativas.** Las APIs son **simuladas** (imitan el comportamiento de A y B; no son las
> versiones reales del reto) y k6 genera datos nuevos en cada corrida, así que los números varían. El
> **veredicto oficial** sale de los resultados JMeter del kit (workflow *Performance Gate*).

Validar con k6 real dejó dos mejoras en la herramienta: el lector de k6 2.x (que copia `name` en `url`) y
la prueba de significancia para errores (antes 3 errores sueltos en 415 peticiones hacían fallar a B).

## Cómo probarlo en GitHub

- **Actions → Performance Gate → Run workflow**, y elegir `todas`, `version-a` o `version-b`.
- O cambiar un límite en `perf-gate.yml` y hacer push. Por ejemplo, con `max_increase_pct: 150` en
  `POST /pagos` y sin `max_ms`, la versión A seguiría fallando por su tasa de error.
