# nuwek-kpi-challenge

API REST sencilla que limpia `ventas.csv`, lo guarda en una base de datos y expone los KPIs de ventas **cerradas**.

## 1. Tecnologías utilizadas

| Necesidad | Tecnología | Motivo |
|---|---|---|
| Lenguaje | Python 3.11+ | Ideal para limpieza y analisis de  datos |
| API | FastAPI + Uvicorn | Un endpoint  corto y facil de usar  y Swagger viene incluido en `/docs` |
| Base de datos | SQLite | No requiere instalar nada. Cambiar a PostgreSQL es solo cambiar `DATABASE_URL` |
| Acceso a datos | SQLAlchemy 2.0 | Funciona igual con SQLite o PostgreSQL |
| Procesamiento CSV | `csv` + `decimal` (librería estándar) | 218 filas no justifican pandas, y `Decimal` evita errores de float en dinero |
| Configuración | python-dotenv (`.env`) | Secretos fuera del código |
| Pruebas | pytest + httpx | Pruebas de limpieza, validaciones y endpoint |

## 2. Instalación

Requisitos: Python 3.11 o superior y Git.

```bash
git clone https://github.com/jesscortes3005/nuwek-kpi-challenge.git
cd nuwek-kpi-challenge

python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
```

## 3. Configuración de la base de datos

Por defecto usa **SQLite**: no hay que instalar ni configurar nada. El archivo `ventas.db` y la tabla `ventas`
se crean automáticamente al importar los datos (paso 4). La variable `DATABASE_URL` se define en `.env`:

```
DATABASE_URL=sqlite:///./ventas.db
```

El esquema equivalente en SQL está en `sql/schema.sql` (solo como referencia; no es necesario ejecutarlo).
Tabla `ventas`: `id_venta` (PK), `fecha`, `vendedor` (acepta NULL), `region`, `producto`, `monto` (≥ 0), `estatus`
(`cerrada`, `abierta` o `cancelada`), más un índice `(estatus, fecha)`.

## 4. Importar y procesar `ventas.csv`

```bash
python -m scripts.import_ventas
```

Lee `data/ventas.csv` (UTF-8), normaliza, descarta filas inválidas, elimina duplicados, guarda en la BD y muestra un reporte:

```
Registros originales:          218
Descartados por fecha:         6
Descartados por monto:         5
Descartados por región vacía:  4
Descartados (otros):           0
Registros válidos:             203
Duplicados eliminados:         18
Registros insertados:          185
```

El script es **idempotente**: se puede ejecutar varias veces y siempre deja 185 filas (vacía la tabla antes de cargar).

## 5. Ejecutar la aplicación

```bash
uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000` y la documentación interactiva (Swagger) en `http://127.0.0.1:8000/docs`.

## 6. Probar el endpoint

```bash
# Todo el histórico
curl "http://127.0.0.1:8000/api/ventas/resumen"

# Con periodo (rango inclusivo en ambos extremos)
curl "http://127.0.0.1:8000/api/ventas/resumen?fecha_inicio=2026-01-01&fecha_fin=2026-03-31"

# Error 400: parámetro inválido
curl -i "http://127.0.0.1:8000/api/ventas/resumen?fecha_inicio=hola"
```

Respuesta del histórico completo (solo ventas cerradas):

```json
{
  "total_ventas": 4757842.1,
  "numero_ventas": 106,
  "por_region": [
    {"region": "Centro", "total": 1036102.99},
    {"region": "Sur", "total": 1024346.66},
    {"region": "Norte", "total": 916965.85},
    {"region": "Occidente", "total": 914494.32},
    {"region": "Bajío", "total": 865932.28}
  ]
}
```

| Situación | Respuesta |
|---|---|
| Periodo sin ventas | `200` → `{"total_ventas": 0, "numero_ventas": 0, "por_region": []}` |
| `fecha_inicio=hola`, fecha inexistente (`2026-02-30`) o `fecha_inicio` > `fecha_fin` | `400` → `{"error": "mensaje claro"}` |
| Error interno | `500` → `{"error": "Error interno del servidor."}` (sin detalles; la traza queda solo en el log del servidor) |

**Pruebas automatizadas:**

```bash
pytest -v
```

## 7. Problemas encontrados en los datos y decisiones tomadas

El archivo tiene 218 filas y 200 `id_venta` únicos. Se aplicaron las reglas del reto tal cual, en este orden: normalizar → descartar inválidas → deduplicar.

