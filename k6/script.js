// Prueba de carga k6 equivalente al plan JMeter del kit (la usa .github/workflows/k6-load-test.yml).
// Manual:  k6 run --out json=resultados.json -e BASE_URL=http://localhost:8080 script.js
//
// Importante para el gate: cada petición lleva el tag `name` con la MISMA etiqueta que usa
// JMeter, así producción (JMeter) y la versión nueva (k6) se pueden comparar endpoint por endpoint.
import http from 'k6/http';
import { sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'http://localhost:8080';

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || '90s',
};

const json = { headers: { 'Content-Type': 'application/json' } };

export default function () {
  http.get(`${BASE}/clientes`, { tags: { name: 'GET /clientes' } });
  http.get(`${BASE}/cuentas/ahorros/saldo`, { tags: { name: 'Consultar saldo, cuenta ahorros' } });
  http.post(`${BASE}/pagos`, JSON.stringify({ valor: 1000 }),
    { ...json, tags: { name: 'POST /pagos' } });
  http.post(`${BASE}/transferencias`, JSON.stringify({ valor: 500 }),
    { ...json, tags: { name: 'POST /transferencias' } });
  sleep(0.1);
}
