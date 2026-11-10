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
| [`resultados/`](resultados) | `produccion-actual.csv` es la línea base; **cada otro archivo es una versión a evaluar** (hoy: A y B del kit, 5 min, 50 usuarios) |
| [`perf-gate.yml`](perf-gate.yml) | Límites de **este** equipo (p. ej. pagos más estricto: +10 % y SLA de 600 ms) |
| [`.github/workflows/performance-gate.yml`](.github/workflows/performance-gate.yml) | Descubre los archivos de `resultados/`, evalúa cada uno contra producción y solo despliega (simulado) los que pasan |

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

## Evaluar una versión nueva

No hay que tocar el workflow: **cada archivo de `resultados/` (salvo `produccion-actual.csv`) se evalúa
automáticamente** contra producción, con su propio job, reporte e issue.

**Desde el navegador:**
1. Entra a la carpeta [`resultados/`](resultados) → **Add file → Upload files**.
2. Sube el archivo de resultados, por ejemplo `version-c.csv` (CSV de JMeter, o `.json`/`.csv` de k6).
3. **Commit changes**.
4. En **Actions** aparece la ejecución sola, con un job `version-c` además de `version-a` y `version-b`.

**Desde tu computador:**
```bash
cp mi-prueba.csv resultados/version-c.csv
git add resultados/version-c.csv
git commit -m "test: evaluar version-c"
git push
```

**Requisitos del archivo:** columnas `timeStamp`, `elapsed`, `label` y `success` (`true`/`false`). Los nombres
de los endpoints (`label`) deben coincidir con los de producción para poder compararse. Si el archivo trae un
dato inválido, el job se detiene e indica la línea y la columna.

**Evaluar solo una:** **Actions → Performance Gate → Run workflow** y escribir el nombre sin extensión
(por ejemplo `version-c`). Si lo dejas vacío, evalúa todas.

Para dejar de evaluar una versión, borra su archivo de `resultados/`.

## Cómo probarlo en GitHub

- **Actions → Performance Gate → Run workflow** (todas las versiones, o una por nombre).
- O cambiar un límite en `perf-gate.yml` y hacer push. Por ejemplo, con `max_increase_pct: 150` en
  `POST /pagos` y sin `max_ms`, la versión A seguiría fallando por su tasa de error.
