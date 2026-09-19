# nuwek-kpi-challenge

Este proyecto es mi solución al reto técnico de Grupo Nuwek. Lee el archivo `ventas.csv`, lo limpia, lo guarda en una base de datos y deja una API donde se pueden consultar los KPIs de ventas cerradas.

Está dividido en dos partes que solo se comunican a través de la base de datos:

1. **La importación**, que se corre una sola vez: lee el CSV, lo limpia y lo guarda.
2. **La API**, que consulta esa base de datos y responde `GET /api/ventas/resumen`.

## Contenido

1. [Tecnologías utilizadas](#1-tecnologías-utilizadas)
2. [Cómo instalar el proyecto](#2-cómo-instalar-el-proyecto)
3. [Cómo configurar la base de datos](#3-cómo-configurar-la-base-de-datos)
4. [Cómo importar y procesar ventas.csv](#4-cómo-importar-y-procesar-ventascsv)
5. [Cómo ejecutar la aplicación](#5-cómo-ejecutar-la-aplicación)
6. [Cómo probar el endpoint](#6-cómo-probar-el-endpoint)
7. [Problemas encontrados en los datos y decisiones tomadas](#7-problemas-encontrados-en-los-datos-y-decisiones-tomadas)
8. [Cómo manejaría una API Key](#8-cómo-manejaría-una-api-key)
9. [Cómo integraría la solución con un SaaS](#9-cómo-integraría-la-solución-con-un-saas)
10. [Herramientas de IA utilizadas](#10-herramientas-de-ia-utilizadas)

---

## 1. Tecnologías utilizadas

- **Python 3.11 o superior.** Es con el que me siento más cómoda para trabajar con datos.
- **FastAPI y Uvicorn** para la API. Con pocas líneas queda el endpoint y además genera solo una página de documentación (`/docs`) donde se puede probar.
- **SQLite** como base de datos. No hay que instalar nada, y si algún día se quiere usar PostgreSQL basta con cambiar una variable en el `.env`.
- **SQLAlchemy** para hablar con la base de datos desde Python.
- **`csv` y `decimal`** de la librería estándar para leer y limpiar el archivo. Son solo 218 filas, así que no vi necesario usar pandas. Usé `Decimal` para los montos porque con dinero prefiero evitar los errores de redondeo de los decimales normales.
- **python-dotenv** para leer la configuración del archivo `.env`.
- **pytest** para las pruebas.

## 2. Cómo instalar el proyecto

Necesitas tener instalados Python 3.11 o superior y Git.

Primero clona el repositorio y entra a la carpeta:

```bash
git clone https://github.com/jesscortes3005/nuwek-kpi-challenge.git
cd nuwek-kpi-challenge
```

Luego crea un entorno virtual, actívalo e instala las librerías.

En Linux o macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

En Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Si PowerShell no te deja activar el entorno, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a intentarlo. Cuando el entorno está activo, aparece `(.venv)` al inicio de la línea de la terminal.

## 3. Cómo configurar la base de datos

No hay que configurar nada. Uso SQLite, así que el archivo `ventas.db` y la tabla `ventas` se crean solos cuando se importan los datos (paso 4). La ruta de la base de datos está en el archivo `.env`:

```
DATABASE_URL=sqlite:///./ventas.db
```

La tabla `ventas` tiene estas columnas:

- `id_venta`: es la clave primaria, por eso no puede haber dos ventas con el mismo id.
- `fecha`: en formato `YYYY-MM-DD`.
- `vendedor`: puede quedar vacío.
- `region`: obligatoria.
- `producto`: puede quedar vacío.
- `monto`: número que no puede ser negativo.
- `estatus`: solo `cerrada`, `abierta` o `cancelada`.

También agregué un índice sobre `estatus` y `fecha`, porque son los campos que usa la consulta principal. En `sql/schema.sql` está el mismo esquema escrito en SQL, solo como referencia (no hace falta ejecutarlo).

## 4. Cómo importar y procesar ventas.csv

```bash
python -m scripts.import_ventas
```

El script hace esto, en este orden:

1. Lee `data/ventas.csv` como UTF-8.
2. Normaliza cada campo (fechas, montos, región y estatus).
3. Descarta las filas inválidas.
4. Elimina los duplicados.
5. Guarda lo que queda en la base de datos.

Al terminar imprime un reporte. Con el archivo del reto debe salir así:

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

Se puede correr varias veces sin problema: antes de guardar vacía la tabla, así que siempre quedan 185 filas.

## 5. Cómo ejecutar la aplicación

```bash
uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000` y la documentación con la que se puede probar en `http://127.0.0.1:8000/docs`. Para detener el servidor, `Ctrl+C`.

Importante: hay que haber hecho antes la importación del paso 4. Si no, la base de datos estará vacía.

## 6. Cómo probar el endpoint

El endpoint es `GET /api/ventas/resumen`. Acepta dos parámetros opcionales, `fecha_inicio` y `fecha_fin`, en formato `YYYY-MM-DD`. Los dos extremos están incluidos, y si no se manda ninguno se calcula todo el histórico. Solo se cuentan las ventas con estatus cerrada.

```bash
# Todo el histórico
curl "http://127.0.0.1:8000/api/ventas/resumen"

# Con un periodo
curl "http://127.0.0.1:8000/api/ventas/resumen?fecha_inicio=2026-01-01&fecha_fin=2026-03-31"

# Con una fecha inválida (responde error 400)
curl -i "http://127.0.0.1:8000/api/ventas/resumen?fecha_inicio=hola"
```

En Windows PowerShell, `curl` es un alias de otro comando y puede fallar. Ahí conviene usar `curl.exe`, o simplemente abrir la URL en el navegador.

Con todo el histórico, la respuesta es esta:

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

Otros casos:

- **Un periodo sin ventas:** responde 200 con `{"total_ventas": 0, "numero_ventas": 0, "por_region": []}`.
- **Una fecha inválida** (`hola`, `2026-02-30`) o una `fecha_inicio` posterior a `fecha_fin`: responde 400 con un mensaje que explica el problema.
- **Un error interno:** responde 500 con un mensaje genérico. Los detalles solo se guardan en el log del servidor, para no mostrar contraseñas ni datos de conexión.

Para correr las pruebas automáticas (son 19):

```bash
pytest -v
```

## 7. Problemas encontrados en los datos y decisiones tomadas

Lo primero fue revisar el CSV antes de escribir código. Tiene 218 filas y 200 ids distintos, con bastantes errores puestos a propósito. Apliqué las reglas del reto tal cual, y en este orden: primero normalizar, luego descartar lo inválido y al final quitar duplicados.

- **Fechas en cuatro formatos** (`2026-03-04`, `2026-03-04 00:00:00`, `04-03-2026` y `04/03/2026`). Los dos primeros son año-mes-día y los otros dos día-mes-año, así que `04-03-2026` es el 4 de marzo. Reconozco cada formato y valido con `strptime` que el día exista.
- **Seis fechas inválidas**, como `2026-13-45`, `0000-00-00`, `ayer`, `31/02/2026` o una vacía. Esas filas se descartan.
- **Montos en seis formatos** (`60,901.75`, `$82,482.90`, `72 760.95`, `54608,19`, entre otros). Quito el `$` y los espacios. Si tiene coma y punto, la coma es de miles; si solo tiene coma, es el decimal.
- **Cinco montos inválidos** (`abc`, `N/A`, vacíos y uno negativo, `-3500.00`). Esas filas se descartan.
- **La región estaba escrita de 21 formas distintas** (` Bajío `, `BAJÍO`, `norte`...). Con `strip()` y `capitalize()` quedan las 5 regiones reales: Norte, Sur, Centro, Occidente y Bajío. Cuatro filas no tenían región y se descartaron.
- **El estatus tenía 15 variantes** (`Cerrado`, `  cerrada  `, `CANCELADA`...). Lo paso a minúsculas, quito espacios y trato `cerrado` y `cerrada` como lo mismo (igual con abierta y cancelada).
- **18 duplicados.** Eran el mismo `id_venta` escrito con otro formato (por ejemplo, `V0089` con `2026-06-10` y con `10-06-2026`). Una vez normalizados son idénticos, así que dejo la primera aparición. Comprobé que ninguna pareja se contradecía.
- **Tres filas sin vendedor.** Las conservo y guardo el vendedor como vacío, porque no afecta los KPIs.
- **Acentos.** Se leen bien como UTF-8, no hubo problemas de codificación.

Al final quedaron **185 filas**: 106 cerradas, 45 abiertas y 34 canceladas.

Algunas decisiones que tomé por mi cuenta:

- Dejé que `producto` pueda quedar vacío, porque el reto no dice qué hacer en ese caso (en este archivo nunca viene vacío).
- Si una fila llegara sin `id_venta` o con un estatus desconocido, también se descartaría. Aquí no pasa, pero protege a la base de datos.
- Las fechas del endpoint las valido yo, porque FastAPI responde con error 422 por defecto y el reto pide 400.

## 8. Cómo manejaría una API Key

La guardaría en una variable de entorno. En mi computadora, en el archivo `.env`, que está en el `.gitignore` para que nunca se suba a GitHub. En un servidor real, usaría el sistema de secretos del servicio donde se despliegue. El código la leería con `os.getenv("API_KEY")`.

No la pondría dentro del código, ni en el repositorio (tampoco en commits viejos), ni en el README, ni en los logs o mensajes de error. En `.env.example` solo dejaría un valor de ejemplo falso, para que se sepa que la variable existe.

Si alguna vez se llegara a subir por error, no basta con borrar el commit: hay que revocar la clave y generar una nueva.

## 9. Cómo integraría la solución con un SaaS

1. No escribiría nada directamente en la base de datos del SaaS, porque podría afectar lo que ya está funcionando.
2. Usaría su API oficial, o una réplica de solo lectura si existe.
3. Pediría una credencial exclusiva para esta integración, con permisos solo de lectura.
4. Esa credencial iría en variables de entorno, nunca en el código.
5. Toda la comunicación sería por HTTPS.
6. Un proceso programado leería los datos del SaaS y los copiaría a la base de datos de esta API.
7. Pondría reintentos, límites de peticiones y registros, para no saturar al SaaS.
8. Lo probaría primero en un ambiente de pruebas. Así, si mi API falla, el SaaS sigue funcionando igual.

## 10. Herramientas de IA utilizadas

Usé **Claude** como asistente. Me ayudó a analizar el enunciado y el CSV, a proponer la arquitectura y a generar el código, las pruebas y el borrador de este README.

Yo revisé y aprobé el plan antes de implementarlo, instalé y ejecuté el proyecto, corrí las pruebas, comprobé la API contra los resultados esperados (106 ventas cerradas, el filtro por fechas, un periodo sin ventas y los errores 400) y armé el repositorio y el Pull Request.

---

## Dificultades y aprendizajes

- **Trabajar con la terminal en Windows me costó al principio.** Tuve problemas para activar el entorno virtual en PowerShell: primero por escribir mal la ruta y luego porque estaba parada en una carpeta distinta a la del proyecto. Además, tenía el proyecto dentro de otra carpeta con el mismo nombre, y eso me confundió un rato.
- **Vi que una rama creada en mi computadora no aparece en GitHub hasta hacer `git push`.** Antes pensé que algo estaba mal.
- **Aprendí que revisar los datos antes de programar ahorra mucho tiempo.** Saber qué errores había en el CSV me dejó claras las reglas de limpieza antes de escribir código

## Estructura del proyecto

```text
nuwek-kpi-challenge/
├── app/
│   ├── main.py                  # crea la API y maneja el error 500
│   ├── config.py                # lee el .env
│   ├── database.py              # conexión a la base de datos
│   ├── models.py                # la tabla ventas
│   ├── validators.py            # valida fecha_inicio y fecha_fin
│   ├── api/ventas.py            # el endpoint /api/ventas/resumen
│   ├── services/kpi_service.py  # las consultas de los KPIs
│   └── etl/
│       ├── cleaning.py          # reglas de limpieza
│       └── importer.py          # lee, limpia, quita duplicados y guarda
├── scripts/import_ventas.py     # comando para importar el CSV
├── sql/schema.sql               # esquema en SQL (referencia)
├── data/ventas.csv
├── tests/                       # las 19 pruebas
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Lo que no incluí

No hice Docker ni la colección de Postman, porque eran opcionales. Tampoco puse autenticación, porque el reto no la pide. La documentación con Swagger sí está disponible en `/docs`.
