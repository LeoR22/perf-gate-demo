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

## Cómo probarlo

- **Actions → Performance Gate → Run workflow**, y elegir `todas`, `version-a` o `version-b`.
- O cambiar un límite en `perf-gate.yml` y hacer push. Por ejemplo, con `max_increase_pct: 150` en
  `POST /pagos` y sin `max_ms`, la versión A seguiría fallando por su tasa de error.
