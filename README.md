# Task Lists API · Prueba técnica Crehana

API REST para gestionar listas de tareas y sus tareas, construida con **FastAPI** sobre una
arquitectura por capas (Domain, Application, Infrastructure, Entrypoints).

Incluye:

- **CRUD** de listas y de tareas dentro de cada lista.
- **Cambio de estado** de una tarea (`PENDING`, `IN_PROGRESS`, `COMPLETED`).
- **Listado de tareas** con filtros por estado o prioridad, paginación y el **porcentaje de
  completitud** de la lista.
- **Autenticación JWT**: cada usuario solo ve sus propias listas.
- **Asignación** de un responsable a cada tarea, por email.
- **Notificación simulada**: al asignar una tarea se "envía" un email, que queda en el log.

Las razones detrás de cada decisión técnica están en [`DECISION_LOG.md`](DECISION_LOG.md).

---

## Stack

| Área | Herramienta |
|---|---|
| Lenguaje | Python 3.14 |
| API | FastAPI, Pydantic v2 |
| Base de datos | PostgreSQL 18, SQLAlchemy 2 (síncrono, psycopg 3), Alembic |
| Seguridad | JWT con PyJWT (HS256), contraseñas con Argon2id |
| Tests | pytest, pytest-cov (cobertura de ramas, mínimo 75%) |
| Calidad | flake8, black, isort, mypy (estricto), pre-commit |
| Entorno | uv, Docker multistage, docker-compose, GitHub Actions |

---

## Arquitectura

Las dependencias apuntan siempre hacia el dominio. El dominio no importa nada fuera de la
biblioteca estándar.

```
entrypoints (FastAPI) ──┐
                        ├──►  application  ──►  domain
infrastructure (SQLA) ──┘     (casos de uso)    (entidades y reglas)
```

```
src/app/
├── domain/                 Entidades (Task, TaskList, User), value objects, reglas y excepciones
├── application/
│   ├── ports.py            Interfaces: repositorios, UnitOfWork, Clock, hasher, tokens, notificador
│   ├── dto.py              Objetos de entrada y salida de los casos de uso
│   └── use_cases/          Un archivo por caso de uso (auth/, task_lists/, tasks/)
├── infrastructure/
│   ├── db/                 Modelos SQLAlchemy, conversores, repositorios, unit of work
│   ├── security/           Argon2 y JWT
│   ├── notifications/      Email simulado (escribe en el log)
│   └── config.py           Configuración por variables de entorno
└── entrypoints/api/
    ├── routers/            Endpoints HTTP
    ├── schemas/            Schemas Pydantic de request y response
    ├── errors.py           Traducción de errores a respuestas HTTP (Problem Details)
    ├── dependencies.py     Composition root: conecta casos de uso con sus implementaciones
    └── main.py             Creación de la aplicación
migrations/                 Migraciones de Alembic
tests/
├── unit/                   Dominio, casos de uso (con implementaciones falsas) y adaptadores sin I/O
└── integration/            Repositorios y API contra PostgreSQL real
```

---

## Ejecutar con Docker

Requisito: Docker con Compose v2.

```bash
docker compose up --build
```

Esto levanta tres servicios, en orden:

1. `db`: PostgreSQL, con *healthcheck*.
2. `migrate`: aplica las migraciones (`alembic upgrade head`) y termina.
3. `api`: arranca solo si las migraciones terminaron bien.

| URL | Contenido |
|---|---|
| http://localhost:8000/docs | Swagger UI. Usa el botón **Authorize** con tu email y contraseña |
| http://localhost:8000/redoc | Documentación alternativa |
| http://localhost:8000/health | Estado de la API |

Para ver los emails simulados:

```bash
docker compose logs -f api
```

Para detener todo y borrar los datos:

```bash
docker compose down -v
```

Si los puertos 5432 u 8000 están ocupados en tu máquina, cámbialos con variables de entorno:
`POSTGRES_PORT=5434 API_PORT=8080 docker compose up --build`.

---

## Entorno local (sin Docker para la API)