| Problema | Ejemplo | Solución |
|---|---|---|
| Fechas en 4 formatos | `2026-03-04`, `2026-03-04 00:00:00`, `04-03-2026`, `04/03/2026` | Los dos primeros son año-mes-día (hora ignorada). Los otros dos son día-mes-año. |
| Fechas inválidas (6) | `2026-13-45`, `0000-00-00`, vacía, `ayer`, `31/02/2026`, `2026/02/30` | Se valida con `strptime` (rechaza días inexistentes). La fila se descarta. |
| Montos en 6 formatos | `60,901.75`, `$82,482.90`, `72 760.95`, `54608,19` | Se quitan `$` y espacios. Con coma y punto, la coma es de miles. Con solo coma, es el decimal. |
| Montos inválidos (5) | `abc`, `N/A`, vacíos, `-3500.00` | La fila se descarta. |
| Región con 21 variantes | ` Bajío `, `BAJÍO`, `norte` | `strip()` + `capitalize()` → 5 regiones. |
| Región vacía (4) | | La fila se descarta. |
| Estatus con 15 variantes | `Cerrado`, `  cerrada  `, `CANCELADA` | Minúsculas, sin espacios y se unifica género (`cerrado` = `cerrada`). |
| Duplicados (18) | `V0089` con `2026-06-10` y `10-06-2026` | Tras normalizar son idénticos; se conserva la primera aparición. Ninguna pareja era contradictoria. |
| Vendedor vacío (3) | | Se conserva y se guarda como `NULL`. |
| Codificación | Acentos (Bajío, Efraín) | Se lee como UTF-8 y no hubo problemas de mojibake. |

Decisiones adicionales:

- `producto` acepta NULL, porque el reto no define una regla de descarte para él (en el archivo nunca está vacío).
- Una fila con `id_venta` vacío o estatus desconocido se descartaría (protege la clave primaria y el CHECK), aunque en este archivo no ocurre.
- Los parámetros de fecha llegan como texto y se validan manualmente porque FastAPI responde 422 por defecto y el reto pide 400.
- Los montos se procesan con `Decimal`, y se guardan y devuelven redondeados a 2 decimales.

**Resultado final:** 185 filas guardadas (106 cerradas, 45 abiertas, 34 canceladas).

## 8. Cómo manejaría una API Key

- **Dónde SÍ:** en una variable de entorno. En desarrollo, en el archivo `.env` local (que está en `.gitignore`); en producción, en un gestor de secretos (por ejemplo los secrets del servicio de despliegue o de GitHub Actions). El código la lee con `os.getenv("API_KEY")`.
- **Dónde NO:** en el código fuente, en el repositorio (ni en commits antiguos), en `README`, `.env.example` con valor real, logs, mensajes de error, ni en el frontend o URLs.
- Se sube `.env.example` con un valor falso de ejemplo. Si una clave llegara a filtrarse, se **revoca y se rota** de inmediato, porque borrar el commit no basta.

## 9. Cómo integraría la solución con un SaaS

1. No escribiría nunca en la base de datos del SaaS; solo usaría su API oficial o una réplica de solo lectura.
2. Crearía en el SaaS una credencial dedicada con permisos mínimos (solo lectura).
3. Guardaría esa credencial (API_KEY) en variables de entorno o en un gestor de secretos.
4. Toda la comunicación iría por HTTPS.
5. Un proceso programado (ETL) leería los datos del SaaS y los cargaría en la BD de esta API.
6. Añadiría reintentos, límites de tasa y logs, para no saturar al SaaS.
7. Esta API seguiría siendo de solo lectura y separada del SaaS.
8. Si el SaaS ofrece webhooks, los usaría para actualizar solo lo que cambia.
9. Probaría primero en un entorno de pruebas.
10. Con esto, si mi API falla, el SaaS sigue operando sin cambios.

## 10. Herramientas de IA utilizadas

- Usé Claude como asistente para analizar el enunciado y el CSV, proponer la arquitectura y generar el código, las pruebas y el borrador del README. Yo revisé y aprobé el plan, instalé y ejecuté el proyecto, corrí las pruebas, validé la API contra los resultados esperados y armé el repositorio y el Pull Request.

## Estructura del proyecto

```text
nuwek-kpi-challenge/
├── app/
│   ├── main.py            # FastAPI + manejador de error 500
│   ├── config.py          # lee .env
│   ├── database.py        # engine y sesión
│   ├── models.py          # modelo Venta
│   ├── validators.py      # validación de fecha_inicio / fecha_fin
│   ├── api/ventas.py      # GET /api/ventas/resumen
│   ├── services/kpi_service.py   # consultas de KPIs
│   └── etl/
│       ├── cleaning.py    # reglas de limpieza
│       └── importer.py    # lee, limpia, deduplica, guarda, reporta
├── scripts/import_ventas.py
├── sql/schema.sql
├── data/ventas.csv
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Qué faltó / limitaciones

- No incluí Docker ni colección de Postman. Swagger sí está disponible en `/docs`.
- No hay autenticación, porque el reto no la pide.