Requisito: [uv](https://docs.astral.sh/uv/). Si no tienes Python 3.14, uv lo descarga.

```bash
# 1. Dependencias y hooks de git
uv sync
uv run pre-commit install

# 2. Variables de entorno
cp .env.example .env

# 3. Base de datos (solo el contenedor de PostgreSQL) y migraciones
docker compose up -d db
uv run alembic upgrade head

# 4. API con recarga automática
uv run uvicorn app.entrypoints.api.main:app --reload
```

---

## Pruebas

Hay 251 tests: unitarios (dominio, casos de uso, adaptadores) y de integración (repositorios y
API contra PostgreSQL real). La cobertura de ramas es del 99,6%; el mínimo configurado en
`pytest.ini` es 75%.

**Con Docker** (no requiere Python instalado):

```bash
docker compose run --rm --build tests
```

Levanta una base de datos de pruebas en memoria (`db-test`) y ejecuta toda la suite con el
reporte de cobertura.

**En local:**

```bash
docker compose --profile test up -d --wait db-test   # PostgreSQL de pruebas en el puerto 5433
uv run pytest                                        # suite completa con cobertura
uv run pytest -m unit --no-cov                       # solo tests unitarios, sin base de datos
```

---

## Calidad de código

```bash
uv run black --check .     # formato
uv run isort --check-only .  # orden de imports
uv run flake8 .            # linter (configurado en .flake8)
uv run mypy                # tipos en modo estricto
```

`make lint` ejecuta los cuatro; `make format` aplica black e isort. `make help` lista todos los
atajos. GitHub Actions ejecuta los mismos chequeos y la suite de tests en cada push.

---

## Cómo verificar cada requisito del enunciado

Con la API levantada (`docker compose up --build`), el script `scripts/demo.sh` recorre todos los
casos de uso con `curl` y muestra cada respuesta:

```bash
./scripts/demo.sh
```

| Requisito | Dónde verlo |
|---|---|
| CRUD de listas | Pasos 3 y 11 del script; `tests/integration/api/test_task_lists_api.py` |
| CRUD de tareas dentro de una lista | Pasos 4, 5 y 11; `tests/integration/api/test_tasks_api.py` |
| Cambiar el estado de una tarea | Paso 5; `PUT /api/v1/tasks/{id}/status` |
| Filtros por estado o prioridad y porcentaje de completitud | Pasos 6 y 7; `GET /api/v1/lists/{id}/tasks?status=PENDING` |
| Login y JWT (bonus) | Pasos 1 y 2; botón **Authorize** en `/docs` |
| Asignación de tareas (bonus) | Pasos 8 y 9; `PUT /api/v1/tasks/{id}/assignee` |
| Notificación simulada (bonus) | `docker compose logs api \| grep -A6 "Simulated email"` |
| Errores personalizados y validaciones | Paso 10; `tests/integration/api/test_permissions_api.py` |
| Tests unitarios e integración, cobertura ≥ 75% | `docker compose run --rm --build tests` |
| flake8, black, isort | `make lint` |
| Dockerfile multistage y docker-compose | `Dockerfile` (etapas `builder`, `runtime`, `test`) y `docker-compose.yml` |
| Decisiones técnicas | [`DECISION_LOG.md`](DECISION_LOG.md) |

---

## Endpoints

Todos, excepto `/health` y los de autenticación, requieren `Authorization: Bearer <token>`.

| Método | Ruta | Descripción | Quién puede |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Registrarse | Público |
| POST | `/api/v1/auth/login` | Obtener un token (formulario con `username` = email y `password`) | Público |
| POST | `/api/v1/lists` | Crear una lista | Usuario autenticado |
| GET | `/api/v1/lists` | Mis listas, paginadas | Dueño |
| GET · PATCH · DELETE | `/api/v1/lists/{list_id}` | Obtener, renombrar o eliminar una lista (y sus tareas) | Dueño |
| POST | `/api/v1/lists/{list_id}/tasks` | Crear una tarea | Dueño |
| GET | `/api/v1/lists/{list_id}/tasks` | Tareas con filtros `status` y `priority`, paginación y completitud | Dueño |
| GET | `/api/v1/tasks/{task_id}` | Obtener una tarea | Dueño o asignado |
| PATCH · DELETE | `/api/v1/tasks/{task_id}` | Editar (título, descripción, prioridad) o eliminar | Dueño |
| PUT | `/api/v1/tasks/{task_id}/status` | Cambiar el estado | Dueño o asignado |
| PUT · DELETE | `/api/v1/tasks/{task_id}/assignee` | Asignar por email o desasignar | Dueño |
| GET | `/api/v1/users/me/tasks` | Tareas asignadas al usuario actual | Asignado |

Paginación: `limit` (1 a 100, por defecto 10) y `offset`. Las tareas se ordenan por prioridad
y, a igual prioridad, de la más reciente a la más antigua.

Respuesta del listado de tareas:

```json
{
  "items": [],
  "pagination": { "limit": 10, "offset": 0, "total": 2 },
  "completion": { "total_tasks": 3, "completed_tasks": 1, "percentage": 33.33 }
}
```

`pagination.total` cuenta las tareas que cumplen el filtro; `completion` siempre considera
todas las tareas de la lista.

Todos los errores siguen el formato *Problem Details* (RFC 9457):

```json
{
  "title": "Forbidden",
  "status": 403,
  "detail": "Only the owner of the list can modify task '...'.",
  "code": "NOT_TASK_OWNER"
}
```

---

## Pendientes

Lo que quedó fuera del alcance (refresh tokens, envío real de emails en segundo plano,
historial de asignaciones, filtros con varios valores, entre otros) está listado al final de
[`DECISION_LOG.md`](DECISION_LOG.md#pendientes-y-extensiones-futuras), junto con la decisión
que lo originó.
